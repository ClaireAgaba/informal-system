"""
Excel Export functionality for assessment series statistics
"""
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
from datetime import datetime

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from assessment_series.models import AssessmentSeries


def create_formatted_excel(series, overview, category_stats, sector_stats, occupation_stats, grade_dist):
    """
    Create a formatted Excel workbook with assessment series statistics
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Series Results"
    
    # Define styles
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    subheader_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    subheader_font = Font(bold=True, size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_alignment = Alignment(horizontal='center', vertical='center')
    
    current_row = 1
    
    # Title
    ws.merge_cells(f'A{current_row}:K{current_row}')
    title_cell = ws[f'A{current_row}']
    title_cell.value = f"Assessment Series Results: {series.name}"
    title_cell.font = Font(bold=True, size=16, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    title_cell.alignment = center_alignment
    current_row += 1
    
    # Series Info
    ws[f'A{current_row}'] = "Series Period:"
    ws[f'B{current_row}'] = f"{series.start_date} to {series.end_date}"
    current_row += 2
    
    # Overview Section
    ws.merge_cells(f'A{current_row}:K{current_row}')
    overview_header = ws[f'A{current_row}']
    overview_header.value = "OVERVIEW STATISTICS"
    overview_header.font = header_font
    overview_header.fill = header_fill
    overview_header.alignment = center_alignment
    current_row += 1
    
    # Overview headers
    overview_headers = ['Metric', 'Total', 'Male', 'Female', 'Male Passed', 'Female Passed',  'Total Passed', 'Male Pass %', 'Female Pass %', 'Overall Pass %']
    for col_num, header in enumerate(overview_headers, 1):
        cell = ws.cell(row=current_row, column=col_num)
        cell.value = header
        cell.font = subheader_font
        cell.fill = subheader_fill
        cell.alignment = center_alignment
        cell.border = border
    current_row += 1
    
    # Overview data
    ws[f'A{current_row}'] = "All Candidates"
    ws[f'B{current_row}'] = overview['total_candidates']
    ws[f'C{current_row}'] = overview['male']
    ws[f'D{current_row}'] = overview['female']
    ws[f'E{current_row}'] = "-"
    ws[f'F{current_row}'] = "-"
    ws[f'G{current_row}'] = "-"
    ws[f'H{current_row}'] = f"{overview['male_pass_rate']}%"
    ws[f'I{current_row}'] = f"{overview['female_pass_rate']}%"
    ws[f'J{current_row}'] = f"{overview['pass_rate']}%"
    
    for col in range(1, 11):
        ws.cell(row=current_row, column=col).border = border
    current_row += 3
    
    # Performance by Category
    ws.merge_cells(f'A{current_row}:K{current_row}')
    cat_header = ws[f'A{current_row}']
    cat_header.value = "PERFORMANCE BY REGISTRATION CATEGORY"
    cat_header.font = header_font
    cat_header.fill = header_fill
    cat_header.alignment = center_alignment
    current_row += 1
    
    # Category headers
    cat_headers = ['Category', 'Total', 'Male', 'Female', 'Male Passed', 'Female Passed',
                   'Total Passed', 'Male Pass %', 'Female Pass %', 'Overall Pass %']
    for col_num, header in enumerate(cat_headers, 1):
        cell = ws.cell(row=current_row, column=col_num)
        cell.value = header
        cell.font = subheader_font
        cell.fill = subheader_fill
        cell.alignment = center_alignment
        cell.border = border
    current_row += 1
    
    # Category data
    category_names = {
        'modular': 'Modular',
        'formal': 'Formal',
        'workers_pas': "Worker's PAS"
    }
    for cat_key, cat_data in category_stats.items():
        ws[f'A{current_row}'] = category_names.get(cat_key, cat_key)
        ws[f'B{current_row}'] = cat_data['total']
        ws[f'C{current_row}'] = cat_data['male']
        ws[f'D{current_row}'] = cat_data['female']
        ws[f'E{current_row}'] = cat_data['male_passed']
        ws[f'F{current_row}'] = cat_data['female_passed']
        ws[f'G{current_row}'] = cat_data['total_passed']
        ws[f'H{current_row}'] = f"{cat_data['male_pass_rate']}%"
        ws[f'I{current_row}'] = f"{cat_data['female_pass_rate']}%"
        ws[f'J{current_row}'] = f"{cat_data['pass_rate']}%"
        
        for col in range(1, 11):
            ws.cell(row=current_row, column=col).border = border
        current_row += 1
    current_row += 2
    
    # Performance by Sector
    if sector_stats:
        ws.merge_cells(f'A{current_row}:K{current_row}')
        sector_header = ws[f'A{current_row}']
        sector_header.value = "PERFORMANCE BY SECTOR"
        sector_header.font = header_font
        sector_header.fill = header_fill
        sector_header.alignment = center_alignment
        current_row += 1
        
        # Sector headers
        sector_headers = ['Sector', 'Total', 'Male', 'Female', 'Male Passed', 'Female Passed',
                         'Total Passed', 'Male Pass %', 'Female Pass %', 'Overall Pass %']
        for col_num, header in enumerate(sector_headers, 1):
            cell = ws.cell(row=current_row, column=col_num)
            cell.value = header
            cell.font = subheader_font
            cell.fill = subheader_fill
            cell.alignment = center_alignment
            cell.border = border
        current_row += 1
        
        # Sector data
        for sector in sector_stats:
            ws[f'A{current_row}'] = sector['sector_name']
            ws[f'B{current_row}'] = sector['total']
            ws[f'C{current_row}'] = sector['male']
            ws[f'D{current_row}'] = sector['female']
            ws[f'E{current_row}'] = sector['male_passed']
            ws[f'F{current_row}'] = sector['female_passed']
            ws[f'G{current_row}'] = sector['total_passed']
            ws[f'H{current_row}'] = f"{sector['male_pass_rate']}%"
            ws[f'I{current_row}'] = f"{sector['female_pass_rate']}%"
            ws[f'J{current_row}'] = f"{sector['pass_rate']}%"
            
            for col in range(1, 11):
                ws.cell(row=current_row, column=col).border = border
            current_row += 1
        current_row += 2
    
    # Performance by Occupation
    if occupation_stats:
        ws.merge_cells(f'A{current_row}:K{current_row}')
        occ_header = ws[f'A{current_row}']
        occ_header.value = "PERFORMANCE BY OCCUPATION"
        occ_header.font = header_font
        occ_header.fill = header_fill
        occ_header.alignment = center_alignment
        current_row += 1
        
        # Occupation headers
        occ_headers = ['Occupation', 'Code', 'Total', 'Male', 'Female', 'Male Passed', 'Female Passed',
                      'Total Passed', 'Male Pass %', 'Female Pass %', 'Overall Pass %']
        for col_num, header in enumerate(occ_headers, 1):
            cell = ws.cell(row=current_row, column=col_num)
            cell.value = header
            cell.font = subheader_font
            cell.fill = subheader_fill
            cell.alignment = center_alignment
            cell.border = border
        current_row += 1
        
        # Occupation data
        for occ in occupation_stats:
            ws[f'A{current_row}'] = occ['occupation_name']
            ws[f'B{current_row}'] = occ['occupation_code']
            ws[f'C{current_row}'] = occ['total']
            ws[f'D{current_row}'] = occ['male']
            ws[f'E{current_row}'] = occ['female']
            ws[f'F{current_row}'] = occ['male_passed']
            ws[f'G{current_row}'] = occ['female_passed']
            ws[f'H{current_row}'] = occ['total_passed']
            ws[f'I{current_row}'] = f"{occ['male_pass_rate']}%"
            ws[f'J{current_row}'] = f"{occ['female_pass_rate']}%"
            ws[f'K{current_row}'] = f"{occ['pass_rate']}%"
            
            for col in range(1, 12):
                ws.cell(row=current_row, column=col).border = border
            current_row += 1
    
    # Auto-size columns
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    return wb


@api_view(['GET'])
@permission_classes([AllowAny])
def export_series_excel(request, series_id):
    """
    Export assessment series statistics to Excel file
    """
    try:
        # Import necessary models and functions
        from results.models import ModularResult, FormalResult, WorkersPasResult
        from occupations.models import Occupation, Sector
        from django.db.models import Count
        
        series = AssessmentSeries.objects.get(id=series_id)
        
        # Get all results for this series
        all_results = list(ModularResult.objects.filter(assessment_series=series).select_related('candidate')) + \
                      list(FormalResult.objects.filter(assessment_series=series).select_related('candidate')) + \
                      list(WorkersPasResult.objects.filter(assessment_series=series).select_related('candidate'))
        
        # Calculate overview statistics
        male_count = sum(1 for r in all_results if r.candidate.gender == 'male')
        female_count = sum(1 for r in all_results if r.candidate.gender == 'female')
        
        # Count passing results by gender
        male_passed = sum(1 for r in all_results if r.candidate.gender == 'male' and (
            (isinstance(r, ModularResult) and r.mark >= 65) or
            (isinstance(r, FormalResult) and ((r.type == 'theory' and r.mark >= 50) or (r.type == 'practical' and r.mark >= 65))) or
            (isinstance(r, WorkersPasResult) and r.mark >= 65)
        ))
        
        female_passed = sum(1 for r in all_results if r.candidate.gender == 'female' and (
            (isinstance(r, ModularResult) and r.mark >= 65) or
            (isinstance(r, FormalResult) and ((r.type == 'theory' and r.mark >= 50) or (r.type == 'practical' and r.mark >= 65))) or
            (isinstance(r, WorkersPasResult) and r.mark >= 65)
        ))
        
        total_candidates = len(all_results)
        total_passed = male_passed + female_passed
        
        overview = {
            'total_candidates':total_candidates,
            'male': male_count,
            'female': female_count,
            'male_pass_rate': round((male_passed / male_count * 100), 2) if male_count > 0 else 0,
            'female_pass_rate': round((female_passed / female_count * 100), 2) if female_count > 0 else 0,
            'pass_rate': round((total_passed / total_candidates * 100), 2) if total_candidates > 0 else 0
        }
        
        # Get category stats by re-filtering the results
        category_stats = {}
        
        # Modular
        modular_results = [r for r in all_results if isinstance(r, ModularResult)]
        modular_male = [r for r in modular_results if r.candidate.gender == 'male']
        modular_female = [r for r in modular_results if r.candidate.gender == 'female']
        category_stats['modular'] = {
            'total': len(modular_results),
            'male': len(modular_male),
            'female': len(modular_female),
            'male_passed': sum(1 for r in modular_male if r.mark >= 65),
            'female_passed': sum(1 for r in modular_female if r.mark >= 65),
            'total_passed': sum(1 for r in modular_results if r.mark >= 65),
            'male_pass_rate': round((sum(1 for r in modular_male if r.mark >= 65) / len(modular_male) * 100), 2) if len(modular_male) > 0 else 0,
            'female_pass_rate': round((sum(1 for r in modular_female if r.mark >= 65) / len(modular_female) * 100), 2) if len(modular_female) > 0 else 0,
            'pass_rate': round((sum(1 for r in modular_results if r.mark >= 65) / len(modular_results) * 100), 2) if len(modular_results) > 0 else 0
        }
        
        # Formal
        formal_results = [r for r in all_results if isinstance(r, FormalResult)]
        formal_male = [r for r in formal_results if r.candidate.gender == 'male']
        formal_female = [r for r in formal_results if r.candidate.gender == 'female']
        formal_male_passed = sum(1 for r in formal_male if ((r.type == 'theory' and r.mark >= 50) or (r.type == 'practical' and r.mark >= 65)))
        formal_female_passed = sum(1 for r in formal_female if ((r.type == 'theory' and r.mark >= 50) or (r.type == 'practical' and r.mark >= 65)))
        formal_total_passed = formal_male_passed + formal_female_passed
        
        category_stats['formal'] = {
            'total': len(formal_results),
            'male': len(formal_male),
            'female': len(formal_female),
            'male_passed': formal_male_passed,
            'female_passed': formal_female_passed,
            'total_passed': formal_total_passed,
            'male_pass_rate': round((formal_male_passed / len(formal_male) * 100), 2) if len(formal_male) > 0 else 0,
            'female_pass_rate': round((formal_female_passed / len(formal_female) * 100), 2) if len(formal_female) > 0 else 0,
            'pass_rate': round((formal_total_passed / len(formal_results) * 100), 2) if len(formal_results) > 0 else 0
        }
        
        # Worker's PAS
        workers_results = [r for r in all_results if isinstance(r, WorkersPasResult)]
        workers_male = [r for r in workers_results if r.candidate.gender == 'male']
        workers_female = [r for r in workers_results if r.candidate.gender == 'female']
        category_stats['workers_pas'] = {
            'total': len(workers_results),
            'male': len(workers_male),
            'female': len(workers_female),
            'male_passed': sum(1 for r in workers_male if r.mark >= 65),
            'female_passed': sum(1 for r in workers_female if r.mark >= 65),
            'total_passed': sum(1 for r in workers_results if r.mark >= 65),
            'male_pass_rate': round((sum(1 for r in workers_male if r.mark >= 65) / len(workers_male) * 100), 2) if len(workers_male) > 0 else 0,
            'female_pass_rate': round((sum(1 for r in workers_female if r.mark >= 65) / len(workers_female) * 100), 2) if len(workers_female) > 0 else 0,
            'pass_rate': round((sum(1 for r in workers_results if r.mark >= 65) / len(workers_results) * 100), 2) if len(workers_results) > 0 else 0
        }
        
        # Sector stats (simplified - get unique sectors from results)
        sector_stats = []
        sectors = Sector.objects.all()
        for sector in sectors:
            sector_occs = Occupation.objects.filter(sector=sector)
            sector_results = [r for r in all_results if 
                             (hasattr(r, 'module') and r.module and r.module.occupation in sector_occs) or
                             (hasattr(r, 'candidate') and r.candidate.occupation in sector_occs)]
            
            if not sector_results:
                continue
                
            sector_male = [r for r in sector_results if r.candidate.gender == 'male']
            sector_female = [r for r in sector_results if r.candidate.gender == 'female']
            
            sector_male_passed = sum(1 for r in sector_male if (
                (isinstance(r, ModularResult) and r.mark >= 65) or
                (isinstance(r, FormalResult) and ((r.type == 'theory' and r.mark >= 50) or (r.type == 'practical' and r.mark >= 65))) or
                (isinstance(r, WorkersPasResult) and r.mark >= 65)
            ))
            
            sector_female_passed = sum(1 for r in sector_female if (
                (isinstance(r, ModularResult) and r.mark >= 65) or
                (isinstance(r, FormalResult) and ((r.type == 'theory' and r.mark >= 50) or (r.type == 'practical' and r.mark >= 65))) or
                (isinstance(r, WorkersPasResult) and r.mark >= 65)
            ))
            
            sector_total_passed = sector_male_passed + sector_female_passed
            
            sector_stats.append({
                'sector_name': sector.name,
                'total': len(sector_results),
                'male': len(sector_male),
                'female': len(sector_female),
                'male_passed': sector_male_passed,
                'female_passed': sector_female_passed,
                'total_passed': sector_total_passed,
                'male_pass_rate': round((sector_male_passed / len(sector_male) * 100), 2) if len(sector_male) > 0 else 0,
                'female_pass_rate': round((sector_female_passed / len(sector_female) * 100), 2) if len(sector_female) > 0 else 0,
                'pass_rate': round((sector_total_passed / len(sector_results) * 100), 2) if len(sector_results) > 0 else 0
            })
        
        # Occupation stats - simplified
        occupation_stats = []
        occupation_ids = set()
        for result in all_results:
            if hasattr(result, 'module') and result.module:
                occupation_ids.add(result.module.occupation_id)
            elif hasattr(result, 'candidate') and result.candidate and result.candidate.occupation:
                occupation_ids.add(result.candidate.occupation_id)
        
        occupations = Occupation.objects.filter(id__in=occupation_ids)
        for occ in occupations:
            occ_results = [r for r in all_results if 
                          (hasattr(r, 'module') and r.module and r.module.occupation == occ) or
                          (hasattr(r, 'candidate') and r.candidate.occupation == occ)]
            
            if not occ_results:
                continue
                
            occ_male = [r for r in occ_results if r.candidate.gender == 'male']
            occ_female = [r for r in occ_results if r.candidate.gender == 'female']
            
            occ_male_passed = sum(1 for r in occ_male if (
                (isinstance(r, ModularResult) and r.mark >= 65) or
                (isinstance(r, FormalResult) and ((r.type == 'theory' and r.mark >= 50) or (r.type == 'practical' and r.mark >= 65))) or
                (isinstance(r, WorkersPasResult) and r.mark >= 65)
            ))
            
            occ_female_passed = sum(1 for r in occ_female if (
                (isinstance(r, ModularResult) and r.mark >= 65) or
                (isinstance(r, FormalResult) and ((r.type == 'theory' and r.mark >= 50) or (r.type == 'practical' and r.mark >= 65))) or
                (isinstance(r, WorkersPasResult) and r.mark >= 65)
            ))
            
            occ_total_passed = occ_male_passed + occ_female_passed
            
            occupation_stats.append({
                'occupation_name': occ.occ_name,
                'occupation_code': occ.occ_code,
                'total': len(occ_results),
                'male': len(occ_male),
                'female': len(occ_female),
                'male_passed': occ_male_passed,
                'female_passed': occ_female_passed,
                'total_passed': occ_total_passed,
                'male_pass_rate': round((occ_male_passed / len(occ_male) * 100), 2) if len(occ_male) > 0 else 0,
                'female_pass_rate': round((occ_female_passed / len(occ_female) * 100), 2) if len(occ_female) > 0 else 0,
                'pass_rate': round((occ_total_passed / len(occ_results) * 100), 2) if len(occ_results) > 0 else 0
            })
        
        # Create Excel workbook
        wb = create_formatted_excel(
            series=series,
            overview=overview,
            category_stats=category_stats,
            sector_stats=sector_stats,
            occupation_stats=occupation_stats,
            grade_dist={}
        )
        
        # Save to BytesIO
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        # Create response
        response = HttpResponse(
            excel_file.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"Series_Results_{series.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except AssessmentSeries.DoesNotExist:
        return Response({'error': 'Series not found'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)


def create_special_needs_excel(special_needs_overview, disability_breakdown, special_needs_sector, 
                                refugee_overview, refugee_sector, series_filter=None):
    """
    Create a formatted Excel workbook for special needs statistics
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Special Needs Analytics"
    
    # Define styles
    header_fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    subheader_fill = PatternFill(start_color="F2DCDB", end_color="F2DCDB", fill_type="solid")
    subheader_font = Font(bold=True, size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_alignment = Alignment(horizontal='center', vertical='center')
    
    current_row = 1
    
    # Title
    ws.merge_cells(f'A{current_row}:K{current_row}')
    title_cell = ws[f'A{current_row}']
    title_cell.value = "Special Needs Candidates Analytics"
    title_cell.font = Font(bold=True, size=16, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
    title_cell.alignment = center_alignment
    current_row += 1
    
    # Filter info
    if series_filter:
        ws[f'A{current_row}'] = f"Filtered by: {series_filter}"
        current_row += 1
    else:
        ws[f'A{current_row}'] = "Showing: All Assessment Series"
        current_row += 1
    current_row += 1
    
    # Overview Section
    ws.merge_cells(f'A{current_row}:K{current_row}')
    overview_header = ws[f'A{current_row}']
    overview_header.value = "OVERALL STATISTICS"
    overview_header.font = header_font
    overview_header.fill = header_fill
    overview_header.alignment = center_alignment
    current_row += 1
    
    # Overview headers
    overview_headers = ['Metric', 'Total', 'Male', 'Female', 'Male Passed', 'Female Passed', 
                        'Total Passed', 'Male Pass %', 'Female Pass %', 'Overall Pass %']
    for col_num, header in enumerate(overview_headers, 1):
        cell = ws.cell(row=current_row, column=col_num)
        cell.value = header
        cell.font = subheader_font
        cell.fill = subheader_fill
        cell.alignment = center_alignment
        cell.border = border
    current_row += 1
    
    # Overview data
    ws[f'A{current_row}'] = "Special Needs Candidates"
    ws[f'B{current_row}'] = special_needs_overview['total']
    ws[f'C{current_row}'] = special_needs_overview['male']
    ws[f'D{current_row}'] = special_needs_overview['female']
    ws[f'E{current_row}'] = special_needs_overview['male_passed']
    ws[f'F{current_row}'] = special_needs_overview['female_passed']
    ws[f'G{current_row}'] = special_needs_overview['total_passed']
    ws[f'H{current_row}'] = f"{special_needs_overview['male_pass_rate']}%"
    ws[f'I{current_row}'] = f"{special_needs_overview['female_pass_rate']}%"
    ws[f'J{current_row}'] = f"{special_needs_overview['pass_rate']}%"
    
    for col in range(1, 11):
        ws.cell(row=current_row, column=col).border = border
    current_row += 3
    
    # Performance by Disability Type
    if disability_breakdown:
        ws.merge_cells(f'A{current_row}:K{current_row}')
        dis_header = ws[f'A{current_row}']
        dis_header.value = "PERFORMANCE BY DISABILITY TYPE"
        dis_header.font = header_font
        dis_header.fill = header_fill
        dis_header.alignment = center_alignment
        current_row += 1
        
        # Disability headers
        dis_headers = ['Disability Type', 'Total', 'Male', 'Female', 'Male Passed', 'Female Passed',
                       'Total Passed', 'Male Pass %', 'Female Pass %', 'Overall Pass %']
        for col_num, header in enumerate(dis_headers, 1):
            cell = ws.cell(row=current_row, column=col_num)
            cell.value = header
            cell.font = subheader_font
            cell.fill = subheader_fill
            cell.alignment = center_alignment
            cell.border = border
        current_row += 1
        
        # Disability data
        for disability in disability_breakdown:
            ws[f'A{current_row}'] = disability['name']
            ws[f'B{current_row}'] = disability['total']
            ws[f'C{current_row}'] = disability['male']
            ws[f'D{current_row}'] = disability['female']
            ws[f'E{current_row}'] = disability['male_passed']
            ws[f'F{current_row}'] = disability['female_passed']
            ws[f'G{current_row}'] = disability['total_passed']
            ws[f'H{current_row}'] = f"{disability['male_pass_rate']}%"
            ws[f'I{current_row}'] = f"{disability['female_pass_rate']}%"
            ws[f'J{current_row}'] = f"{disability['pass_rate']}%"
            
            for col in range(1, 11):
                ws.cell(row=current_row, column=col).border = border
            current_row += 1
        current_row += 2
    
    # Performance by Sector - Special Needs
    if special_needs_sector:
        ws.merge_cells(f'A{current_row}:K{current_row}')
        sector_header = ws[f'A{current_row}']
        sector_header.value = "PERFORMANCE BY SECTOR"
        sector_header.font = header_font
        sector_header.fill = header_fill
        sector_header.alignment = center_alignment
        current_row += 1
        
        # Sector headers
        sector_headers = ['Sector Name', 'Total', 'Male', 'Female', 'Male Passed', 'Female Passed',
                         'Total Passed', 'Male Pass %', 'Female Pass %', 'Overall Pass %']
        for col_num, header in enumerate(sector_headers, 1):
            cell = ws.cell(row=current_row, column=col_num)
            cell.value = header
            cell.font = subheader_font
            cell.fill = subheader_fill
            cell.alignment = center_alignment
            cell.border = border
        current_row += 1
        
        # Sector data
        for sector in special_needs_sector:
            ws[f'A{current_row}'] = sector['sector_name']
            ws[f'B{current_row}'] = sector['total']
            ws[f'C{current_row}'] = sector['male']
            ws[f'D{current_row}'] = sector['female']
            ws[f'E{current_row}'] = sector['male_passed']
            ws[f'F{current_row}'] = sector['female_passed']
            ws[f'G{current_row}'] = sector['total_passed']
            ws[f'H{current_row}'] = f"{sector['male_pass_rate']}%"
            ws[f'I{current_row}'] = f"{sector['female_pass_rate']}%"
            ws[f'J{current_row}'] = f"{sector['pass_rate']}%"
            
            for col in range(1, 11):
                ws.cell(row=current_row, column=col).border = border
            current_row += 1
    
    # REFUGEE STATISTICS SECTION
    current_row += 2
    
    # Refugee Overview
    ws.merge_cells(f'A{current_row}:K{current_row}')
    refugee_header = ws[f'A{current_row}']
    refugee_header.value = "REFUGEE CANDIDATES"
    refugee_header.font = header_font
    refugee_header.fill = header_fill
    refugee_header.alignment = center_alignment
    current_row += 1
    
    # Refugee overview headers (reuse same format)
    for col_num, header in enumerate(overview_headers, 1):
        cell = ws.cell(row=current_row, column=col_num)
        cell.value = header
        cell.font = subheader_font
        cell.fill = subheader_fill
        cell.alignment = center_alignment
        cell.border = border
    current_row += 1
    
    # Refugee overview data
    ws[f'A{current_row}'] = "Refugee Candidates"
    ws[f'B{current_row}'] = refugee_overview['total']
    ws[f'C{current_row}'] = refugee_overview['male']
    ws[f'D{current_row}'] = refugee_overview['female']
    ws[f'E{current_row}'] = refugee_overview['male_passed']
    ws[f'F{current_row}'] = refugee_overview['female_passed']
    ws[f'G{current_row}'] = refugee_overview['total_passed']
    ws[f'H{current_row}'] = f"{refugee_overview['male_pass_rate']}%"
    ws[f'I{current_row}'] = f"{refugee_overview['female_pass_rate']}%"
    ws[f'J{current_row}'] = f"{refugee_overview['pass_rate']}%"
    
    for col in range(1, 11):
        ws.cell(row=current_row, column=col).border = border
    current_row += 3
    
    # Performance by Sector - Refugee
    if refugee_sector:
        ws.merge_cells(f'A{current_row}:K{current_row}')
        sector_header = ws[f'A{current_row}']
        sector_header.value = "REFUGEE PERFORMANCE BY SECTOR"
        sector_header.font = header_font
        sector_header.fill = header_fill
        sector_header.alignment = center_alignment
        current_row += 1
        
        # Sector headers
        sector_headers = ['Sector Name', 'Total', 'Male', 'Female', 'Male Passed', 'Female Passed',
                         'Total Passed', 'Male Pass %', 'Female Pass %', 'Overall Pass %']
        for col_num, header in enumerate(sector_headers, 1):
            cell = ws.cell(row=current_row, column=col_num)
            cell.value = header
            cell.font = subheader_font
            cell.fill = subheader_fill
            cell.alignment = center_alignment
            cell.border = border
        current_row += 1
        
        # Refugee sector data
        for sector in refugee_sector:
            ws[f'A{current_row}'] = sector['sector_name']
            ws[f'B{current_row}'] = sector['total']
            ws[f'C{current_row}'] = sector['male']
            ws[f'D{current_row}'] = sector['female']
            ws[f'E{current_row}'] = sector['male_passed']
            ws[f'F{current_row}'] = sector['female_passed']
            ws[f'G{current_row}'] = sector['total_passed']
            ws[f'H{current_row}'] = f"{sector['male_pass_rate']}%"
            ws[f'I{current_row}'] = f"{sector['female_pass_rate']}%"
            ws[f'J{current_row}'] = f"{sector['pass_rate']}%"
            
            for col in range(1, 11):
                ws.cell(row=current_row, column=col).border = border
            current_row += 1
    
    # Auto-size columns
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    return wb


@api_view(['GET'])
@permission_classes([AllowAny])
def export_special_needs_excel(request):
    """
    Export special needs statistics to Excel file
    """
    try:
        # We need to recreate the logic from special_needs_analytics to avoid request type issues
        from results.models import ModularResult, FormalResult, WorkersPasResult
        from configurations.models import NatureOfDisability
        
        series_id = request.query_params.get('series_id')
        
        # Get all results (optionally filtered by series)
        if series_id:
            all_results = list(ModularResult.objects.filter(assessment_series_id=series_id).select_related('candidate', 'candidate__nature_of_disability')) + \
                          list(FormalResult.objects.filter(assessment_series_id=series_id).select_related('candidate', 'candidate__nature_of_disability')) + \
                          list(WorkersPasResult.objects.filter(assessment_series_id=series_id).select_related('candidate', 'candidate__nature_of_disability'))
            series = AssessmentSeries.objects.get(id=series_id)
            series_filter = series.name
        else:
            all_results = list(ModularResult.objects.all().select_related('candidate', 'candidate__nature_of_disability')) + \
                          list(FormalResult.objects.all().select_related('candidate', 'candidate__nature_of_disability')) + \
                          list(WorkersPasResult.objects.all().select_related('candidate', 'candidate__nature_of_disability'))
            series_filter = None
        
        # Filter to only special needs candidates
        special_needs_results = [r for r in all_results if r.candidate.has_disability]
        
        # Calculate overview
        special_needs_male = [r for r in special_needs_results if r.candidate.gender == 'male']
        special_needs_female = [r for r in special_needs_results if r.candidate.gender == 'female']
        
        def is_passed(result):
            # Skip results without marks
            if result.mark is None:
                return False
                
            if isinstance(result, ModularResult):
                return result.mark >= 65
            elif isinstance(result, FormalResult):
                return (result.type == 'theory' and result.mark >= 50) or (result.type == 'practical' and result.mark >= 65)
            elif isinstance(result, WorkersPasResult):
                return result.mark >= 65
            return False
        
        male_passed = sum(1 for r in special_needs_male if is_passed(r))
        female_passed = sum(1 for r in special_needs_female if is_passed(r))
        total_passed = male_passed + female_passed
        
        overview = {
            'total': len(special_needs_results),
            'male': len(special_needs_male),
            'female': len(special_needs_female),
            'male_passed': male_passed,
            'female_passed': female_passed,
            'total_passed': total_passed,
            'male_pass_rate': round((male_passed / len(special_needs_male) * 100), 2) if len(special_needs_male) > 0 else 0,
            'female_pass_rate': round((female_passed / len(special_needs_female) * 100), 2) if len(special_needs_female) > 0 else 0,
            'pass_rate': round((total_passed / len(special_needs_results) * 100), 2) if len(special_needs_results) > 0 else 0
        }
        
        # By disability type
        disability_breakdown = []
        for disability in NatureOfDisability.objects.all():
            disability_results = [r for r in special_needs_results if r.candidate.nature_of_disability == disability]
            
            if not disability_results:
                continue
            
            dis_male = [r for r in disability_results if r.candidate.gender == 'male']
            dis_female = [r for r in disability_results if r.candidate.gender == 'female']
            
            dis_male_passed = sum(1 for r in dis_male if is_passed(r))
            dis_female_passed = sum(1 for r in dis_female if is_passed(r))
            dis_total_passed = dis_male_passed + dis_female_passed
            
            disability_breakdown.append({
                'name': disability.name,
                'total': len(disability_results),
                'male': len(dis_male),
                'female': len(dis_female),
                'male_passed': dis_male_passed,
                'female_passed': dis_female_passed,
                'total_passed': dis_total_passed,
                'male_pass_rate': round((dis_male_passed / len(dis_male) * 100), 2) if len(dis_male) > 0 else 0,
                'female_pass_rate': round((dis_female_passed / len(dis_female) * 100), 2) if len(dis_female) > 0 else 0,
                'pass_rate': round((dis_total_passed / len(disability_results) * 100), 2) if len(disability_results) > 0 else 0
            })
        
        # By sector
        from occupations.models import Sector
        sector_breakdown = []
        for sector in Sector.objects.all():
            sector_results = [r for r in special_needs_results if 
                             r.candidate.occupation and r.candidate.occupation.sector == sector]
            
            if not sector_results:
                continue
            
            sector_male = [r for r in sector_results if r.candidate.gender == 'male']
            sector_female = [r for r in sector_results if r.candidate.gender == 'female']
            
            sector_male_passed = sum(1 for r in sector_male if is_passed(r))
            sector_female_passed = sum(1 for r in sector_female if is_passed(r))
            sector_total_passed = sector_male_passed + sector_female_passed
            
            sector_breakdown.append({
                'sector_name': sector.name,
                'total': len(sector_results),
                'male': len(sector_male),
                'female': len(sector_female),
                'male_passed': sector_male_passed,
                'female_passed': sector_female_passed,
                'total_passed': sector_total_passed,
                'male_pass_rate': round((sector_male_passed / len(sector_male) * 100), 2) if len(sector_male) > 0 else 0,
                'female_pass_rate': round((sector_female_passed / len(sector_female) * 100), 2) if len(sector_female) > 0 else 0,
                'pass_rate': round((sector_total_passed / len(sector_results) * 100), 2) if len(sector_results) > 0 else 0
            })
        
        # REFUGEE STATISTICS
        refugee_results = [r for r in all_results if r.candidate.is_refugee]
        refugee_male = [r for r in refugee_results if r.candidate.gender == 'male']
        refugee_female = [r for r in refugee_results if r.candidate.gender == 'female']
        
        refugee_male_passed = sum(1 for r in refugee_male if is_passed(r))
        refugee_female_passed = sum(1 for r in refugee_female if is_passed(r))
        refugee_total_passed = refugee_male_passed + refugee_female_passed
        
        refugee_overview = {
            'total': len(refugee_results),
            'male': len(refugee_male),
            'female': len(refugee_female),
            'male_passed': refugee_male_passed,
            'female_passed': refugee_female_passed,
            'total_passed': refugee_total_passed,
            'male_pass_rate': round((refugee_male_passed / len(refugee_male) * 100), 2) if len(refugee_male) > 0 else 0,
            'female_pass_rate': round((refugee_female_passed / len(refugee_female) * 100), 2) if len(refugee_female) > 0 else 0,
            'pass_rate': round((refugee_total_passed / len(refugee_results) * 100), 2) if len(refugee_results) > 0 else 0
        }
        
        # Refugee by sector
        refugee_sector = []
        for sector in Sector.objects.all():
            sector_results = [r for r in refugee_results if 
                             r.candidate.occupation and r.candidate.occupation.sector == sector]
            
            if not sector_results:
                continue
            
            sector_male = [r for r in sector_results if r.candidate.gender == 'male']
            sector_female = [r for r in sector_results if r.candidate.gender == 'female']
            
            sector_male_passed = sum(1 for r in sector_male if is_passed(r))
            sector_female_passed = sum(1 for r in sector_female if is_passed(r))
            sector_total_passed = sector_male_passed + sector_female_passed
            
            refugee_sector.append({
                'sector_name': sector.name,
                'total': len(sector_results),
                'male': len(sector_male),
                'female': len(sector_female),
                'male_passed': sector_male_passed,
                'female_passed': sector_female_passed,
                'total_passed': sector_total_passed,
                'male_pass_rate': round((sector_male_passed / len(sector_male) * 100), 2) if len(sector_male) > 0 else 0,
                'female_pass_rate': round((sector_female_passed / len(sector_female) * 100), 2) if len(sector_female) > 0 else 0,
                'pass_rate': round((sector_total_passed / len(sector_results) * 100), 2) if len(sector_results) > 0 else 0
            })
        
        # Create Excel workbook with both special needs and refugee data
        wb = create_special_needs_excel(
            special_needs_overview=overview,
            disability_breakdown=disability_breakdown,
            special_needs_sector=sector_breakdown,
            refugee_overview=refugee_overview,
            refugee_sector=refugee_sector,
            series_filter=series_filter
        )
        
        # Save to BytesIO
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        # Create response
        response = HttpResponse(
            excel_file.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"Special_Needs_Analytics_{datetime.now().strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except AssessmentSeries.DoesNotExist:
        return Response({'error': 'Series not found'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)
