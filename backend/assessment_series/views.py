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
            ('Reg No', 20), ('Full Name', 25), ('Center No', 15), ('Center Name', 30), ('Center Contact', 15),
            ('Category', 12), ('Occupation', 20), ('Sector', 15), ('Level/Modules', 20),
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
            ('Reg No', 20), ('Full Name', 25), ('Center No', 15), ('Center Name', 30), ('Center Contact', 15),
            ('Category', 12), ('Occupation', 20), ('Sector', 15), ('Level/Modules', 20),
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
                ws_special.cell(row=special_row, column=3, value=c.assessment_center.center_number if c.assessment_center else '')
                ws_special.cell(row=special_row, column=4, value=c.assessment_center.center_name if c.assessment_center else '')
                ws_special.cell(row=special_row, column=5, value=c.assessment_center.contact_1 if c.assessment_center else '')
                ws_special.cell(row=special_row, column=6, value=category_map.get(c.registration_category, ''))
                ws_special.cell(row=special_row, column=7, value=c.occupation.occ_name if c.occupation else '')
                ws_special.cell(row=special_row, column=8, value=c.occupation.sector.name if c.occupation and c.occupation.sector else '')
                ws_special.cell(row=special_row, column=9, value=level_modules)
                ws_special.cell(row=special_row, column=10, value=c.nature_of_disability.name if c.nature_of_disability else '')
                ws_special.cell(row=special_row, column=11, value=c.disability_specification or '')
                ws_special.cell(row=special_row, column=12, value=calc_age(c.date_of_birth))
                ws_special.cell(row=special_row, column=13, value=c.district.name if c.district else '')
                ws_special.cell(row=special_row, column=14, value=gender_map.get(c.gender, ''))
                ws_special.cell(row=special_row, column=15, value=c.contact or '')
                special_row += 1
                
            if c.is_refugee:
                ws_refugees.cell(row=refugee_row, column=1, value=c.registration_number or '')
                ws_refugees.cell(row=refugee_row, column=2, value=c.full_name or '')
                ws_refugees.cell(row=refugee_row, column=3, value=c.assessment_center.center_number if c.assessment_center else '')
                ws_refugees.cell(row=refugee_row, column=4, value=c.assessment_center.center_name if c.assessment_center else '')
                ws_refugees.cell(row=refugee_row, column=5, value=c.assessment_center.contact_1 if c.assessment_center else '')
                ws_refugees.cell(row=refugee_row, column=6, value=category_map.get(c.registration_category, ''))
                ws_refugees.cell(row=refugee_row, column=7, value=c.occupation.occ_name if c.occupation else '')
                ws_refugees.cell(row=refugee_row, column=8, value=c.occupation.sector.name if c.occupation and c.occupation.sector else '')
                ws_refugees.cell(row=refugee_row, column=9, value=level_modules)
                ws_refugees.cell(row=refugee_row, column=10, value=c.refugee_number or '')
                ws_refugees.cell(row=refugee_row, column=11, value=c.nationality or 'Uganda')
                ws_refugees.cell(row=refugee_row, column=12, value=calc_age(c.date_of_birth))
                ws_refugees.cell(row=refugee_row, column=13, value=c.district.name if c.district else '')
                ws_refugees.cell(row=refugee_row, column=14, value=gender_map.get(c.gender, ''))
                ws_refugees.cell(row=refugee_row, column=15, value=c.contact or '')
                refugee_row += 1

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        safe_series_name = str(series.name).replace(" ", "_").lower()
        response['Content-Disposition'] = f'attachment; filename=special_needs_refugees_{safe_series_name}_{date.today().strftime("%Y%m%d")}.xlsx'
        wb.save(response)
        
        return response

    @action(detail=True, methods=['get'])
    def export_registration_summary(self, request, pk=None):
        """Export registration summary by category down to the module level into an Excel file"""
        from django.http import HttpResponse
        from datetime import date
        import openpyxl
        from openpyxl.styles import Font, PatternFill
        from candidates.models import CandidateEnrollment
        from collections import defaultdict

        series = self.get_object()

        # Fetch active enrollments with related fields to optimize querying
        enrollments = CandidateEnrollment.objects.filter(
            assessment_series=series,
            is_active=True
        ).select_related(
            'candidate',
            'candidate__occupation',
            'occupation_level'
        ).prefetch_related(
            'modules__module',
            'papers__paper',
            'occupation_level__modules'
        )

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Registration Summary"

        headers = [
            ('Registration Category', 20),
            ('Occupation Code', 20),
            ('Occupation Name', 30),
            ('Module / Paper Code', 25),
            ('Level', 15),
            ('Candidates', 12)
        ]

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")

        for col, (header, width) in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            ws.column_dimensions[cell.column_letter].width = width

        # Dictionary to store the counts
        # Key: (Category, Occupation Code, Occupation Name, Module Code, Level)
        # Value: Count
        counts = defaultdict(int)

        category_map = {'modular': 'Modular', 'formal': 'Formal', 'workers_pas': "Worker's PAS"}

        for enrollment in enrollments:
            c = enrollment.candidate
            cat = category_map.get(c.registration_category, c.registration_category)
            occ_code = c.occupation.occ_code if c.occupation else 'N/A'
            occ_name = c.occupation.occ_name if c.occupation else 'N/A'

            if c.is_formal() and enrollment.occupation_level:
                level_name = enrollment.occupation_level.level_name
                level_modules = enrollment.occupation_level.modules.all()
                if level_modules:
                    for mod in level_modules:
                        key = (cat, occ_code, occ_name, mod.module_code, level_name)
                        counts[key] += 1
                else:
                    # In case a formal level has no modules explicitly added yet
                    key = (cat, occ_code, occ_name, 'N/A', level_name)
                    counts[key] += 1
            elif c.is_modular():
                level_name = 'N/A'
                modules = enrollment.modules.all()
                if modules:
                    for m in modules:
                        key = (cat, occ_code, occ_name, m.module.module_code, level_name)
                        counts[key] += 1
                else:
                     key = (cat, occ_code, occ_name, 'N/A', level_name)
                     counts[key] += 1
            elif c.is_workers_pas():
                level_name = enrollment.occupation_level.level_name if enrollment.occupation_level else 'N/A'
                papers = enrollment.papers.all()
                modules = enrollment.modules.all()
                
                if not papers and not modules:
                    key = (cat, occ_code, occ_name, 'N/A', level_name)
                    counts[key] += 1
                
                for p in papers:
                    key = (cat, occ_code, occ_name, p.paper.paper_code, level_name)
                    counts[key] += 1
                    
                for m in modules:
                    key = (cat, occ_code, occ_name, m.module.module_code, level_name)
                    counts[key] += 1

        row = 2
        for (cat, occ_code, occ_name, mod_code, level), count in sorted(counts.items()):
            ws.cell(row=row, column=1, value=cat)
            ws.cell(row=row, column=2, value=occ_code)
            ws.cell(row=row, column=3, value=occ_name)
            ws.cell(row=row, column=4, value=mod_code)
            ws.cell(row=row, column=5, value=level)
            ws.cell(row=row, column=6, value=count)
            row += 1

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        safe_series_name = str(series.name).replace(" ", "_").lower()
        response['Content-Disposition'] = f'attachment; filename=registration_summary_{safe_series_name}_{date.today().strftime("%Y%m%d")}.xlsx'
        wb.save(response)
        
        return response
