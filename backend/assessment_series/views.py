from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AssessmentSeries
from .serializers import AssessmentSeriesSerializer


class AssessmentSeriesViewSet(viewsets.ModelViewSet):
    """ViewSet for AssessmentSeries model"""
    queryset = AssessmentSeries.objects.all()
    serializer_class = AssessmentSeriesSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    
    @action(detail=True, methods=['post'])
    def set_current(self, request, pk=None):
        """Set this series as the current assessment series"""
        series = self.get_object()
        series.is_current = True
        series.save()
        serializer = self.get_serializer(series)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def release_results(self, request, pk=None):
        """Release results for this assessment series"""
        series = self.get_object()
        series.results_released = True
        series.save()
        serializer = self.get_serializer(series)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def export_special_needs(self, request, pk=None):
        """Export special needs and refugee candidates for a specific series into an Excel file"""
        from django.http import HttpResponse
        from datetime import date
        from django.db.models import Q
        import openpyxl
        from openpyxl.styles import Font, PatternFill
        from candidates.models import CandidateEnrollment

        series = self.get_object()

        # Find candidates enrolled in this series who are either refugees or have a disability
        # Use select_related to optimize the queries
        enrollments = CandidateEnrollment.objects.filter(
            assessment_series=series,
            is_active=True
        ).filter(
            Q(candidate__has_disability=True) | Q(candidate__is_refugee=True)
        ).select_related(
            'candidate',
            'candidate__assessment_center',
            'candidate__occupation',
            'candidate__occupation__sector',
            'candidate__district',
            'candidate__nature_of_disability',
            'occupation_level'
        )

        wb = openpyxl.Workbook()
        
        # --- Sheet 1: Special Needs Candidates ---
        ws_special = wb.active
        ws_special.title = "Special Needs Candidates"
        
        special_headers = [
            ('Reg No', 20), ('Full Name', 25), ('Center', 30), ('Category', 12), 
            ('Occupation', 20), ('Sector', 15), ('Level/Modules', 20),
            ('Nature of Disability', 25), ('Disability Notes', 30),
            ('Age', 6), ('District', 15), ('Gender', 8), ('Contact', 15)
        ]
        
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        
        for col, (header, width) in enumerate(special_headers, 1):
            cell = ws_special.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            ws_special.column_dimensions[cell.column_letter].width = width

        # --- Sheet 2: Refugees ---
        ws_refugees = wb.create_sheet(title="Refugees")
        
        refugee_headers = [
            ('Reg No', 20), ('Full Name', 25), ('Center', 30), ('Category', 12), 
            ('Occupation', 20), ('Sector', 15), ('Level/Modules', 20),
            ('Refugee ID', 20), ('Nationality', 15),
            ('Age', 6), ('District', 15), ('Gender', 8), ('Contact', 15)
        ]
        
        for col, (header, width) in enumerate(refugee_headers, 1):
            cell = ws_refugees.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            ws_refugees.column_dimensions[cell.column_letter].width = width
            
        category_map = {'modular': 'Modular', 'formal': 'Formal', 'workers_pas': "Worker's PAS"}
        gender_map = {'male': 'Male', 'female': 'Female', 'other': 'Other'}
        
        def calc_age(dob):
            if not dob:
                return ''
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        special_row = 2
        refugee_row = 2

        # Filter enrollments into the two lists
        # A candidate might be both and will appear on both sheets
        for enrollment in enrollments:
            c = enrollment.candidate
            
            # Formatting level/modules
            level_modules = ''
            if c.registration_category in ['formal', 'workers_pas'] and enrollment.occupation_level:
                level_modules = enrollment.occupation_level.level_name
            elif c.registration_category in ['modular', 'workers_pas']:
                modules = enrollment.modules.all()
                if modules:
                    level_modules = ', '.join([m.module.module_code for m in modules])
                elif c.registration_category == 'workers_pas':
                    papers = enrollment.papers.all()
                    if papers:
                        level_modules = ', '.join([p.paper.paper_code for p in papers])

            if c.has_disability:
                ws_special.cell(row=special_row, column=1, value=c.registration_number or '')
                ws_special.cell(row=special_row, column=2, value=c.full_name or '')
                ws_special.cell(row=special_row, column=3, value=c.assessment_center.center_name if c.assessment_center else '')
                ws_special.cell(row=special_row, column=4, value=category_map.get(c.registration_category, ''))
                ws_special.cell(row=special_row, column=5, value=c.occupation.occ_name if c.occupation else '')
                ws_special.cell(row=special_row, column=6, value=c.occupation.sector.name if c.occupation and c.occupation.sector else '')
                ws_special.cell(row=special_row, column=7, value=level_modules)
                ws_special.cell(row=special_row, column=8, value=c.nature_of_disability.name if c.nature_of_disability else '')
                ws_special.cell(row=special_row, column=9, value=c.disability_specification or '')
                ws_special.cell(row=special_row, column=10, value=calc_age(c.date_of_birth))
                ws_special.cell(row=special_row, column=11, value=c.district.name if c.district else '')
                ws_special.cell(row=special_row, column=12, value=gender_map.get(c.gender, ''))
                ws_special.cell(row=special_row, column=13, value=c.contact or '')
                special_row += 1
                
            if c.is_refugee:
                ws_refugees.cell(row=refugee_row, column=1, value=c.registration_number or '')
                ws_refugees.cell(row=refugee_row, column=2, value=c.full_name or '')
                ws_refugees.cell(row=refugee_row, column=3, value=c.assessment_center.center_name if c.assessment_center else '')
                ws_refugees.cell(row=refugee_row, column=4, value=category_map.get(c.registration_category, ''))
                ws_refugees.cell(row=refugee_row, column=5, value=c.occupation.occ_name if c.occupation else '')
                ws_refugees.cell(row=refugee_row, column=6, value=c.occupation.sector.name if c.occupation and c.occupation.sector else '')
                ws_refugees.cell(row=refugee_row, column=7, value=level_modules)
                ws_refugees.cell(row=refugee_row, column=8, value=c.refugee_number or '')
                ws_refugees.cell(row=refugee_row, column=9, value=c.nationality or 'Uganda')
                ws_refugees.cell(row=refugee_row, column=10, value=calc_age(c.date_of_birth))
                ws_refugees.cell(row=refugee_row, column=11, value=c.district.name if c.district else '')
                ws_refugees.cell(row=refugee_row, column=12, value=gender_map.get(c.gender, ''))
                ws_refugees.cell(row=refugee_row, column=13, value=c.contact or '')
                refugee_row += 1

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        safe_series_name = str(series.name).replace(" ", "_").lower()
        response['Content-Disposition'] = f'attachment; filename=special_needs_refugees_{safe_series_name}_{date.today().strftime("%Y%m%d")}.xlsx'
        wb.save(response)
        
        return response
