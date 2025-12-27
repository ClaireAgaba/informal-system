from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from candidates.models import EnrollmentModule, Candidate, CandidateEnrollment, EnrollmentPaper
from occupations.models import OccupationModule, OccupationLevel, OccupationPaper
from assessment_series.models import AssessmentSeries


class MarksheetViewSet(viewsets.ViewSet):
    """
    ViewSet for generating marksheets
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], url_path='generate-modular')
    def generate_modular_marksheet(self, request):
        """Generate Excel marksheet for modular candidates"""
        assessment_series_id = request.data.get('assessment_series')
        occupation_id = request.data.get('occupation')
        module_id = request.data.get('module')
        assessment_center_id = request.data.get('assessment_center')  # Optional
        
        if not all([assessment_series_id, occupation_id, module_id]):
            return Response(
                {'error': 'Assessment series, occupation, and module are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assessment_series = AssessmentSeries.objects.get(id=assessment_series_id)
            module = OccupationModule.objects.get(id=module_id, occupation_id=occupation_id)
        except (AssessmentSeries.DoesNotExist, OccupationModule.DoesNotExist):
            return Response(
                {'error': 'Invalid assessment series or module'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get enrolled candidates for this module
        enrollments = EnrollmentModule.objects.filter(
            module=module,
            enrollment__assessment_series=assessment_series,
            enrollment__candidate__registration_category='modular'
        ).select_related(
            'enrollment__candidate',
            'enrollment__candidate__occupation'
        ).order_by('enrollment__candidate__registration_number')
        
        # Filter by assessment center if provided
        if assessment_center_id:
            enrollments = enrollments.filter(
                enrollment__candidate__assessment_center_id=assessment_center_id
            )
        
        if not enrollments.exists():
            return Response(
                {'error': 'No enrolled candidates found for the selected parameters'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Marksheet"
        
        # Define headers
        headers = ['SN', 'REGISTRATION NO.', 'FULL NAME', 'OCCUPATION CODE', 
                  'CATEGORY', 'MODULE CODE', 'PRACTICAL']
        
        # Style for headers
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Write headers
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # Write data rows
        for idx, enrollment_module in enumerate(enrollments, 1):
            candidate = enrollment_module.enrollment.candidate
            
            ws.cell(row=idx+1, column=1, value=idx)
            ws.cell(row=idx+1, column=2, value=candidate.registration_number)
            ws.cell(row=idx+1, column=3, value=candidate.full_name)
            ws.cell(row=idx+1, column=4, value=candidate.occupation.occ_code if candidate.occupation else '')
            ws.cell(row=idx+1, column=5, value='Modular')
            ws.cell(row=idx+1, column=6, value=module.module_code)
            ws.cell(row=idx+1, column=7, value='')  # Empty for practical marks to be filled
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 18
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 15
        ws.column_dimensions['G'].width = 12
        
        # Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"Marksheet_{module.module_code}_{assessment_series.name.replace(' ', '_')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        return response
    
    @action(detail=False, methods=['post'], url_path='generate-formal')
    def generate_formal_marksheet(self, request):
        """Generate Excel marksheet for formal candidates"""
        assessment_series_id = request.data.get('assessment_series')
        occupation_id = request.data.get('occupation')
        level_id = request.data.get('level')
        structure_type = request.data.get('structure_type')
        assessment_center_id = request.data.get('assessment_center')  # Optional
        
        if not all([assessment_series_id, occupation_id, level_id, structure_type]):
            return Response(
                {'error': 'Assessment series, occupation, level, and structure type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assessment_series = AssessmentSeries.objects.get(id=assessment_series_id)
            level = OccupationLevel.objects.get(id=level_id, occupation_id=occupation_id)
        except (AssessmentSeries.DoesNotExist, OccupationLevel.DoesNotExist):
            return Response(
                {'error': 'Invalid assessment series or level'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get formal candidates for this occupation and level through enrollments
        candidates = Candidate.objects.filter(
            occupation_id=occupation_id,
            registration_category='formal',
            enrollments__assessment_series=assessment_series,
            enrollments__occupation_level=level
        ).select_related('occupation', 'assessment_center').distinct().order_by('registration_number')
        
        # Filter by assessment center if provided
        if assessment_center_id:
            candidates = candidates.filter(assessment_center_id=assessment_center_id)
        
        if not candidates.exists():
            return Response(
                {'error': 'No candidates found for the selected parameters'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Marksheet"
        
        # Style for headers
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        if structure_type == 'papers':
            # Paper-based marksheet
            # Get all papers for this level
            papers = OccupationPaper.objects.filter(level=level).order_by('paper_code')
            
            if not papers.exists():
                return Response(
                    {'error': 'No papers found for this level'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Define headers: Basic info + paper codes
            headers = ['SN', 'REGISTRATION NO.', 'FULL NAME', 'OCCUPATION CODE', 
                      'CATEGORY', 'LEVEL']
            
            # Add paper codes as columns
            for paper in papers:
                headers.append(paper.paper_code)
            
            # Write headers
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.value = header
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
            
            # Write data rows
            for idx, candidate in enumerate(candidates, 1):
                ws.cell(row=idx+1, column=1, value=idx)
                ws.cell(row=idx+1, column=2, value=candidate.registration_number)
                ws.cell(row=idx+1, column=3, value=candidate.full_name)
                ws.cell(row=idx+1, column=4, value=candidate.occupation.occ_code if candidate.occupation else '')
                ws.cell(row=idx+1, column=5, value='Formal')
                ws.cell(row=idx+1, column=6, value=level.level_name)
                
                # Empty cells for paper marks
                for paper_idx in range(len(papers)):
                    ws.cell(row=idx+1, column=7+paper_idx, value='')
            
            # Adjust column widths
            ws.column_dimensions['A'].width = 5
            ws.column_dimensions['B'].width = 25
            ws.column_dimensions['C'].width = 30
            ws.column_dimensions['D'].width = 18
            ws.column_dimensions['E'].width = 12
            ws.column_dimensions['F'].width = 15
            
            # Set width for paper columns
            for i in range(len(papers)):
                col_letter = get_column_letter(7 + i)
                ws.column_dimensions[col_letter].width = 12
        
        else:  # structure_type == 'modules'
            # Module-based marksheet with Theory and Practical columns
            # Get all modules for this level
            modules = OccupationModule.objects.filter(level=level).order_by('module_code')
            
            if not modules.exists():
                return Response(
                    {'error': 'No modules found for this level'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Define headers: Basic info + Theory/Practical for each module
            headers = ['SN', 'REGISTRATION NO.', 'FULL NAME', 'OCCUPATION CODE', 
                      'CATEGORY', 'LEVEL', 'THEORY', 'PRACTICAL']
            
            # Write headers
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.value = header
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
            
            # Write data rows
            for idx, candidate in enumerate(candidates, 1):
                ws.cell(row=idx+1, column=1, value=idx)
                ws.cell(row=idx+1, column=2, value=candidate.registration_number)
                ws.cell(row=idx+1, column=3, value=candidate.full_name)
                ws.cell(row=idx+1, column=4, value=candidate.occupation.occ_code if candidate.occupation else '')
                ws.cell(row=idx+1, column=5, value='Formal')
                ws.cell(row=idx+1, column=6, value=level.level_name)
                ws.cell(row=idx+1, column=7, value='')  # Theory
                ws.cell(row=idx+1, column=8, value='')  # Practical
            
            # Adjust column widths
            ws.column_dimensions['A'].width = 5
            ws.column_dimensions['B'].width = 25
            ws.column_dimensions['C'].width = 30
            ws.column_dimensions['D'].width = 18
            ws.column_dimensions['E'].width = 12
            ws.column_dimensions['F'].width = 15
            ws.column_dimensions['G'].width = 12
            ws.column_dimensions['H'].width = 12
        
        # Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"Marksheet_Formal_{level.level_name.replace(' ', '_')}_{assessment_series.name.replace(' ', '_')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        return response
    
    @action(detail=False, methods=['post'], url_path='generate-workers-pas')
    def generate_workers_pas_marksheet(self, request):
        """Generate Excel marksheet for Worker's PAS candidates with highlighted enrolled papers"""
        assessment_series_id = request.data.get('assessment_series')
        occupation_id = request.data.get('occupation')
        level_id = request.data.get('level')
        assessment_center_id = request.data.get('assessment_center')  # Optional
        
        if not all([assessment_series_id, occupation_id, level_id]):
            return Response(
                {'error': 'Assessment series, occupation, and level are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assessment_series = AssessmentSeries.objects.get(id=assessment_series_id)
            level = OccupationLevel.objects.get(id=level_id, occupation_id=occupation_id)
        except (AssessmentSeries.DoesNotExist, OccupationLevel.DoesNotExist):
            return Response(
                {'error': 'Invalid assessment series or level'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all papers for this level
        papers = OccupationPaper.objects.filter(level=level).order_by('paper_code')
        
        if not papers.exists():
            return Response(
                {'error': 'No papers found for this level'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get Worker's PAS candidates with enrollments
        # Note: Worker's PAS can select papers from any level, but we filter by papers in the selected level
        enrollments = CandidateEnrollment.objects.filter(
            assessment_series=assessment_series,
            candidate__occupation_id=occupation_id,
            candidate__registration_category='workers_pas',
            papers__paper__level=level
        ).select_related('candidate', 'candidate__occupation', 'candidate__assessment_center').prefetch_related(
            'papers__paper'
        ).distinct().order_by('candidate__registration_number')
        
        # Filter by assessment center if provided
        if assessment_center_id:
            enrollments = enrollments.filter(candidate__assessment_center_id=assessment_center_id)
        
        if not enrollments.exists():
            return Response(
                {'error': 'No candidates found for the selected parameters'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Marksheet"
        
        # Style for headers
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Style for highlighted cells (yellow)
        highlight_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        
        # Define headers: Basic info + paper codes
        headers = ['SN', 'REGISTRATION NO.', 'FULL NAME', 'OCCUPATION CODE', 
                  'CATEGORY', 'LEVEL']
        
        # Add paper codes as columns
        paper_list = list(papers)
        for paper in paper_list:
            headers.append(paper.paper_code)
        
        # Write headers
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # Write data rows
        for idx, enrollment in enumerate(enrollments, 1):
            candidate = enrollment.candidate
            
            ws.cell(row=idx+1, column=1, value=idx)
            ws.cell(row=idx+1, column=2, value=candidate.registration_number)
            ws.cell(row=idx+1, column=3, value=candidate.full_name)
            ws.cell(row=idx+1, column=4, value=candidate.occupation.occ_code if candidate.occupation else '')
            ws.cell(row=idx+1, column=5, value="Worker's PAS")
            ws.cell(row=idx+1, column=6, value=level.level_name)
            
            # Get enrolled papers for this candidate
            enrolled_paper_ids = set(enrollment.papers.values_list('paper_id', flat=True))
            
            # Fill paper columns and highlight enrolled ones
            for paper_idx, paper in enumerate(paper_list):
                cell = ws.cell(row=idx+1, column=7+paper_idx, value='')
                
                # Highlight if candidate is enrolled in this paper
                if paper.id in enrolled_paper_ids:
                    cell.fill = highlight_fill
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 18
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 15
        
        # Set width for paper columns
        for i in range(len(paper_list)):
            col_letter = get_column_letter(7 + i)
            ws.column_dimensions[col_letter].width = 12
        
        # Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"Marksheet_WorkersPAS_{level.level_name.replace(' ', '_')}_{assessment_series.name.replace(' ', '_')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        return response
