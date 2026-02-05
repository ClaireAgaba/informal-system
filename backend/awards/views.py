from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q, Exists, OuterRef
from django.http import HttpResponse
from candidates.models import Candidate
from results.models import ModularResult, FormalResult
from io import BytesIO
from PyPDF2 import PdfMerger


class AwardsViewSet(viewsets.ViewSet):
    """
    ViewSet to list candidates who qualify for awards.
    A candidate qualifies if:
    - They are enrolled
    - They have results
    - ALL their results are passing (based on mark thresholds)
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        List all candidates who have passed (all results are passing).
        Returns candidates from both modular and formal categories.
        
        Pass marks:
        - Practical: 65%
        - Theory: 50%
        """
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

        # Combine both querysets
        candidates = (modular_candidates | formal_candidates).select_related(
            'occupation', 'assessment_center'
        ).order_by('-created_at')

        # Build response data
        data = []
        for candidate in candidates:
            # Get award and assessment series from results
            award = ""
            assessment_series_name = ""
            completion_year = ""
            
            if candidate.registration_category == 'modular':
                # For modular, get from occupation.award_modular and results
                if candidate.occupation:
                    award = candidate.occupation.award_modular or ""
                modular_result = ModularResult.objects.filter(candidate=candidate).select_related('assessment_series').first()
                if modular_result and modular_result.assessment_series:
                    assessment_series_name = modular_result.assessment_series.name or ""
                    completion_year = modular_result.assessment_series.completion_year or ""
            else:
                # For formal, get from the level and results
                formal_result = FormalResult.objects.filter(candidate=candidate).select_related('level', 'assessment_series').first()
                if formal_result:
                    if formal_result.level:
                        award = formal_result.level.award or ""
                    if formal_result.assessment_series:
                        assessment_series_name = formal_result.assessment_series.name or ""
                        completion_year = formal_result.assessment_series.completion_year or ""

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
                'completion_date': completion_year or assessment_series_name,
                'printed': bool(candidate.transcript_serial_number),
                'tr_sno': candidate.transcript_serial_number or "",
            })

        return Response(data)

    @action(detail=False, methods=['post'], url_path='bulk-print-transcripts')
    def bulk_print_transcripts(self, request):
        """
        Generate transcripts for multiple candidates and merge into a single PDF.
        """
        candidate_ids = request.data.get('candidate_ids', [])
        
        if not candidate_ids:
            return Response(
                {'error': 'No candidates selected'},
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
