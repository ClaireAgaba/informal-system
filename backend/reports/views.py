from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Q
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image as PILImage
import os
from django.conf import settings

from candidates.models import Candidate
from assessment_centers.models import AssessmentCenter
from assessment_series.models import AssessmentSeries
from occupations.models import Occupation


class ReportViewSet(viewsets.ViewSet):
    """
    ViewSet for generating various reports
    """
    permission_classes = [permissions.AllowAny]  # Allow unauthenticated access

    def _get_center_for_rep(self, request):
        """Helper method to get assessment center for center representative"""
        if request.user.is_authenticated and request.user.user_type == 'center_representative':
            if hasattr(request.user, 'center_rep_profile'):
                return request.user.center_rep_profile.assessment_center
        return None

    def _get_branch_for_rep(self, request):
        """Helper method to get branch for center representative"""
        if request.user.is_authenticated and request.user.user_type == 'center_representative':
            if hasattr(request.user, 'center_rep_profile'):
                return request.user.center_rep_profile.assessment_center_branch
        return None

    @action(detail=False, methods=['get'], url_path='candidate-album')
    def candidate_album(self, request):
        """
        Generate candidate album PDF with photos
        Query params: assessment_center, assessment_series, registration_category, occupation, level (optional for formal/workers_pas)
        """
        # Get query parameters
        assessment_center_id = request.query_params.get('assessment_center')
        assessment_series_id = request.query_params.get('assessment_series')
        registration_category = request.query_params.get('registration_category')
        occupation_id = request.query_params.get('occupation')
        level_id = request.query_params.get('level')  # Optional, required for formal/workers_pas
        branch_id = request.query_params.get('branch')

        # Check if user is center representative and restrict to their center
        rep_center = self._get_center_for_rep(request)
        if rep_center:
            assessment_center_id = str(rep_center.id)

        rep_branch = self._get_branch_for_rep(request)
        if rep_branch:
            branch_id = str(rep_branch.id)

        # Validate required parameters
        if not all([assessment_center_id, assessment_series_id, registration_category, occupation_id]):
            return Response(
                {'error': 'Missing required parameters: assessment_center, assessment_series, registration_category, occupation'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate level for formal only (workers_pas can have null level)
        if registration_category == 'formal' and not level_id:
            return Response(
                {'error': 'Level is required for formal category'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            assessment_center = AssessmentCenter.objects.get(id=assessment_center_id)
            assessment_series = AssessmentSeries.objects.get(id=assessment_series_id)
            occupation = Occupation.objects.get(id=occupation_id)
            
            branch = None
            if branch_id:
                from assessment_centers.models import CenterBranch
                branch = CenterBranch.objects.get(id=branch_id)
            
            # Get level if provided
            from occupations.models import OccupationLevel
            level = None
            if level_id:
                level = OccupationLevel.objects.get(id=level_id)
        except (AssessmentCenter.DoesNotExist, AssessmentSeries.DoesNotExist, Occupation.DoesNotExist) as e:
            return Response(
                {'error': f'Invalid parameter: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filter candidates
        # Filter candidates based on enrollment in the assessment series
        # consistently for all registration categories
        
        # Base filter for candidates
        filter_params = {
            'assessment_center': assessment_center,
            'registration_category': registration_category,
            'occupation': occupation,
            'is_submitted': True,
            'verification_status': 'verified',
            'enrollments__assessment_series': assessment_series,
            'enrollments__is_active': True
        }
        
        if branch:
            filter_params['assessment_center_branch'] = branch
        
        # Additional filtering based on level if provided
        if level:
            if registration_category == 'workers_pas':
                # Workers PAS: filter by level OR null level (they can select papers from any level)
                # But since we are filtering candidates, we need to use Q objects for the enrollment check
                # However, since we already have enrollments__assessment_series in filter_params,
                # we need to be careful not to conflict or double-filter incorrectly.
                
                # Let's construct the queryset directly to be safe and clear
                candidates = Candidate.objects.filter(
                    assessment_center=assessment_center,
                    registration_category=registration_category,
                    occupation=occupation,
                    is_submitted=True,
                    verification_status='verified',
                    enrollments__assessment_series=assessment_series,
                    enrollments__is_active=True
                ).filter(
                    Q(enrollments__occupation_level=level) | Q(enrollments__occupation_level__isnull=True)
                )
            else:
                # Formal/Modular with level: strict level matching
                filter_params['enrollments__occupation_level'] = level
                candidates = Candidate.objects.filter(**filter_params)
        else:
            # Workers PAS or Modular without specific level (if applicable)
            # Just use the base params which include assessment series
            candidates = Candidate.objects.filter(**filter_params)
            
        # Ensure distinct results since we're filtering across relationships
        candidates = candidates.distinct().select_related(
            'occupation', 'assessment_center', 'assessment_center_branch'
        ).order_by('registration_number')
            

        
        # Debug: Print filter params and candidate count
        print(f"DEBUG: Filter params: {filter_params}")
        print(f"DEBUG: Found {candidates.count()} candidates")
        
        # Debug: Check each candidate individually if we have enrolled IDs but no matches
        if 'id__in' in filter_params and filter_params['id__in'] and candidates.count() == 0:
            print("DEBUG: Checking why enrolled candidates don't match...")
            for cand_id in filter_params['id__in']:
                cand = Candidate.objects.filter(id=cand_id).first()
                if cand:
                    print(f"  Candidate {cand_id}: center={cand.assessment_center_id}, reg_cat={cand.registration_category}, occ={cand.occupation_id}, submitted={cand.is_submitted}, verified={cand.verification_status}")
                    print(f"  Expected: center={assessment_center.id}, reg_cat={registration_category}, occ={occupation.id}, submitted=True, verified='verified'")

        # Check if there are any candidates
        if not candidates.exists():
            # Provide more detailed error message
            error_msg = f'No verified candidates found for {occupation.occ_name}'
            if level:
                error_msg += f' at {level.level_name}'
            error_msg += f' in {assessment_center.center_name} for {assessment_series.name}. '
            error_msg += 'Please ensure candidates are verified and enrolled in the selected level.'
            
            return Response(
                {'error': error_msg},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            title=f"Candidate Album - {assessment_series.name}"
        )

        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#000000'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#000000'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#000000'),
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )

        # Add header with logo
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
        
        # Group candidates by branch
        grouped_candidates = {}
        if assessment_center.has_branches:
            for cand in candidates:
                cand_branch = cand.assessment_center_branch
                if cand_branch not in grouped_candidates:
                    grouped_candidates[cand_branch] = []
                grouped_candidates[cand_branch].append(cand)
        else:
            grouped_candidates[None] = list(candidates)

        first_page = True
        
        # Sort branches gracefully (putting None first if any)
        sorted_branches = sorted(list(grouped_candidates.keys()), key=lambda b: b.branch_code if b else '')

        for branch_key in sorted_branches:
            branch_candidates = grouped_candidates[branch_key]
            
            if not branch_candidates:
                continue
                
            if not first_page:
                elements.append(PageBreak())
            first_page = False
            
            # Header table with logo and contact info
            header_data = []
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=1.2*inch, height=1.2*inch)
                header_data = [[
                    Paragraph("P.O.Box 1499<br/>Email: info@uvtab.go.ug", info_style),
                    logo,
                    Paragraph("Tel: +256392002468", info_style)
                ]]
            else:
                header_data = [[
                    Paragraph("P.O.Box 1499<br/>Email: info@uvtab.go.ug", info_style),
                    '',
                    Paragraph("Tel: +256392002468", info_style)
                ]]

            header_table = Table(header_data, colWidths=[3*inch, 3*inch, 3*inch])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 0.2*inch))

            # Title
            elements.append(Paragraph("UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD", title_style))
            elements.append(Spacer(1, 0.1*inch))

            # Subtitle
            elements.append(Paragraph(f"Registered Candidates for {assessment_series.name}", subtitle_style))
            elements.append(Spacer(1, 0.05*inch))

            # Assessment center info
            elements.append(Paragraph(
                f"Assessment Center: {assessment_center.center_number} - {assessment_center.center_name}",
                subtitle_style
            ))
            elements.append(Spacer(1, 0.1*inch))
            
            # Branch info if applicable
            if branch_key:
                branch_label = f"Branch: {branch_key.branch_code} - {branch_key.branch_name}"
                
                # Check if district exists on branch and add it
                if hasattr(branch_key, 'district') and branch_key.district:
                    branch_label += f" - {branch_key.district.name}"
                    
                elements.append(Paragraph(
                    branch_label,
                    subtitle_style
                ))
                elements.append(Spacer(1, 0.1*inch))

            # Occupation details
            reg_category_display = dict(Candidate.REGISTRATION_CATEGORY_CHOICES).get(registration_category, registration_category)
            elements.append(Paragraph(f"Occupation Name: {occupation.occ_name}", info_style))
            elements.append(Paragraph(f"Occupation Code: {occupation.occ_code}", info_style))
            elements.append(Paragraph(f"Registration Category: {reg_category_display}", info_style))
            
            # Add level info for formal/workers_pas
            if level:
                elements.append(Paragraph(f"Level: {level.level_name}", info_style))
                
            elements.append(Spacer(1, 0.2*inch))

            # Prepare table data - add ENROLLMENT column for Workers PAS
            if registration_category == 'workers_pas':
                table_data = [['S/N', 'PHOTO', 'FULL NAME', 'GENDER', 'OCCUPATION', 'REG TYPE', 'ENROLLMENT', 'SPECIAL NEEDS', 'SIGNATURE']]
            else:
                table_data = [['S/N', 'PHOTO', 'FULL NAME', 'GENDER', 'OCCUPATION', 'REG TYPE', 'SPECIAL NEEDS', 'SIGNATURE']]

            for idx, candidate in enumerate(branch_candidates, start=1):
                # Handle photo and registration number
                photo_cell = ''
                reg_no_text = candidate.registration_number or 'NO REG NO'
                reg_no_paragraph = Paragraph(reg_no_text, ParagraphStyle('SmallReg', fontSize=8, alignment=TA_CENTER, leading=10))
                
                if candidate.passport_photo:
                    try:
                        photo_path = candidate.passport_photo.path
                        if os.path.exists(photo_path):
                            # Open image with PIL to handle EXIF orientation
                            pil_img = PILImage.open(photo_path)
                            
                            # Auto-rotate based on EXIF orientation
                            try:
                                from PIL import ImageOps
                                pil_img = ImageOps.exif_transpose(pil_img)
                            except Exception:
                                pass  # If EXIF handling fails, use image as-is
                            
                            # Save to temporary buffer
                            from io import BytesIO as ImgBuffer
                            img_buffer = ImgBuffer()
                            pil_img.save(img_buffer, format='JPEG')
                            img_buffer.seek(0)
                            
                            # Create ReportLab image from buffer
                            img = Image(img_buffer, width=0.8*inch, height=1*inch)
                            
                            # Combine photo and reg no
                            photo_cell = [img, Spacer(1, 0.05*inch), reg_no_paragraph]
                        else:
                            photo_cell = [Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER)), Spacer(1, 0.05*inch), reg_no_paragraph]
                    except Exception as e:
                        photo_cell = [Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER)), Spacer(1, 0.05*inch), reg_no_paragraph]
                else:
                    photo_cell = [Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER)), Spacer(1, 0.05*inch), reg_no_paragraph]

                # Special needs
                special_needs = "No"
                if candidate.has_disability and candidate.nature_of_disability:
                    special_needs = candidate.nature_of_disability.name if hasattr(candidate.nature_of_disability, 'name') else "Yes"

                # For Workers PAS, get enrollment info (papers from different levels)
                enrollment_info = ''
                if registration_category == 'workers_pas':
                    from candidates.models import CandidateEnrollment, EnrollmentPaper
                    # Get the candidate's enrollment for this series
                    enrollment = CandidateEnrollment.objects.filter(
                        candidate=candidate,
                        assessment_series=assessment_series
                    ).first()
                    
                    if enrollment:
                        # Get all enrolled papers with their module and level info
                        enrolled_papers = EnrollmentPaper.objects.filter(
                            enrollment=enrollment
                        ).select_related('paper', 'paper__module', 'paper__module__level').order_by('paper__module__level__level_name')
                        
                        # Group by level
                        level_info = {}
                        for ep in enrolled_papers:
                            if ep.paper and ep.paper.module and ep.paper.module.level:
                                level_name = ep.paper.module.level.level_name
                                paper_code = ep.paper.paper_code
                                if level_name not in level_info:
                                    level_info[level_name] = []
                                level_info[level_name].append(paper_code)
                        
                        # Format as "Level 1 (HDWp01, HDWp03), Level 2 (HDWp05)"
                        enrollment_parts = []
                        for level_name, papers in level_info.items():
                            enrollment_parts.append(f"{level_name} ({', '.join(papers)})")
                        enrollment_info = ', '.join(enrollment_parts)

                # Build row based on category
                if registration_category == 'workers_pas':
                    # Wrap enrollment info in Paragraph for proper text wrapping
                    enrollment_cell = Paragraph(
                        enrollment_info or 'N/A',
                        ParagraphStyle('EnrollmentStyle', fontSize=7, leading=9, alignment=TA_LEFT)
                    )
                    
                    row = [
                        str(idx),
                        photo_cell,
                        candidate.full_name or '',
                        candidate.gender.capitalize() if candidate.gender else '',
                        occupation.occ_name,
                        reg_category_display,
                        enrollment_cell,
                        special_needs,
                        ''  # Signature column left blank
                    ]
                else:
                    row = [
                        str(idx),
                        photo_cell,
                        candidate.full_name or '',
                        candidate.gender.capitalize() if candidate.gender else '',
                        occupation.occ_name,
                        reg_category_display,
                        special_needs,
                        ''  # Signature column left blank
                    ]
                table_data.append(row)

            # Create table with appropriate column widths
            if registration_category == 'workers_pas':
                # S/N, PHOTO(+REG NO), FULL NAME, GENDER, OCCUPATION, REG TYPE, ENROLLMENT, SPECIAL NEEDS, SIGNATURE
                col_widths = [0.3*inch, 1.4*inch, 1.8*inch, 0.6*inch, 1.1*inch, 0.85*inch, 1.8*inch, 0.9*inch, 0.85*inch]
            else:
                # S/N, PHOTO(+REG NO), FULL NAME, GENDER, OCCUPATION, REG TYPE, SPECIAL NEEDS, SIGNATURE
                col_widths = [0.4*inch, 1.8*inch, 2.2*inch, 0.8*inch, 1.5*inch, 1.2*inch, 1.2*inch, 1*inch]
            
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                
                # Body styling
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # S/N center
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Photo center
                ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Gender center
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 1), (-1, -1), 4),
                ('RIGHTPADDING', (0, 1), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
            ]))

            elements.append(table)

        # Add page number footer with total pages
        def add_page_number(canvas, doc):
            page_num = canvas.getPageNumber()
            total_pages = doc.page
            text = f"Page {page_num} of {total_pages}"
            canvas.saveState()
            canvas.setFont('Helvetica', 9)
            canvas.drawCentredString(landscape(A4)[0] / 2, 0.3*inch, text)
            canvas.restoreState()

        # Build PDF with two passes to get total page count
        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

        # Get PDF from buffer
        pdf = buffer.getvalue()
        buffer.close()

        # Create filename
        clean_series_name = assessment_series.name.strip().replace(' ', '_')
        filename = f"candidate_album_{assessment_center.center_number}_{occupation.occ_code}_{clean_series_name}.pdf"

        # Return PDF response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=False, methods=['get'], url_path='result-list')
    def result_list(self, request):
        """
        Generate result list PDF for modular candidates
        Grouped by assessment center and module with page breaks
        """
        # Get query parameters
        assessment_series_id = request.query_params.get('assessment_series')
        registration_category = request.query_params.get('registration_category')
        occupation_id = request.query_params.get('occupation')
        assessment_center_id = request.query_params.get('assessment_center')  # Optional
        
        # Check if user is center representative and restrict to their center
        rep_center = self._get_center_for_rep(request)
        if rep_center:
            assessment_center_id = str(rep_center.id)
        
        # Validate required parameters
        if not all([assessment_series_id, registration_category, occupation_id]):
            return Response(
                {'error': 'Missing required parameters: assessment_series, registration_category, occupation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assessment_series = AssessmentSeries.objects.get(id=assessment_series_id)
            occupation = Occupation.objects.get(id=occupation_id)
            
            # Get assessment center if specified
            assessment_center = None
            if assessment_center_id:
                assessment_center = AssessmentCenter.objects.get(id=assessment_center_id)
        except (AssessmentSeries.DoesNotExist, Occupation.DoesNotExist, AssessmentCenter.DoesNotExist) as e:
            return Response(
                {'error': f'Invalid parameter: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # For modular, get results grouped by center and module
        if registration_category == 'modular':
            from results.models import ModularResult
            
            # Build filter for results
            result_filter = {
                'assessment_series': assessment_series,
                'module__occupation': occupation,
                'status__in': ['normal', 'special']  # Include normal and special results
            }
            
            # If specific center, filter by it
            if assessment_center:
                result_filter['candidate__assessment_center'] = assessment_center
            
            # Get all results
            results = ModularResult.objects.filter(**result_filter).select_related(
                'candidate', 'candidate__assessment_center', 'module'
            ).order_by(
                'candidate__assessment_center__center_number',
                'module__module_code',
                'candidate__registration_number'
            )
            
            if not results.exists():
                return Response(
                    {'error': f'No results found for {occupation.occ_name} in {assessment_series.name}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Group results by center and module
            grouped_results = {}
            for result in results:
                center = result.candidate.assessment_center
                module = result.module
                
                if center not in grouped_results:
                    grouped_results[center] = {}
                if module not in grouped_results[center]:
                    grouped_results[center][module] = []
                
                grouped_results[center][module].append(result)
            
            # Generate PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=0.5*inch, bottomMargin=0.5*inch)
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=11,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            info_style = ParagraphStyle(
                'InfoStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=4,
                fontName='Helvetica'
            )
            
            # Iterate through centers and modules
            first_page = True
            for center, modules in grouped_results.items():
                for module, module_results in modules.items():
                    # Add page break between sections (except first)
                    if not first_page:
                        elements.append(PageBreak())
                    first_page = False
                    
                    # Header with logo (note: filename is uvtab-logo.png with hyphen)
                    logo_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
                    if not os.path.exists(logo_path):
                        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
                    
                    if os.path.exists(logo_path):
                        logo = Image(logo_path, width=0.8*inch, height=0.8*inch)
                    else:
                        logo = ''
                    
                    # Header table with contact info and logo
                    header_data = [
                            [
                                Paragraph("P.O.Box 1499<br/>Email: info@uvtab.go.ug", info_style),
                                logo,
                                Paragraph("Tel: +256392002468", info_style)
                            ]]

                    header_table = Table(header_data, colWidths=[3*inch, 3*inch, 3*inch])
                    header_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    elements.append(header_table)
                    elements.append(Spacer(1, 0.2*inch))
                    
                    # Title
                    elements.append(Paragraph("UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD", title_style))
                    elements.append(Paragraph("PROVISIONAL ASSESSMENT RESULTS FOR", subtitle_style))
                    elements.append(Paragraph(f"ASSESSMENT PERIOD: {assessment_series.name}", subtitle_style))
                    elements.append(Spacer(1, 0.1*inch))
                    
                    # Category, Occupation, Center, Module info
                    reg_category_display = dict(Candidate.REGISTRATION_CATEGORY_CHOICES).get(registration_category, registration_category)
                    elements.append(Paragraph(f"Category: {reg_category_display}", info_style))
                    elements.append(Paragraph(f"Occupation: {occupation.occ_name}", info_style))
                    elements.append(Paragraph(f"Assessment Center: {center.center_name}", info_style))
                    elements.append(Paragraph(f"Module: {module.module_name} ({module.module_code})", info_style))
                    elements.append(Spacer(1, 0.2*inch))
                    
                    # Table data
                    table_data = [['S/N', 'Photo', 'Reg No', 'Name', 'Gender', 'Practical', 'Comment']]
                    
                    for idx, result in enumerate(module_results, start=1):
                        candidate = result.candidate
                        
                        # Handle photo
                        photo_cell = ''
                        if candidate.passport_photo:
                            try:
                                photo_path = candidate.passport_photo.path
                                if os.path.exists(photo_path):
                                    # Open image with PIL to handle EXIF orientation
                                    pil_img = PILImage.open(photo_path)
                                    
                                    # Auto-rotate based on EXIF orientation
                                    try:
                                        from PIL import ImageOps
                                        pil_img = ImageOps.exif_transpose(pil_img)
                                    except Exception:
                                        pass
                                    
                                    # Save to temporary buffer
                                    from io import BytesIO as ImgBuffer
                                    img_buffer = ImgBuffer()
                                    pil_img.save(img_buffer, format='JPEG')
                                    img_buffer.seek(0)
                                    
                                    # Create ReportLab image from buffer
                                    img = Image(img_buffer, width=0.6*inch, height=0.75*inch)
                                    photo_cell = img
                                else:
                                    photo_cell = Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER))
                            except Exception as e:
                                photo_cell = Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER))
                        else:
                            photo_cell = Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER))
                        
                        # Grade and comment
                        grade = result.grade or ''
                        comment = result.comment or ''
                        
                        row = [
                            str(idx),
                            photo_cell,
                            candidate.registration_number or '',
                            candidate.full_name or '',
                            candidate.gender.capitalize() if candidate.gender else '',
                            grade,
                            comment
                        ]
                        table_data.append(row)
                    
                    # Create table with landscape-optimized widths
                    col_widths = [0.4*inch, 0.9*inch, 1.5*inch, 2.8*inch, 0.8*inch, 1.2*inch, 2.5*inch]
                    table = Table(table_data, colWidths=col_widths, repeatRows=1)
                    table.setStyle(TableStyle([
                        # Header styling
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 0), (-1, 0), 8),
                        
                        # Body styling
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # S/N center
                        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Photo center
                        ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Gender center
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 1), (-1, -1), 4),
                        ('RIGHTPADDING', (0, 1), (-1, -1), 4),
                        ('TOPPADDING', (0, 1), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                        
                        # Grid
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
                    ]))
                    
                    elements.append(table)
            
            # Build PDF
            doc.build(elements)
            
            # Get PDF from buffer
            pdf = buffer.getvalue()
            buffer.close()
            
            # Create filename
            center_part = f"{assessment_center.center_number}_" if assessment_center else "all_centers_"
            filename = f"result_list_{center_part}{occupation.occ_code}_{assessment_series.name.replace(' ', '_')}.pdf"
            
            # Return PDF response
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        elif registration_category == 'formal':
            from results.models import FormalResult
            from occupations.models import OccupationLevel
            
            # Level is required for formal
            level_id = request.query_params.get('level')
            if not level_id:
                return Response(
                    {'error': 'Level is required for formal category'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                level = OccupationLevel.objects.get(id=level_id)
            except OccupationLevel.DoesNotExist:
                return Response(
                    {'error': 'Invalid level'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Build filter for results
            result_filter = {
                'assessment_series': assessment_series,
                'level': level,
                'level__occupation': occupation,  # Filter by occupation
                'candidate__occupation': occupation,  # Also filter candidate's occupation
                'status__in': ['normal', 'retake']  # Include normal and retake results
            }
            
            # If specific center, filter by it
            if assessment_center:
                result_filter['candidate__assessment_center'] = assessment_center
            
            # Get all results
            results = FormalResult.objects.filter(**result_filter).select_related(
                'candidate', 'candidate__assessment_center', 'exam', 'paper', 'level'
            ).order_by(
                'candidate__assessment_center__center_number',
                'candidate__registration_number',
                'exam__module_code',
                'paper__paper_code'
            )
            
            if not results.exists():
                return Response(
                    {'error': f'No results found for {occupation.occ_name} - {level.level_name} in {assessment_series.name}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Determine if module-based or paper-based
            is_module_based = results.filter(exam__isnull=False).exists()
            is_paper_based = results.filter(paper__isnull=False).exists()
            
            # Group results by center and candidate
            grouped_results = {}
            for result in results:
                center = result.candidate.assessment_center
                candidate = result.candidate
                
                if center not in grouped_results:
                    grouped_results[center] = {}
                if candidate not in grouped_results[center]:
                    grouped_results[center][candidate] = {
                        'theory': {},
                        'practical': {}
                    }
                
                # Store results by type
                # Use module code or paper code as key
                if result.exam:
                    key = result.exam.module_code
                elif result.paper:
                    key = result.paper.paper_code
                else:
                    key = 'default'
                
                # Store in appropriate type bucket
                if result.type == 'theory':
                    grouped_results[center][candidate]['theory'][key] = result
                elif result.type == 'practical':
                    grouped_results[center][candidate]['practical'][key] = result
            
            # Get all unique modules or papers for column headers
            if is_module_based:
                modules = results.filter(exam__isnull=False).values_list('exam__module_code', 'exam__module_name').distinct().order_by('exam__module_code')
                column_items = list(modules)
            else:
                papers = results.filter(paper__isnull=False).values_list('paper__paper_code', 'paper__paper_name').distinct().order_by('paper__paper_code')
                column_items = list(papers)
            
            # Generate PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=0.5*inch, bottomMargin=0.5*inch)
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=11,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            info_style = ParagraphStyle(
                'InfoStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=4,
                fontName='Helvetica'
            )
            
            # Iterate through centers
            first_page = True
            for center, candidates in grouped_results.items():
                # Add page break between centers (except first)
                if not first_page:
                    elements.append(PageBreak())
                first_page = False
                
                # Header with logo (note: filename is uvtab-logo.png with hyphen)
                logo_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
                if not os.path.exists(logo_path):
                    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
                
                if os.path.exists(logo_path):
                    logo = Image(logo_path, width=0.8*inch, height=0.8*inch)
                else:
                    logo = ''
                
                # Header table with contact info and logo
                header_data = [
                        [
                            Paragraph("P.O.Box 1499<br/>Email: info@uvtab.go.ug", info_style),
                            logo,
                            Paragraph("Tel: +256392002468", info_style)
                        ]]

                header_table = Table(header_data, colWidths=[3*inch, 3*inch, 3*inch])
                header_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                    ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(header_table)
                elements.append(Spacer(1, 0.2*inch))
                
                # Title
                elements.append(Paragraph("UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD", title_style))
                elements.append(Paragraph("PROVISIONAL ASSESSMENT RESULTS FOR", subtitle_style))
                elements.append(Paragraph(f"ASSESSMENT PERIOD: {assessment_series.name}", subtitle_style))
                elements.append(Spacer(1, 0.1*inch))
                
                # Category, Occupation, Level, Center info
                reg_category_display = dict(Candidate.REGISTRATION_CATEGORY_CHOICES).get(registration_category, registration_category)
                elements.append(Paragraph(f"Category: {reg_category_display}", info_style))
                elements.append(Paragraph(f"Occupation: {occupation.occ_name}", info_style))
                elements.append(Paragraph(f"Level: {level.level_name}", info_style))
                elements.append(Paragraph(f"Assessment Center: {center.center_name}", info_style))
                elements.append(Spacer(1, 0.2*inch))
                
                # Build table headers - always use simple Theory/Practical columns
                table_headers = ['S/N', 'Photo', 'Reg No', 'Name', 'Gender', 'Theory', 'Practical', 'Comment']
                table_data = [table_headers]
                
                # Build table rows
                for idx, (candidate, results_data) in enumerate(sorted(candidates.items(), key=lambda x: x[0].registration_number), start=1):
                    # Handle photo
                    photo_cell = ''
                    if candidate.passport_photo:
                        try:
                            photo_path = candidate.passport_photo.path
                            if os.path.exists(photo_path):
                                pil_img = PILImage.open(photo_path)
                                try:
                                    from PIL import ImageOps
                                    pil_img = ImageOps.exif_transpose(pil_img)
                                except Exception:
                                    pass
                                
                                from io import BytesIO as ImgBuffer
                                img_buffer = ImgBuffer()
                                pil_img.save(img_buffer, format='JPEG')
                                img_buffer.seek(0)
                                
                                img = Image(img_buffer, width=0.6*inch, height=0.75*inch)
                                photo_cell = img
                            else:
                                photo_cell = Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER))
                        except Exception:
                            photo_cell = Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER))
                    else:
                        photo_cell = Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER))
                    
                    row = [
                        str(idx),
                        photo_cell,
                        candidate.registration_number or '',
                        candidate.full_name or '',
                        candidate.gender.capitalize() if candidate.gender else '',
                    ]
                    
                    # Get theory and practical results for this candidate
                    theory_result = None
                    practical_result = None
                    
                    if results_data['theory']:
                        theory_result = list(results_data['theory'].values())[0]
                    
                    if results_data['practical']:
                        practical_result = list(results_data['practical'].values())[0]
                    
                    # Debug logging
                    print(f"Candidate: {candidate.full_name}")
                    print(f"Theory results: {results_data['theory']}")
                    print(f"Practical results: {results_data['practical']}")
                    print(f"Theory result: {theory_result}")
                    print(f"Practical result: {practical_result}")
                    
                    # Helper function to check if grade is passing
                    # Pass mark: 50% in theory, 65% in practical
                    def is_passing_grade(grade, grade_type):
                        if not grade:
                            return False
                        grade_upper = grade.upper().strip()
                        
                        if grade_type == 'theory':
                            # Theory failing grades (below 50%): C-, D, E
                            failing_grades = ['C-', 'D', 'E', 'F', 'U', 'FAIL']
                        else:  # practical
                            # Practical failing grades (below 65%): B-, C, C-, D, D-, E
                            failing_grades = ['B-', 'C', 'C-', 'D', 'D-', 'E', 'F', 'U', 'FAIL']
                        
                        return grade_upper not in failing_grades
                    
                    # Theory grade - with color styling if unsuccessful
                    theory_grade = theory_result.grade if theory_result else ''
                    is_theory_pass = is_passing_grade(theory_grade, 'theory')
                    
                    if theory_grade and not is_theory_pass:
                        # Create red text for failing grade
                        theory_cell = Paragraph(
                            f'<font color="red"><b>{theory_grade}</b></font>',
                            ParagraphStyle('FailGrade', fontSize=8, alignment=TA_CENTER)
                        )
                    else:
                        theory_cell = theory_grade or ''
                    
                    row.append(theory_cell)
                    
                    # Practical grade - with color styling if unsuccessful
                    practical_grade = practical_result.grade if practical_result else ''
                    is_practical_pass = is_passing_grade(practical_grade, 'practical')
                    
                    print(f"Theory grade: {theory_grade}, Pass: {is_theory_pass}")
                    print(f"Practical grade: {practical_grade}, Pass: {is_practical_pass}")
                    
                    if practical_grade and not is_practical_pass:
                        # Create red text for failing grade
                        practical_cell = Paragraph(
                            f'<font color="red"><b>{practical_grade}</b></font>',
                            ParagraphStyle('FailGrade', fontSize=8, alignment=TA_CENTER)
                        )
                    else:
                        practical_cell = practical_grade or ''
                    
                    row.append(practical_cell)
                    
                    # Build comment based on individual results
                    comment_parts = []
                    
                    # Check theory status
                    if theory_result:
                        theory_status = 'Successful' if is_theory_pass else 'Not Successful'
                        comment_parts.append(f'{theory_status} (Theory)')
                    
                    # Check practical status
                    if practical_result:
                        practical_status = 'Successful' if is_practical_pass else 'Not Successful'
                        comment_parts.append(f'{practical_status} (Practical)')
                    
                    comment = ', '.join(comment_parts) if comment_parts else ''
                    row.append(comment)
                    
                    table_data.append(row)
                
                # Fixed column widths for consistent layout
                col_widths = [0.4*inch, 0.8*inch, 1.5*inch, 2.5*inch, 0.8*inch, 1.2*inch, 1.2*inch, 2*inch]
                
                # Create table
                table = Table(table_data, colWidths=col_widths, repeatRows=1)
                table.setStyle(TableStyle([
                    # Header styling
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('TOPPADDING', (0, 0), (-1, 0), 6),
                    
                    # Body styling
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # S/N center
                    ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Photo center
                    ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Gender center
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 1), (-1, -1), 3),
                    ('RIGHTPADDING', (0, 1), (-1, -1), 3),
                    ('TOPPADDING', (0, 1), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                    
                    # Grid
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
                ]))
                
                elements.append(table)
            
            # Build PDF
            doc.build(elements)
            
            # Get PDF from buffer
            pdf = buffer.getvalue()
            buffer.close()
            
            # Create filename
            center_part = f"{assessment_center.center_number}_" if assessment_center else "all_centers_"
            filename = f"result_list_{center_part}{occupation.occ_code}_{level.level_name.replace(' ', '_')}_{assessment_series.name.replace(' ', '_')}.pdf"
            
            # Return PDF response
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        elif registration_category == 'workers_pas':
            # Workers PAS Result List
            from results.models import WorkersPasResult
            
            # Get level if provided (optional for workers_pas)
            level = None
            level_id = request.query_params.get('level')
            if level_id:
                try:
                    level = OccupationLevel.objects.get(id=level_id, occupation=occupation)
                except OccupationLevel.DoesNotExist:
                    return Response(
                        {'error': 'Invalid level'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Build filter for results
            result_filter = {
                'assessment_series': assessment_series,
                'candidate__occupation': occupation,
                'status__in': ['normal', 'retake']
            }
            
            # Add level filter if provided
            if level:
                result_filter['level'] = level
            
            # Add center filter if provided
            if assessment_center:
                result_filter['candidate__assessment_center'] = assessment_center
            
            # Get all results
            results = WorkersPasResult.objects.filter(**result_filter).select_related(
                'candidate', 'candidate__assessment_center', 'level', 'module', 'paper'
            ).order_by(
                'candidate__assessment_center__center_number',
                'level__level_name',
                'module__module_code',
                'paper__paper_code',
                'candidate__registration_number'
            )
            
            if not results.exists():
                error_msg = f'No results found for {occupation.occ_name}'
                if level:
                    error_msg += f' - {level.level_name}'
                error_msg += f' in {assessment_series.name}'
                return Response({'error': error_msg}, status=status.HTTP_404_NOT_FOUND)
            
            # Group results by center -> level -> module -> paper -> candidate
            grouped_results = {}
            for result in results:
                center = result.candidate.assessment_center
                level_key = result.level
                module = result.module
                paper = result.paper
                candidate = result.candidate
                
                if center not in grouped_results:
                    grouped_results[center] = {}
                if level_key not in grouped_results[center]:
                    grouped_results[center][level_key] = {}
                if module not in grouped_results[center][level_key]:
                    grouped_results[center][level_key][module] = {}
                if paper not in grouped_results[center][level_key][module]:
                    grouped_results[center][level_key][module][paper] = []
                
                grouped_results[center][level_key][module][paper].append({
                    'candidate': candidate,
                    'result': result
                })
            
            # Generate PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=0.5*inch, bottomMargin=0.5*inch)
            elements = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            info_style = ParagraphStyle(
                'InfoStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=3,
                fontName='Helvetica'
            )
            
            section_style = ParagraphStyle(
                'SectionStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.whitesmoke,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                backColor=colors.HexColor('#4472C4')
            )
            
            # Process each center
            first_page = True
            for center_idx, (center, levels_data) in enumerate(sorted(grouped_results.items(), key=lambda x: x[0].center_number)):
                if center_idx > 0:
                    elements.append(PageBreak())
                    first_page = False
                
                # Header with logo (same format as modular/formal)
                logo_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
                if not os.path.exists(logo_path):
                    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
                
                if os.path.exists(logo_path):
                    logo = Image(logo_path, width=0.8*inch, height=0.8*inch)
                else:
                    logo = ''
                
                # Header table with contact info and logo (matching modular/formal format)
                header_data = [
                    [
                        Paragraph("P.O.Box 1499<br/>Email: info@uvtab.go.ug", info_style),
                        logo,
                        Paragraph("Tel: +256392002468", info_style)
                    ]
                ]
                
                header_table = Table(header_data, colWidths=[3*inch, 3*inch, 3*inch])
                header_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                    ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(header_table)
                elements.append(Spacer(1, 0.2*inch))
                
                # Title
                elements.append(Paragraph("UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD", title_style))
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph("PROVISIONAL ASSESSMENT RESULTS FOR", subtitle_style))
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph(f"ASSESSMENT PERIOD: {assessment_series.name}", subtitle_style))
                elements.append(Spacer(1, 0.2*inch))
                
                # Category, Occupation, Level, Center info
                reg_category_display = dict(Candidate.REGISTRATION_CATEGORY_CHOICES).get(registration_category, registration_category)
                elements.append(Paragraph(f"<b>Category:</b> {reg_category_display}", info_style))
                elements.append(Paragraph(f"<b>Occupation:</b> {occupation.occ_name}", info_style))
                if level:
                    elements.append(Paragraph(f"<b>Level:</b> {level.level_name}", info_style))
                elements.append(Paragraph(f"<b>Assessment Center:</b> {center.center_name}", info_style))
                elements.append(Spacer(1, 0.2*inch))
                
                # Process each level in this center
                for level_key, modules_data in sorted(levels_data.items(), key=lambda x: x[0].level_name if x[0] else ''):
                    # Process each module in this level
                    for module, papers_data in sorted(modules_data.items(), key=lambda x: x[0].module_code):
                        # Process each paper in this module
                        for paper, candidates_data in sorted(papers_data.items(), key=lambda x: x[0].paper_code):
                            # Section header: MODULE - PAPER
                            section_title = f"{module.module_code} - {module.module_name} and {paper.paper_code} - {paper.paper_name}"
                            elements.append(Paragraph(section_title, section_style))
                            elements.append(Spacer(1, 0.1*inch))
                            
                            # Table headers
                            table_headers = ['S/N', 'Photo', 'Reg No', 'Name', 'Gender', 'Level', 'Practical', 'Comment']
                            table_data = [table_headers]
                            
                            # Add candidate rows
                            for idx, item in enumerate(candidates_data, start=1):
                                candidate = item['candidate']
                                result = item['result']
                                
                                # Handle photo
                                photo_cell = ''
                                if candidate.passport_photo:
                                    try:
                                        photo_path = candidate.passport_photo.path
                                        if os.path.exists(photo_path):
                                            pil_img = PILImage.open(photo_path)
                                            try:
                                                from PIL import ImageOps
                                                pil_img = ImageOps.exif_transpose(pil_img)
                                            except Exception:
                                                pass
                                            
                                            from io import BytesIO as ImgBuffer
                                            img_buffer = ImgBuffer()
                                            pil_img.save(img_buffer, format='JPEG')
                                            img_buffer.seek(0)
                                            photo_cell = Image(img_buffer, width=0.6*inch, height=0.6*inch)
                                    except Exception as e:
                                        photo_cell = Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER))
                                else:
                                    photo_cell = Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER))
                                
                                # Determine comment based on grade
                                comment = result.comment if result.comment else 'Successful'
                                
                                row = [
                                    str(idx),
                                    photo_cell,
                                    candidate.registration_number or '',
                                    candidate.full_name or '',
                                    candidate.gender.capitalize() if candidate.gender else '',
                                    level_key.level_name if level_key else '',
                                    result.grade or '',
                                    comment
                                ]
                                
                                table_data.append(row)
                            
                            # Create table
                            col_widths = [0.4*inch, 0.8*inch, 1.5*inch, 2.5*inch, 0.8*inch, 1*inch, 0.8*inch, 1.5*inch]
                            table = Table(table_data, colWidths=col_widths, repeatRows=1)
                            table.setStyle(TableStyle([
                                # Header styling
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 8),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                                
                                # Body styling
                                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # S/N
                                ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Photo
                                ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Gender
                                ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Level
                                ('ALIGN', (6, 1), (6, -1), 'CENTER'),  # Mark
                                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                                ('FONTSIZE', (0, 1), (-1, -1), 8),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
                            ]))
                            
                            elements.append(table)
                            elements.append(Spacer(1, 0.2*inch))
            
            # Build PDF
            doc.build(elements)
            pdf = buffer.getvalue()
            buffer.close()
            
            # Create filename
            center_part = f"{assessment_center.center_number}_" if assessment_center else "all_centers_"
            level_part = f"{level.level_name.replace(' ', '_')}_" if level else "all_levels_"
            filename = f"result_list_{center_part}{occupation.occ_code}_{level_part}{assessment_series.name.replace(' ', '_')}.pdf"
            
            # Return PDF response
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        else:
            return Response(
                {'error': f'Result lists for {registration_category} category not yet implemented'},
                status=status.HTTP_400_BAD_REQUEST
            )
