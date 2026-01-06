from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse
from decimal import Decimal
from datetime import date
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from .models import Candidate, CandidateEnrollment, EnrollmentModule, EnrollmentPaper
from .serializers import (
    CandidateListSerializer,
    CandidateDetailSerializer,
    CandidateCreateUpdateSerializer,
    CandidateEnrollmentSerializer,
    EnrollCandidateSerializer
)
from occupations.models import OccupationLevel, OccupationModule, OccupationPaper
from assessment_series.models import AssessmentSeries


class CandidateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing candidates
    """
    permission_classes = [AllowAny]  # TODO: Change to IsAuthenticated after auth is set up
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['registration_number', 'full_name', 'contact', 'refugee_number']
    ordering_fields = ['created_at', 'full_name', 'registration_number']
    ordering = ['-created_at']
    
    filterset_fields = {
        'registration_category': ['exact'],
        'assessment_center': ['exact'],
        'occupation': ['exact'],
        'has_disability': ['exact'],
        'is_refugee': ['exact'],
        'verification_status': ['exact'],
        'status': ['exact'],
        'gender': ['exact'],
        'entry_year': ['exact'],
        'intake': ['exact'],
    }
    
    def get_queryset(self):
        """Optimize queryset with select_related and prefetch_related"""
        queryset = Candidate.objects.select_related(
            'district',
            'village',
            'nature_of_disability',
            'assessment_center',
            'assessment_center_branch',
            'occupation',
            'occupation__sector',
            'created_by',
            'updated_by',
            'verified_by'
        ).all()
        
        # Filter by center for center representatives
        if self.request.user.is_authenticated and self.request.user.user_type == 'center_representative':
            if hasattr(self.request.user, 'center_rep_profile'):
                center_rep = self.request.user.center_rep_profile
                queryset = queryset.filter(assessment_center=center_rep.assessment_center)
                # If center rep is assigned to a specific branch, filter by that branch too
                if center_rep.assessment_center_branch:
                    queryset = queryset.filter(assessment_center_branch=center_rep.assessment_center_branch)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CandidateListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CandidateCreateUpdateSerializer
        return CandidateDetailSerializer
    
    def perform_create(self, serializer):
        """Set created_by when creating a candidate"""
        staff = None
        if hasattr(self.request.user, 'staff'):
            staff = self.request.user.staff
        serializer.save(created_by=staff, updated_by=staff)
    
    def perform_update(self, serializer):
        """Set updated_by when updating a candidate"""
        staff = None
        if hasattr(self.request.user, 'staff'):
            staff = self.request.user.staff
        serializer.save(updated_by=staff)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a candidate"""
        candidate = self.get_object()
        staff = None
        if hasattr(request.user, 'staff'):
            staff = request.user.staff
        
        candidate.verification_status = 'verified'
        candidate.verified_by = staff
        from django.utils import timezone
        candidate.verification_date = timezone.now()
        candidate.save()
        
        serializer = self.get_serializer(candidate)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline a candidate"""
        candidate = self.get_object()
        staff = None
        if hasattr(request.user, 'staff'):
            staff = request.user.staff
        
        reason = request.data.get('reason', '')
        candidate.verification_status = 'declined'
        candidate.verified_by = staff
        candidate.decline_reason = reason
        from django.utils import timezone
        candidate.verification_date = timezone.now()
        candidate.save()
        
        serializer = self.get_serializer(candidate)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def clear_payment(self, request, pk=None):
        """Mark payment as cleared for a candidate"""
        candidate = self.get_object()
        staff = None
        if hasattr(request.user, 'staff'):
            staff = request.user.staff
        
        candidate.payment_cleared = True
        from django.utils import timezone
        candidate.payment_cleared_date = timezone.now().date()
        candidate.payment_cleared_by = staff
        candidate.payment_amount_cleared = request.data.get('amount', 0)
        candidate.payment_center_series_ref = request.data.get('reference', '')
        candidate.save()
        
        serializer = self.get_serializer(candidate)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_photo(self, request, pk=None):
        """Upload passport photo"""
        candidate = self.get_object()
        if 'passport_photo' in request.FILES:
            candidate.passport_photo = request.FILES['passport_photo']
            candidate.save()
            serializer = self.get_serializer(candidate)
            return Response(serializer.data)
        return Response(
            {'error': 'No photo file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """Upload identification or qualification document"""
        candidate = self.get_object()
        
        if 'identification_document' in request.FILES:
            candidate.identification_document = request.FILES['identification_document']
        elif 'qualification_document' in request.FILES:
            candidate.qualification_document = request.FILES['qualification_document']
        else:
            return Response(
                {'error': 'No document file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        candidate.save()
        serializer = self.get_serializer(candidate)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get candidate statistics"""
        queryset = self.filter_queryset(self.get_queryset())
        
        stats = {
            'total': queryset.count(),
            'by_category': {
                'modular': queryset.filter(registration_category='modular').count(),
                'formal': queryset.filter(registration_category='formal').count(),
                'workers_pas': queryset.filter(registration_category='workers_pas').count(),
            },
            'by_status': {
                'verified': queryset.filter(verification_status='verified').count(),
                'pending': queryset.filter(verification_status='pending_verification').count(),
                'declined': queryset.filter(verification_status='declined').count(),
            },
            'by_gender': {
                'male': queryset.filter(gender='male').count(),
                'female': queryset.filter(gender='female').count(),
            },
            'refugees': queryset.filter(is_refugee=True).count(),
            'with_disability': queryset.filter(has_disability=True).count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def export(self, request):
        """Export candidates to Excel - optimized for large datasets"""
        candidate_ids = request.data.get('ids', [])
        export_all = request.data.get('export_all', False)
        
        # Get queryset based on filters or IDs - use values() for speed
        if export_all:
            queryset = self.filter_queryset(self.get_queryset())
        elif candidate_ids:
            queryset = self.get_queryset().filter(id__in=candidate_ids)
        else:
            return Response({'error': 'No candidates selected'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use values for faster data retrieval (avoid model instantiation)
        candidates = queryset.values(
            'registration_number', 'full_name', 'date_of_birth', 'gender',
            'nationality', 'contact', 'has_disability', 'is_refugee',
            'assessment_center__center_name', 'registration_category',
            'occupation__occ_name', 'occupation__sector__name', 'district__name'
        )
        
        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Candidates"
        
        # Define headers and column widths
        headers = [
            ('Reg No', 20), ('Full Name', 25), ('Center', 30), ('Category', 12), 
            ('Occupation', 20), ('Sector', 15), ('Disability', 10), ('Refugee', 10), 
            ('Nationality', 12), ('Age', 6), ('District', 15), ('Gender', 8), ('Contact', 15)
        ]
        
        # Style for headers only
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        
        # Write headers and set column widths
        for col, (header, width) in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            ws.column_dimensions[cell.column_letter].width = width
        
        # Category display mapping
        category_map = {'modular': 'Modular', 'formal': 'Formal', 'workers_pas': "Worker's PAS"}
        gender_map = {'male': 'Male', 'female': 'Female', 'other': 'Other'}
        
        # Calculate age helper
        today = date.today()
        def calc_age(dob):
            if not dob:
                return ''
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        # Write data rows (no styling for speed)
        for row_num, c in enumerate(candidates, 2):
            ws.cell(row=row_num, column=1, value=c['registration_number'] or '')
            ws.cell(row=row_num, column=2, value=c['full_name'] or '')
            ws.cell(row=row_num, column=3, value=c['assessment_center__center_name'] or '')
            ws.cell(row=row_num, column=4, value=category_map.get(c['registration_category'], ''))
            ws.cell(row=row_num, column=5, value=c['occupation__occ_name'] or '')
            ws.cell(row=row_num, column=6, value=c['occupation__sector__name'] or '')
            ws.cell(row=row_num, column=7, value='Yes' if c['has_disability'] else 'No')
            ws.cell(row=row_num, column=8, value='Yes' if c['is_refugee'] else 'No')
            ws.cell(row=row_num, column=9, value=c['nationality'] or 'Uganda')
            ws.cell(row=row_num, column=10, value=calc_age(c['date_of_birth']))
            ws.cell(row=row_num, column=11, value=c['district__name'] or '')
            ws.cell(row=row_num, column=12, value=gender_map.get(c['gender'], ''))
            ws.cell(row=row_num, column=13, value=c['contact'] or '')
        
        # Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=candidates_export_{date.today().strftime("%Y%m%d")}.xlsx'
        wb.save(response)
        
        return response
    
    @action(detail=True, methods=['get'])
    def enrollments(self, request, pk=None):
        """Get all enrollments for a candidate"""
        candidate = self.get_object()
        enrollments = candidate.enrollments.select_related(
            'assessment_series',
            'occupation_level',
            'occupation_level__occupation'
        ).prefetch_related('modules', 'papers').all()
        serializer = CandidateEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        """Enroll a candidate in an assessment series"""
        candidate = self.get_object()
        
        # Validate input
        serializer = EnrollCandidateSerializer(
            data=request.data,
            context={'candidate': candidate}
        )
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        assessment_series = validated_data['assessment_series_obj']
        occupation_level = validated_data['occupation_level_obj']
        modules = validated_data.get('modules', [])
        papers = validated_data.get('papers', [])
        
        # Calculate billing
        total_amount = Decimal('0.00')
        reg_category = candidate.registration_category
        
        if reg_category == 'formal':
            # Formal: use formal_fee from the level
            total_amount = occupation_level.formal_fee
        
        elif reg_category == 'modular':
            # Modular: use modular fee based on number of modules
            if len(modules) == 1:
                total_amount = occupation_level.modular_fee_single_module
            elif len(modules) == 2:
                total_amount = occupation_level.modular_fee_double_module
        
        elif reg_category == 'workers_pas':
            # Workers PAS: fee per paper (75k per paper)
            # Get the per-paper fee from any level (they should all be the same)
            any_level = candidate.occupation.levels.first()
            if any_level:
                per_paper_fee = any_level.workers_pas_per_module_fee  # Using this as per-paper fee
                total_amount = per_paper_fee * len(papers)
        
        # Create enrollment with transaction
        try:
            with transaction.atomic():
                # Check if enrollment already exists
                if reg_category == 'workers_pas':
                    # For Workers PAS, check by candidate and assessment_series only
                    existing = CandidateEnrollment.objects.filter(
                        candidate=candidate,
                        assessment_series=assessment_series
                    ).first()
                else:
                    existing = CandidateEnrollment.objects.filter(
                        candidate=candidate,
                        assessment_series=assessment_series,
                        occupation_level=occupation_level
                    ).first()
                
                if existing:
                    return Response(
                        {'error': 'Candidate is already enrolled in this assessment series'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create enrollment
                enrollment = CandidateEnrollment.objects.create(
                    candidate=candidate,
                    assessment_series=assessment_series,
                    occupation_level=occupation_level,  # Will be None for Workers PAS
                    total_amount=total_amount
                )
                
                # For formal candidates, auto-enroll in all modules/papers for the level
                if reg_category == 'formal':
                    if occupation_level.structure_type == 'modules':
                        # Enroll in all modules for this level
                        all_modules = occupation_level.modules.all()
                        for module in all_modules:
                            EnrollmentModule.objects.create(
                                enrollment=enrollment,
                                module=module
                            )
                    elif occupation_level.structure_type == 'papers':
                        # Enroll in all papers for this level
                        all_papers = occupation_level.papers.all()
                        for paper in all_papers:
                            EnrollmentPaper.objects.create(
                                enrollment=enrollment,
                                paper=paper
                            )
                else:
                    # For modular/workers_pas, use the selected modules/papers
                    # Add modules
                    if modules:
                        for module_id in modules:
                            module = OccupationModule.objects.get(id=module_id)
                            EnrollmentModule.objects.create(
                                enrollment=enrollment,
                                module=module
                            )
                    
                    # Add papers
                    if papers:
                        for paper_id in papers:
                            paper = OccupationPaper.objects.get(id=paper_id)
                            EnrollmentPaper.objects.create(
                                enrollment=enrollment,
                                paper=paper
                            )
                
                # Return created enrollment
                enrollment_serializer = CandidateEnrollmentSerializer(enrollment)
                return Response(enrollment_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], url_path='enrollment-options')
    def enrollment_options(self, request, pk=None):
        """Get enrollment options for a candidate based on their registration category"""
        candidate = self.get_object()
        occupation = candidate.occupation
        
        if not occupation:
            return Response(
                {'error': 'Candidate has no occupation assigned'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reg_category = candidate.registration_category
        
        # Get assessment series
        assessment_series = AssessmentSeries.objects.filter(is_active=True).values('id', 'name', 'start_date', 'end_date')
        
        response_data = {
            'assessment_series': list(assessment_series),
            'registration_category': reg_category,
            'occupation': {
                'id': occupation.id,
                'occ_code': occupation.occ_code,
                'occ_name': occupation.occ_name,
            }
        }
        
        if reg_category == 'formal':
            # Formal: show all levels
            levels = occupation.levels.filter(is_active=True).values(
                'id', 'level_name', 'formal_fee'
            )
            response_data['levels'] = list(levels)
        
        elif reg_category == 'modular':
            # Modular: show level 1 with its modules
            level_1 = occupation.levels.filter(level_name__icontains='level 1', is_active=True).first()
            if level_1:
                modules = level_1.modules.filter(is_active=True).values(
                    'id', 'module_code', 'module_name'
                )
                response_data['level'] = {
                    'id': level_1.id,
                    'level_name': level_1.level_name,
                    'modular_fee_single_module': str(level_1.modular_fee_single_module),
                    'modular_fee_double_module': str(level_1.modular_fee_double_module),
                }
                response_data['modules'] = list(modules)
                response_data['module_limit'] = {'min': 1, 'max': 2}
        
        elif reg_category == 'workers_pas':
            # Workers PAS: show all levels with their modules and nested papers
            levels_data = []
            for level in occupation.levels.filter(is_active=True):
                modules_data = []
                for module in level.modules.filter(is_active=True):
                    # Get papers that belong to this module
                    papers = module.papers.filter(is_active=True).values(
                        'id', 'paper_code', 'paper_name', 'paper_type'
                    )
                    modules_data.append({
                        'id': module.id,
                        'module_code': module.module_code,
                        'module_name': module.module_name,
                        'papers': list(papers),
                    })
                
                levels_data.append({
                    'id': level.id,
                    'level_name': level.level_name,
                    'workers_pas_base_fee': str(level.workers_pas_base_fee),
                    'workers_pas_per_module_fee': str(level.workers_pas_per_module_fee),
                    'modules': modules_data,
                })
            response_data['levels'] = levels_data
        
        return Response(response_data)
    
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit a draft candidate and generate registration number
        Format: UVT001/X/25/A/HD/M/001
        - UVT001: Center number
        - X: Nationality (U for Uganda, X for others)
        - 25: Entry year (last 2 digits)
        - A: Intake (M or A)
        - HD: Occupation code
        - M: Registration category (M=Modular, F=Formal, I=Workers PAS)
        - 001: Unique sequence per center+occupation
        """
        candidate = self.get_object()
        
        if candidate.is_submitted:
            return Response(
                {'error': 'Candidate has already been submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate required fields
        if not candidate.assessment_center:
            return Response(
                {'error': 'Assessment center is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not candidate.occupation:
            return Response(
                {'error': 'Occupation is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not candidate.entry_year:
            return Response(
                {'error': 'Entry year is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not candidate.intake:
            return Response(
                {'error': 'Intake is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not candidate.registration_category:
            return Response(
                {'error': 'Registration category is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build registration number components
        # 1. Center number (e.g., UVT001)
        center_number = candidate.assessment_center.center_number
        
        # 2. Nationality code (U for Uganda, X for others)
        nationality_code = 'U' if candidate.nationality == 'Uganda' else 'X'
        
        # 3. Entry year (last 2 digits)
        year_code = str(candidate.entry_year)[-2:]
        
        # 4. Intake (M or A)
        intake_code = candidate.intake
        
        # 5. Occupation code
        occ_code = candidate.occupation.occ_code
        
        # 6. Registration category code
        reg_cat_map = {
            'modular': 'M',
            'formal': 'F',
            'workers_pas': 'I'
        }
        reg_cat_code = reg_cat_map.get(candidate.registration_category, 'M')
        
        # 7. Sequence number (unique per center + occupation)
        # Find the last candidate with same center and occupation
        last_candidate = Candidate.objects.filter(
            assessment_center=candidate.assessment_center,
            occupation=candidate.occupation,
            is_submitted=True,
            registration_number__isnull=False
        ).order_by('-id').first()
        
        if last_candidate and last_candidate.registration_number:
            # Extract the sequence number (last part after final /)
            parts = last_candidate.registration_number.split('/')
            try:
                last_seq = int(parts[-1])
                new_seq = last_seq + 1
            except (ValueError, IndexError):
                new_seq = 1
        else:
            new_seq = 1
        
        # Generate registration number
        registration_number = f'{center_number}/{nationality_code}/{year_code}/{intake_code}/{occ_code}/{reg_cat_code}/{new_seq:04d}'
        
        # Update candidate with registration number first
        candidate.registration_number = registration_number
        candidate.is_submitted = True
        candidate.save()
        
        # Generate payment code after saving (so candidate.pk is available)
        payment_code = candidate.generate_payment_code()
        if payment_code:
            candidate.payment_code = payment_code
            candidate.save()
        
        return Response(
            {
                'message': 'Candidate submitted successfully',
                'registration_number': registration_number,
                'payment_code': payment_code
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_photo(self, request, pk=None):
        """Upload passport photo"""
        candidate = self.get_object()
        
        if 'photo' not in request.FILES:
            return Response(
                {'error': 'No photo file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        candidate.passport_photo = request.FILES['photo']
        candidate.save()
        
        return Response(
            {
                'message': 'Photo uploaded successfully',
                'photo_url': candidate.passport_photo.url if candidate.passport_photo else None
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_document(self, request, pk=None):
        """Upload identification or qualification document"""
        candidate = self.get_object()
        
        document_type = request.data.get('document_type')
        
        if document_type not in ['identification', 'qualification']:
            return Response(
                {'error': 'Invalid document type. Must be "identification" or "qualification"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'document' not in request.FILES:
            return Response(
                {'error': 'No document file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if document_type == 'identification':
            candidate.identification_document = request.FILES['document']
        else:
            candidate.qualification_document = request.FILES['document']
        
        candidate.save()
        
        return Response(
            {
                'message': f'{document_type.capitalize()} document uploaded successfully',
                'document_url': (
                    candidate.identification_document.url if document_type == 'identification'
                    else candidate.qualification_document.url
                ) if (candidate.identification_document or candidate.qualification_document) else None
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def generate_payment_code(self, request, pk=None):
        """Generate payment code for a candidate who has a registration number"""
        candidate = self.get_object()
        
        # Check if candidate is submitted and has registration number
        if not candidate.is_submitted:
            return Response(
                {'error': 'Candidate must be submitted first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not candidate.registration_number:
            return Response(
                {'error': 'Candidate must have a registration number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if payment code already exists
        if candidate.payment_code:
            return Response(
                {
                    'message': 'Payment code already exists',
                    'payment_code': candidate.payment_code
                },
                status=status.HTTP_200_OK
            )
        
        # Validate required fields
        if not all([candidate.assessment_center, candidate.entry_year, candidate.pk]):
            return Response(
                {'error': 'Missing required fields (assessment center, entry year, or candidate ID)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate payment code
        payment_code = candidate.generate_payment_code()
        
        if not payment_code:
            return Response(
                {'error': 'Failed to generate payment code'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Save payment code
        candidate.payment_code = payment_code
        candidate.save()
        
        return Response(
            {
                'message': 'Payment code generated successfully',
                'payment_code': payment_code
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def mark_payment_cleared(self, request, pk=None):
        """Mark candidate payment as cleared (for manual payment confirmation)"""
        candidate = self.get_object()
        
        # Check if candidate has enrollments
        if not candidate.enrollments.exists():
            return Response(
                {'error': 'Candidate has no enrollments to bill'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate total billed amount
        from django.db.models import Sum
        from decimal import Decimal
        total_billed = candidate.enrollments.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Mark payment as cleared
        candidate.payment_cleared = True
        candidate.payment_amount_cleared = total_billed
        candidate.payment_cleared_date = timezone.now()
        candidate.payment_cleared_by = request.user.get_full_name() or request.user.username
        
        # Set reference if not already set
        if not candidate.payment_center_series_ref:
            candidate.payment_center_series_ref = f'MANUAL-{timezone.now().strftime("%Y%m%d%H%M%S")}'
        
        candidate.save()
        
        return Response(
            {
                'message': 'Payment marked as cleared successfully',
                'payment_cleared': True,
                'amount_cleared': float(total_billed),
                'cleared_by': candidate.payment_cleared_by,
                'cleared_date': candidate.payment_cleared_date
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get candidate results based on registration category"""
        candidate = self.get_object()
        
        # Get results based on registration category
        if candidate.registration_category == 'modular':
            from results.models import ModularResult
            results = ModularResult.objects.filter(candidate=candidate).select_related(
                'assessment_series', 'module', 'entered_by'
            )
            
            results_data = []
            for result in results:
                results_data.append({
                    'id': result.id,
                    'assessment_series_name': result.assessment_series.name,
                    'module_name': result.module.module_name,
                    'module_code': result.module.module_code,
                    'type': result.type,
                    'mark': float(result.mark) if result.mark is not None else None,
                    'grade': result.grade,
                    'comment': result.comment,
                    'status': result.get_status_display(),
                    'entered_by': result.entered_by.get_full_name() if result.entered_by else None,
                    'entered_at': result.entered_at,
                })
            
            return Response(results_data, status=status.HTTP_200_OK)
        
        elif candidate.registration_category == 'formal':
            from results.models import FormalResult
            results = FormalResult.objects.filter(candidate=candidate).select_related(
                'assessment_series', 'level', 'exam', 'paper', 'entered_by'
            ).order_by('level__level_name', 'type')
            
            results_data = []
            for result in results:
                exam_or_paper_name = ''
                if result.exam:
                    exam_or_paper_name = result.exam.module_name
                elif result.paper:
                    exam_or_paper_name = result.paper.paper_name
                
                results_data.append({
                    'id': result.id,
                    'assessment_series': {
                        'id': result.assessment_series.id,
                        'name': result.assessment_series.name,
                    },
                    'level': {
                        'id': result.level.id,
                        'name': result.level.level_name,
                        'structure_type': result.level.structure_type,
                    },
                    'exam_or_paper': exam_or_paper_name,
                    'is_exam': result.exam is not None,
                    'type': result.type,
                    'mark': float(result.mark) if result.mark is not None else None,
                    'grade': result.grade,
                    'comment': result.comment,
                    'status': result.get_status_display(),
                    'entered_by': result.entered_by.get_full_name() if result.entered_by else None,
                    'entered_at': result.entered_at,
                })
            
            return Response(results_data, status=status.HTTP_200_OK)
        
        elif candidate.registration_category == 'workers_pas':
            from results.models import WorkersPasResult
            results = WorkersPasResult.objects.filter(candidate=candidate).select_related(
                'assessment_series', 'level', 'module', 'paper', 'entered_by'
            ).order_by('assessment_series', 'level', 'module', 'paper')
            
            results_data = []
            for result in results:
                results_data.append({
                    'id': result.id,
                    'assessment_series_name': result.assessment_series.name,
                    'level_name': result.level.level_name,
                    'module_code': result.module.module_code,
                    'module_name': result.module.module_name,
                    'paper_code': result.paper.paper_code,
                    'paper_name': result.paper.paper_name,
                    'type': result.type,
                    'mark': float(result.mark) if result.mark is not None else None,
                    'grade': result.grade,
                    'comment': result.comment,
                    'status': result.get_status_display(),
                    'entered_by_name': result.entered_by.get_full_name() if result.entered_by else None,
                    'entered_at': result.entered_at,
                })
            
            return Response(results_data, status=status.HTTP_200_OK)
        
        # Placeholder for other categories
        return Response([], status=status.HTTP_200_OK)
    
    # Modular results endpoints moved to results/views.py
    # - add_results -> /api/results/modular/add/
    # - enrollment_modules -> /api/results/modular/enrollment-modules/
    # - update_results -> /api/results/modular/update/
    # - verified_results_pdf -> /api/results/modular/verified-pdf/


# Standalone view for de-enrollment
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_enrollment_view(request, enrollment_id):
    """De-enroll a candidate by deleting their enrollment"""
    try:
        enrollment = CandidateEnrollment.objects.get(id=enrollment_id)
        candidate = enrollment.candidate
        
        # Check if candidate has any results
        from results.models import ModularResult, FormalResult, WorkersPasResult
        
        has_modular_results = ModularResult.objects.filter(
            candidate=candidate,
            assessment_series=enrollment.assessment_series
        ).exists()
        
        has_formal_results = FormalResult.objects.filter(
            candidate=candidate,
            assessment_series=enrollment.assessment_series
        ).exists()
        
        has_workers_pas_results = WorkersPasResult.objects.filter(
            candidate=candidate,
            assessment_series=enrollment.assessment_series
        ).exists()
        
        if has_modular_results or has_formal_results or has_workers_pas_results:
            return Response(
                {'error': 'Can\'t de-enroll, candidate already has marks'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment.delete()
        
        return Response(
            {'message': 'Enrollment deleted successfully'},
            status=status.HTTP_200_OK
        )
    except CandidateEnrollment.DoesNotExist:
        return Response(
            {'error': 'Enrollment not found'},
            status=status.HTTP_404_NOT_FOUND
        )
