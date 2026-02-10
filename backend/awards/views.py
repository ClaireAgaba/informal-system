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
from occupations.models import OccupationModule, OccupationPaper
from io import BytesIO
from PyPDF2 import PdfMerger
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
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

    @method_decorator(cache_page(60 * 15))
    def list(self, request):
        """
        List all candidates who have passed (all results are passing).
        Returns candidates from both modular and formal categories.
        Supports pagination with 'page' and 'page_size' query params.
        
        Pass marks:
        - Practical: 65%
        - Theory: 50%
        """
        # Get pagination parameters (page_size=0 means load all)
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 0)  # Default to all
        try:
            page = int(page)
            page_size = int(page_size)
        except (ValueError, TypeError):
            page = 1
            page_size = 0
        # Get candidates with modular results where ALL results are passing
        # A result is failing if: mark < 65 for practical, mark < 50 for theory, or mark is null/-1
        modular_candidates = Candidate.objects.filter(
            registration_category='modular'
        ).filter(
            Exists(ModularResult.objects.filter(candidate=OuterRef('pk')))
        ).exclude(
            # Exclude if any result is failing
            Exists(ModularResult.objects.filter(
                candidate=OuterRef('pk')
            ).filter(
                Q(mark__isnull=True) |
                Q(mark=-1) |
                Q(type='practical', mark__lt=65) |
                Q(type='theory', mark__lt=50)
            ))
        )

        # Get candidates with formal results where ALL results are passing
        formal_candidates = Candidate.objects.filter(
            registration_category='formal'
        ).filter(
            Exists(FormalResult.objects.filter(candidate=OuterRef('pk')))
        ).exclude(
            # Exclude if any result is failing
            Exists(FormalResult.objects.filter(
                candidate=OuterRef('pk')
            ).filter(
                Q(mark__isnull=True) |
                Q(mark=-1) |
                Q(type='practical', mark__lt=65) |
                Q(type='theory', mark__lt=50)
            ))
        )

        # Combine both querysets with prefetch for efficiency
        from django.db.models import Prefetch
        
        candidates_qs = (modular_candidates | formal_candidates).select_related(
            'occupation', 'assessment_center'
        ).prefetch_related(
            Prefetch('modular_results', queryset=ModularResult.objects.select_related('assessment_series')),
            Prefetch('formal_results', queryset=FormalResult.objects.select_related('level', 'assessment_series', 'paper')),
        ).order_by('-created_at')

        # Get total count first
        total_count = candidates_qs.count()
        
        # Paginate at database level (page_size=0 means load all)
        if page_size > 0:
            start = (page - 1) * page_size
            end = start + page_size
            candidates = list(candidates_qs[start:end])
            num_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
            has_next = page < num_pages
            has_previous = page > 1
        else:
            # Load all candidates
            candidates = list(candidates_qs)
            num_pages = 1
            has_next = False
            has_previous = False
            page = 1

        # Build response data (only for paginated subset)
        # Also filter out formal candidates without enough credit units
        data = []
        qualified_count = 0
        for candidate in candidates:
            # Get award and assessment series from prefetched results
            award = ""
            completion_year = ""
            
            if candidate.registration_category == 'modular':
                if candidate.occupation:
                    award = candidate.occupation.award_modular or ""
                modular_results_list = list(candidate.modular_results.all())
                if modular_results_list and modular_results_list[0].assessment_series:
                    completion_year = modular_results_list[0].assessment_series.completion_year or modular_results_list[0].assessment_series.name or ""
            else:
                # For formal candidates, check qualification
                qualifies, _ = formal_candidate_qualifies(candidate)
                if not qualifies:
                    # Skip this candidate - doesn't qualify
                    continue
                
                formal_results_list = list(candidate.formal_results.all())
                if formal_results_list:
                    if formal_results_list[0].level:
                        award = formal_results_list[0].level.award or ""
                    if formal_results_list[0].assessment_series:
                        completion_year = formal_results_list[0].assessment_series.completion_year or formal_results_list[0].assessment_series.name or ""

            qualified_count += 1
            data.append({
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
            })

        return Response({
            'results': data,
            'count': qualified_count,  # Only count candidates who actually qualify
            'num_pages': num_pages,
            'current_page': page,
            'page_size': page_size,
            'has_next': has_next,
            'has_previous': has_previous,
        })

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
        )
        
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
        )
        
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
