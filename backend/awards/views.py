from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q, Exists, OuterRef
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage
from candidates.models import Candidate
from results.models import ModularResult, FormalResult
from configurations.models import ReprintReason
from awards.models import TranscriptCollection
from awards.serializers import TranscriptCollectionListSerializer, TranscriptCollectionDetailSerializer
from occupations.models import OccupationModule, OccupationPaper
from io import BytesIO
from PyPDF2 import PdfMerger
from django.conf import settings


def formal_candidate_qualifies(candidate):
    """
    Check if a formal candidate qualifies for transcript/awards.
    
    For module-based levels: Check if both Theory AND Practical results exist and passed
    (formal candidates don't take individual modules, just Theory+Practical papers)
    
    For paper-based levels: Check if earned CUs >= required CUs
    
    Returns (qualifies: bool, message: str) tuple.
    """
    formal_results = list(candidate.formal_results.all())
    if not formal_results:
        return False, "No results found"
    
    # Get the level from first result
    first_result = formal_results[0]
    if not first_result.level:
        return False, "No level found"
    
    level = first_result.level
    
    if level.structure_type == 'modules':
        # For module-based levels, formal candidates just need Theory + Practical passed
        has_theory_passed = False
        has_practical_passed = False
        
        for r in formal_results:
            if r.comment == 'Successful':
                if r.type == 'theory':
                    has_theory_passed = True
                elif r.type == 'practical':
                    has_practical_passed = True
        
        if has_theory_passed and has_practical_passed:
            return True, "Qualified"
        else:
            missing = []
            if not has_theory_passed:
                missing.append("Theory")
            if not has_practical_passed:
                missing.append("Practical")
            return False, f"Missing successful results for: {', '.join(missing)}"
    else:
        # For paper-based levels, check credit units
        earned_cus = 0
        for r in formal_results:
            if r.comment == 'Successful' and r.paper and r.paper.credit_units:
                earned_cus += r.paper.credit_units
        
        required_cus = 0
        level_papers = OccupationPaper.objects.filter(level=level, is_active=True)
        for paper in level_papers:
            if paper.credit_units:
                required_cus += paper.credit_units
        
        if earned_cus >= required_cus:
            return True, "Qualified"
        else:
            return False, f"Earned credit units ({earned_cus}) are less than required ({required_cus})"


class AwardsViewSet(viewsets.ViewSet):
    """
    ViewSet to list candidates who qualify for awards.
    A candidate qualifies if:
    - They are enrolled
    - They have results
    - ALL their results are passing (based on mark thresholds)
    """
    permission_classes = [IsAuthenticated]

    def _get_base_queryset(self):
        """Build the base queryset of qualifying candidates."""
        from django.db.models import Prefetch
        
        modular_candidates = Candidate.objects.filter(
            registration_category='modular'
        ).filter(
            Exists(ModularResult.objects.filter(candidate=OuterRef('pk')))
        ).exclude(
            Exists(ModularResult.objects.filter(
                candidate=OuterRef('pk')
            ).filter(
                Q(mark__isnull=True) |
                Q(mark=-1) |
                Q(type='practical', mark__lt=65) |
                Q(type='theory', mark__lt=50)
            ))
        )

        formal_candidates = Candidate.objects.filter(
            registration_category='formal'
        ).filter(
            Exists(FormalResult.objects.filter(candidate=OuterRef('pk')))
        ).exclude(
            Exists(FormalResult.objects.filter(
                candidate=OuterRef('pk')
            ).filter(
                Q(mark__isnull=True) |
                Q(mark=-1) |
                Q(type='practical', mark__lt=65) |
                Q(type='theory', mark__lt=50)
            ))
        )

        return (modular_candidates | formal_candidates).select_related(
            'occupation', 'assessment_center'
        ).prefetch_related(
            Prefetch('modular_results', queryset=ModularResult.objects.select_related('assessment_series')),
            Prefetch('formal_results', queryset=FormalResult.objects.select_related('level', 'assessment_series', 'paper')),
        )

    def _apply_filters(self, qs, request):
        """Apply search and filter query params to the queryset."""
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(full_name__icontains=search) |
                Q(registration_number__icontains=search) |
                Q(assessment_center__center_name__icontains=search) |
                Q(occupation__occ_name__icontains=search) |
                Q(transcript_serial_number__icontains=search)
            )

        category = request.query_params.get('category', '')
        if category:
            qs = qs.filter(registration_category=category)

        entry_year = request.query_params.get('entry_year', '')
        if entry_year:
            qs = qs.filter(entry_year=entry_year)

        intake = request.query_params.get('intake', '')
        if intake:
            qs = qs.filter(intake=intake)

        center = request.query_params.get('center', '')
        if center:
            qs = qs.filter(assessment_center__center_name=center)

        occupation = request.query_params.get('occupation', '')
        if occupation:
            qs = qs.filter(occupation__occ_name=occupation)

        printed = request.query_params.get('printed', '')
        if printed == 'yes':
            qs = qs.filter(transcript_serial_number__isnull=False).exclude(transcript_serial_number='')
        elif printed == 'no':
            qs = qs.filter(Q(transcript_serial_number__isnull=True) | Q(transcript_serial_number=''))

        collection_status = request.query_params.get('collection_status', '')
        if collection_status == 'taken':
            qs = qs.filter(transcript_collected=True)
        elif collection_status == 'not_taken':
            qs = qs.filter(transcript_collected=False)

        return qs

    def _serialize_candidate(self, candidate):
        """Serialize a single candidate to dict."""
        award = ""
        completion_year = ""
        
        if candidate.registration_category == 'modular':
            if candidate.occupation:
                award = candidate.occupation.award_modular or ""
            modular_results_list = list(candidate.modular_results.all())
            if modular_results_list and modular_results_list[0].assessment_series:
                completion_year = modular_results_list[0].assessment_series.completion_year or modular_results_list[0].assessment_series.name or ""
        else:
            qualifies, _ = formal_candidate_qualifies(candidate)
            if not qualifies:
                return None
            
            formal_results_list = list(candidate.formal_results.all())
            if formal_results_list:
                if formal_results_list[0].level:
                    award = formal_results_list[0].level.award or ""
                if formal_results_list[0].assessment_series:
                    completion_year = formal_results_list[0].assessment_series.completion_year or formal_results_list[0].assessment_series.name or ""

        return {
            'id': candidate.id,
            'passport_photo': candidate.passport_photo.url if candidate.passport_photo else None,
            'registration_number': candidate.registration_number or "",
            'full_name': candidate.full_name or "",
            'center_name': candidate.assessment_center.center_name if candidate.assessment_center else "",
            'center_id': candidate.assessment_center.id if candidate.assessment_center else None,
            'registration_category': candidate.get_registration_category_display() if candidate.registration_category else "",
            'registration_category_code': candidate.registration_category or "",
            'occupation_name': candidate.occupation.occ_name if candidate.occupation else "",
            'occupation_id': candidate.occupation.id if candidate.occupation else None,
            'entry_year': candidate.entry_year or "",
            'intake': candidate.get_intake_display() if candidate.intake else "",
            'intake_code': candidate.intake or "",
            'assessment_intake': candidate.get_intake_display() if candidate.intake else "",
            'award': award,
            'completion_date': completion_year,
            'printed': bool(candidate.transcript_serial_number),
            'tr_sno': candidate.transcript_serial_number or "",
            'transcript_collected': candidate.transcript_collected,
            'transcript_collector_name': candidate.transcript_collector_name or "",
            'transcript_collector_phone': candidate.transcript_collector_phone or "",
            'transcript_collection_date': str(candidate.transcript_collection_date) if candidate.transcript_collection_date else "",
        }

    def list(self, request):
        """
        List candidates who have passed. Server-side pagination, search, and filtering.
        Default page_size=50. Use page_size=0 to load all (for export).
        """
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))

        candidates_qs = self._get_base_queryset()
        candidates_qs = self._apply_filters(candidates_qs, request)
        candidates_qs = candidates_qs.order_by('registration_number')

        total_count = candidates_qs.count()

        if page_size > 0:
            start = (page - 1) * page_size
            end = start + page_size
            candidates = list(candidates_qs[start:end])
        else:
            candidates = list(candidates_qs)

        data = []
        for candidate in candidates:
            item = self._serialize_candidate(candidate)
            if item:
                data.append(item)

        num_pages = max(1, (total_count + page_size - 1) // page_size) if page_size > 0 else 1

        return Response({
            'results': data,
            'count': total_count,
            'num_pages': num_pages,
            'current_page': page,
            'page_size': page_size,
            'has_next': page < num_pages if page_size > 0 else False,
            'has_previous': page > 1,
        })

    @action(detail=False, methods=['get'], url_path='filter-options')
    def filter_options(self, request):
        """Return unique centers and occupations for filter dropdowns."""
        candidates_qs = self._get_base_queryset()
        centers = list(
            candidates_qs.exclude(assessment_center__isnull=True)
            .values_list('assessment_center__center_name', flat=True)
            .distinct().order_by('assessment_center__center_name')
        )
        occupations = list(
            candidates_qs.exclude(occupation__isnull=True)
            .values_list('occupation__occ_name', flat=True)
            .distinct().order_by('occupation__occ_name')
        )
        return Response({'centers': centers, 'occupations': occupations})

    @action(detail=False, methods=['post'], url_path='update-collection-status')
    def update_collection_status(self, request):
        """
        Update transcript collection status for a candidate.
        """
        candidate_id = request.data.get('candidate_id')
        collected = request.data.get('collected', False)
        collector_name = request.data.get('collector_name', '')
        collector_phone = request.data.get('collector_phone', '')
        collection_date = request.data.get('collection_date', None)

        if not candidate_id:
            return Response(
                {'error': 'candidate_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not candidate.transcript_serial_number:
            return Response(
                {'error': 'Candidate does not have a printed transcript'},
                status=status.HTTP_400_BAD_REQUEST
            )

        candidate.transcript_collected = collected
        candidate.transcript_collector_name = collector_name if collected else None
        candidate.transcript_collector_phone = collector_phone if collected else None

        if collected and collection_date:
            candidate.transcript_collection_date = collection_date
        elif collected and not collection_date:
            from django.utils import timezone
            candidate.transcript_collection_date = timezone.now().date()
        elif not collected:
            candidate.transcript_collection_date = None

        candidate.save()

        return Response({
            'success': True,
            'message': 'Collection status updated',
            'transcript_collected': candidate.transcript_collected,
            'transcript_collector_name': candidate.transcript_collector_name or '',
            'transcript_collector_phone': candidate.transcript_collector_phone or '',
            'transcript_collection_date': str(candidate.transcript_collection_date) if candidate.transcript_collection_date else '',
        })

    @action(detail=False, methods=['post'], url_path='collect-transcripts')
    def collect_transcripts(self, request):
        """
        Collect transcripts for multiple candidates from the same center.
        Creates a TranscriptCollection record and updates each candidate's collection status.
        """
        from django.utils import timezone

        candidate_ids = request.data.getlist('candidate_ids') if hasattr(request.data, 'getlist') else request.data.get('candidate_ids', [])
        # Handle comma-separated string from FormData
        if isinstance(candidate_ids, str):
            candidate_ids = [int(x.strip()) for x in candidate_ids.split(',') if x.strip()]
        elif isinstance(candidate_ids, list) and len(candidate_ids) == 1 and isinstance(candidate_ids[0], str):
            candidate_ids = [int(x.strip()) for x in candidate_ids[0].split(',') if x.strip()]
        else:
            candidate_ids = [int(x) for x in candidate_ids]

        designation = request.data.get('designation', '')
        nin = request.data.get('nin', '')
        collector_name = request.data.get('collector_name', '')
        collector_phone = request.data.get('collector_phone', '')
        email = request.data.get('email', '')
        collection_date = request.data.get('collection_date', '')
        signature_data = request.data.get('signature_data', '')
        supporting_document = request.FILES.get('supporting_document')

        # Validate required fields
        errors = {}
        if not candidate_ids:
            errors['candidate_ids'] = 'At least one candidate must be selected'
        if not designation:
            errors['designation'] = 'Designation is required'
        if not nin:
            errors['nin'] = 'NIN is required'
        if not collector_name:
            errors['collector_name'] = 'Collector Name is required'
        if not collector_phone:
            errors['collector_phone'] = 'Phone Number is required'
        if not email:
            errors['email'] = 'Email is required'
        if designation in ('candidate', 'other_person') and not supporting_document:
            errors['supporting_document'] = 'Supporting document is required for Candidate and Other Person designations'

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        if not collection_date:
            collection_date = timezone.now().date()

        # Validate candidates exist, have printed transcripts, and belong to the same center
        candidates = list(Candidate.objects.filter(id__in=candidate_ids).select_related('assessment_center'))
        if len(candidates) != len(candidate_ids):
            return Response(
                {'error': 'Some candidates were not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check all candidates have printed transcripts
        not_printed = [c for c in candidates if not c.transcript_serial_number]
        if not_printed:
            names = ', '.join([c.registration_number or str(c.id) for c in not_printed])
            return Response(
                {'error': f'The following candidates do not have printed transcripts: {names}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check all candidates belong to the same center
        center_ids = set(c.assessment_center_id for c in candidates if c.assessment_center_id)
        if len(center_ids) != 1:
            return Response(
                {'error': 'All selected candidates must belong to the same center'},
                status=status.HTTP_400_BAD_REQUEST
            )

        center_id = center_ids.pop()

        # Check none are already collected
        already_collected = [c for c in candidates if c.transcript_collected]
        if already_collected:
            names = ', '.join([c.registration_number or str(c.id) for c in already_collected])
            return Response(
                {'error': f'The following candidates have already had their transcripts collected: {names}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the collection record
        receipt_number = TranscriptCollection.generate_receipt_number()
        collection = TranscriptCollection.objects.create(
            designation=designation,
            nin=nin,
            assessment_center_id=center_id,
            collector_name=collector_name,
            collector_phone=collector_phone,
            email=email,
            collection_date=collection_date,
            signature_data=signature_data or None,
            supporting_document=supporting_document,
            candidate_count=len(candidates),
            receipt_number=receipt_number,
            created_by=request.user if request.user.is_authenticated else None,
        )
        collection.candidates.set(candidates)

        # Update each candidate's collection status
        for candidate in candidates:
            candidate.transcript_collected = True
            candidate.transcript_collector_name = collector_name
            candidate.transcript_collector_phone = collector_phone
            candidate.transcript_collection_date = collection_date
            candidate.save(update_fields=[
                'transcript_collected',
                'transcript_collector_name',
                'transcript_collector_phone',
                'transcript_collection_date',
            ])

        # Build response with receipt data for printing
        candidate_list = [{
            'registration_number': c.registration_number,
            'full_name': c.full_name,
            'tr_sno': c.transcript_serial_number,
        } for c in candidates]

        issued_by = ''
        if request.user.is_authenticated:
            issued_by = f'{request.user.first_name} {request.user.last_name}'.strip() or request.user.username

        receipt = {
            'receipt_number': receipt_number,
            'designation': designation,
            'nin': nin,
            'center_name': collection.assessment_center.center_name,
            'collector_name': collector_name,
            'collector_phone': collector_phone,
            'email': email,
            'collection_date': str(collection_date),
            'candidate_count': len(candidates),
            'candidates': candidate_list,
            'issued_by': issued_by,
            'signature_data': signature_data or '',
        }

        # Send receipt email to collector in background
        if email:
            from awards.emails import send_collection_receipt_email
            send_collection_receipt_email(receipt, email)

        return Response({
            'success': True,
            'message': f'{len(candidates)} transcript(s) marked as collected',
            'receipt': receipt,
        })

    @action(detail=False, methods=['post'], url_path='bulk-print-transcripts')
    def bulk_print_transcripts(self, request):
        """
        Generate transcripts for multiple candidates and merge into a single PDF.
        Only allows printing for candidates who haven't been printed yet.
        """
        candidate_ids = request.data.get('candidate_ids', [])
        
        if not candidate_ids:
            return Response(
                {'error': 'No candidates selected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if any candidate already has a transcript printed
        already_printed = Candidate.objects.filter(
            id__in=candidate_ids,
            transcript_serial_number__isnull=False
        ).exclude(transcript_serial_number='')
        
        if already_printed.exists():
            return Response(
                {
                    'error': 'All selected candidate(s) already have printed transcripts. Only reprints are allowed through the reprint process.',
                    'already_printed_count': already_printed.count()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get candidates
        candidates = Candidate.objects.filter(id__in=candidate_ids).select_related(
            'occupation', 'assessment_center'
        ).order_by('registration_number')
        
        if not candidates.exists():
            return Response(
                {'error': 'No valid candidates found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Import transcript generation functions
        from results.views import ModularResultViewSet, FormalResultViewSet
        
        # Create PDF merger
        merger = PdfMerger()
        generated_count = 0
        
        for candidate in candidates:
            try:
                # Create a mock request with the candidate ID in query_params
                class MockRequest:
                    def __init__(self, user, candidate_id):
                        self.user = user
                        self.query_params = {'candidate_id': str(candidate_id)}
                
                mock_request = MockRequest(request.user, candidate.id)
                
                if candidate.registration_category == 'modular':
                    # Check if candidate has modular results
                    if ModularResult.objects.filter(candidate=candidate).exists():
                        viewset = ModularResultViewSet()
                        response = viewset.transcript_pdf(mock_request)
                        
                        if response.status_code == 200:
                            pdf_buffer = BytesIO(response.content)
                            merger.append(pdf_buffer)
                            generated_count += 1
                else:
                    # Formal candidate
                    if FormalResult.objects.filter(candidate=candidate).exists():
                        viewset = FormalResultViewSet()
                        response = viewset.transcript_pdf(mock_request)
                        
                        if response.status_code == 200:
                            pdf_buffer = BytesIO(response.content)
                            merger.append(pdf_buffer)
                            generated_count += 1
            except Exception as e:
                # Log error but continue with other candidates
                print(f"Error generating transcript for candidate {candidate.id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if generated_count == 0:
            return Response(
                {'error': 'No transcripts could be generated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Write merged PDF to response
        output = BytesIO()
        merger.write(output)
        merger.close()
        output.seek(0)
        
        response = HttpResponse(output.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Transcripts.pdf"'
        
        return response

    @action(detail=False, methods=['post'], url_path='bulk-upload-serial-numbers')
    def bulk_upload_serial_numbers(self, request):
        """
        Bulk upload transcript serial numbers from an Excel file.
        Expected columns: Registration Number, TR SNo
        Validates each row and returns detailed results.
        """
        import openpyxl

        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'No file uploaded'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file type
        if not file.name.endswith(('.xlsx', '.xls')):
            return Response(
                {'error': 'Invalid file format. Please upload an Excel file (.xlsx or .xls)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            wb = openpyxl.load_workbook(file, read_only=True)
            ws = wb.active
        except Exception as e:
            return Response(
                {'error': f'Could not read Excel file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Read header row
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return Response(
                {'error': 'Excel file is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        header = [str(cell).strip().lower() if cell else '' for cell in rows[0]]

        # Find column indices
        reg_col = None
        sno_col = None
        for i, h in enumerate(header):
            if h in ('registration number', 'reg no', 'regno', 'registration_number'):
                reg_col = i
            elif h in ('tr sno', 'trsno', 'tr_sno', 'serial number', 'serial_number', 'serialno'):
                sno_col = i

        if reg_col is None or sno_col is None:
            return Response(
                {'error': 'Excel file must have columns: "Registration Number" and "TR SNo"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data_rows = rows[1:]
        if not data_rows:
            return Response(
                {'error': 'Excel file has no data rows'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build set of qualifying candidate IDs (candidates in awards module)
        qualifying_ids = set(
            self._get_base_queryset().values_list('id', flat=True)
        )

        results = []
        success_count = 0
        error_count = 0
        total_rows = len(data_rows)

        for idx, row in enumerate(data_rows, start=2):
            reg_no = str(row[reg_col]).strip() if row[reg_col] else ''
            tr_sno = str(row[sno_col]).strip() if row[sno_col] else ''

            # Skip completely empty rows
            if not reg_no and not tr_sno:
                continue

            row_result = {
                'row': idx,
                'registration_number': reg_no,
                'tr_sno': tr_sno,
            }

            # Validate required fields
            if not reg_no:
                row_result['status'] = 'error'
                row_result['message'] = 'Registration Number is missing'
                results.append(row_result)
                error_count += 1
                continue

            if not tr_sno:
                row_result['status'] = 'error'
                row_result['message'] = 'TR SNo is missing'
                results.append(row_result)
                error_count += 1
                continue

            # Find candidate
            try:
                candidate = Candidate.objects.get(registration_number=reg_no)
            except Candidate.DoesNotExist:
                row_result['status'] = 'error'
                row_result['message'] = f'Candidate with Reg No "{reg_no}" not found'
                results.append(row_result)
                error_count += 1
                continue
            except Candidate.MultipleObjectsReturned:
                row_result['status'] = 'error'
                row_result['message'] = f'Multiple candidates found with Reg No "{reg_no}"'
                results.append(row_result)
                error_count += 1
                continue

            # Check if candidate qualifies for awards (is in the awards module)
            if candidate.id not in qualifying_ids:
                row_result['status'] = 'error'
                row_result['message'] = f'Candidate "{reg_no}" does not qualify for a transcript. They must be in the awards module first.'
                results.append(row_result)
                error_count += 1
                continue

            # Check if serial number is already assigned to another candidate
            existing = Candidate.objects.filter(
                transcript_serial_number=tr_sno
            ).exclude(id=candidate.id).first()
            if existing:
                row_result['status'] = 'error'
                row_result['message'] = f'Serial No "{tr_sno}" is already assigned to {existing.registration_number} ({existing.full_name})'
                results.append(row_result)
                error_count += 1
                continue

            # Check if candidate already has a serial number
            if candidate.transcript_serial_number:
                row_result['status'] = 'error'
                row_result['message'] = f'Candidate already has Serial No "{candidate.transcript_serial_number}". Cannot override.'
                results.append(row_result)
                error_count += 1
                continue

            # All checks passed — assign serial number
            candidate.transcript_serial_number = tr_sno
            candidate.save(update_fields=['transcript_serial_number'])
            row_result['status'] = 'success'
            row_result['message'] = 'Serial number assigned successfully'
            row_result['candidate_name'] = candidate.full_name
            results.append(row_result)
            success_count += 1

        wb.close()

        return Response({
            'total_rows': total_rows,
            'success_count': success_count,
            'error_count': error_count,
            'results': results,
        })

    @action(detail=False, methods=['post'], url_path='reprint-transcripts')
    def reprint_transcripts(self, request):
        """
        Reprint transcripts for candidates who already have printed transcripts.
        Requires a reprint reason. If reason requires duplicate watermark (e.g., Lost Transcript),
        the PDF will have a "DUPLICATE" watermark.
        """
        candidate_ids = request.data.get('candidate_ids', [])
        reason_id = request.data.get('reason_id')
        
        if not candidate_ids:
            return Response(
                {'error': 'No candidates selected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not reason_id:
            return Response(
                {'error': 'Reprint reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get reprint reason
        try:
            reprint_reason = ReprintReason.objects.get(id=reason_id, is_active=True)
        except ReprintReason.DoesNotExist:
            return Response(
                {'error': 'Invalid reprint reason'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get candidates
        candidates = Candidate.objects.filter(id__in=candidate_ids).select_related(
            'occupation', 'assessment_center'
        ).order_by('registration_number')
        
        if not candidates.exists():
            return Response(
                {'error': 'No valid candidates found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Import transcript generation functions
        from results.views import ModularResultViewSet, FormalResultViewSet
        
        # Create PDF merger
        merger = PdfMerger()
        generated_count = 0
        
        # Determine if watermark is needed
        add_watermark = reprint_reason.requires_duplicate_watermark
        
        for candidate in candidates:
            try:
                # Create a mock request with the candidate ID and watermark flag
                class MockRequest:
                    def __init__(self, user, candidate_id, duplicate_watermark=False):
                        self.user = user
                        self.query_params = {
                            'candidate_id': str(candidate_id),
                            'duplicate_watermark': 'true' if duplicate_watermark else 'false'
                        }
                
                mock_request = MockRequest(request.user, candidate.id, add_watermark)
                
                if candidate.registration_category == 'modular':
                    # Check if candidate has modular results
                    if ModularResult.objects.filter(candidate=candidate).exists():
                        viewset = ModularResultViewSet()
                        response = viewset.transcript_pdf(mock_request)
                        
                        if response.status_code == 200:
                            pdf_buffer = BytesIO(response.content)
                            merger.append(pdf_buffer)
                            generated_count += 1
                elif candidate.registration_category == 'formal':
                    # Formal candidate
                    if FormalResult.objects.filter(candidate=candidate).exists():
                        viewset = FormalResultViewSet()
                        response = viewset.transcript_pdf(mock_request)
                        
                        if response.status_code == 200:
                            pdf_buffer = BytesIO(response.content)
                            merger.append(pdf_buffer)
                            generated_count += 1
            except Exception as e:
                # Log error but continue with other candidates
                print(f"Error generating transcript for candidate {candidate.id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if generated_count == 0:
            return Response(
                {'error': 'No transcripts could be generated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Write merged PDF to response
        output = BytesIO()
        merger.write(output)
        merger.close()
        output.seek(0)
        
        response = HttpResponse(output.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Reprinted_Transcripts.pdf"'
        
        return response

    @action(detail=False, methods=['get'], url_path='collection-receipts')
    def collection_receipts(self, request):
        """
        List all transcript collection receipts with search, filtering, and pagination.
        """
        qs = TranscriptCollection.objects.select_related(
            'assessment_center', 'created_by'
        ).all()

        # Search
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(receipt_number__icontains=search) |
                Q(collector_name__icontains=search) |
                Q(nin__icontains=search) |
                Q(assessment_center__center_name__icontains=search)
            )

        # Filter by center
        center_id = request.query_params.get('center_id')
        if center_id:
            qs = qs.filter(assessment_center_id=center_id)

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        paginator = Paginator(qs, page_size)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        serializer = TranscriptCollectionListSerializer(page_obj.object_list, many=True)
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
        })

    @action(detail=False, methods=['delete'], url_path='collection-receipts/(?P<receipt_id>[0-9]+)/revoke')
    def revoke_collection_receipt(self, request, receipt_id=None):
        """
        Revoke/delete a collection receipt. Resets candidate collection status.
        """
        try:
            collection = TranscriptCollection.objects.prefetch_related('candidates').get(id=receipt_id)
        except TranscriptCollection.DoesNotExist:
            return Response(
                {'error': 'Collection receipt not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Reset candidate collection fields
        candidates = collection.candidates.all()
        for candidate in candidates:
            candidate.transcript_collected = False
            candidate.transcript_collector_name = None
            candidate.transcript_collector_phone = None
            candidate.transcript_collection_date = None
            candidate.save(update_fields=[
                'transcript_collected',
                'transcript_collector_name',
                'transcript_collector_phone',
                'transcript_collection_date',
            ])

        receipt_number = collection.receipt_number
        collection.delete()

        return Response({
            'success': True,
            'message': f'Receipt {receipt_number} revoked. {candidates.count()} candidate(s) reset.',
        })

    @action(detail=False, methods=['get'], url_path='collection-receipts/(?P<receipt_id>[0-9]+)')
    def collection_receipt_detail(self, request, receipt_id=None):
        """
        Get detailed view of a single transcript collection receipt.
        """
        try:
            collection = TranscriptCollection.objects.select_related(
                'assessment_center', 'created_by'
            ).prefetch_related('candidates__assessment_center').get(id=receipt_id)
        except TranscriptCollection.DoesNotExist:
            return Response(
                {'error': 'Collection receipt not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TranscriptCollectionDetailSerializer(collection)
        return Response(serializer.data)
