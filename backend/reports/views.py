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
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
        filter_params = {
            'assessment_center': assessment_center,
            'registration_category': registration_category,
            'occupation': occupation,
            'is_submitted': True,
            'verification_status': 'verified'
        }
        
        # For formal/workers_pas with level, filter through enrollments
        if level:
            # Get candidates enrolled in this level for this assessment series
            from candidates.models import CandidateEnrollment
            
            # For workers_pas, level can be null in enrollment, so we need to handle both cases
            if registration_category == 'workers_pas':
                # Workers PAS: filter by level OR null level (they can select papers from any level)
                enrollments = CandidateEnrollment.objects.filter(
                    assessment_series=assessment_series
                ).filter(
                    Q(occupation_level=level) | Q(occupation_level__isnull=True)
                )
            else:
                # Formal: strict level matching
                enrollments = CandidateEnrollment.objects.filter(
                    assessment_series=assessment_series,
                    occupation_level=level
                )
            
            enrolled_candidate_ids = list(enrollments.values_list('candidate_id', flat=True))
            
            # Debug: Check if we have any enrollments
            level_name = level.level_name if level else "Any"
            print(f"DEBUG: Found {len(enrolled_candidate_ids)} enrollments for level {level_name} in {assessment_series.name}")
            print(f"DEBUG: Enrolled candidate IDs: {enrolled_candidate_ids}")
            
            if enrolled_candidate_ids:
                filter_params['id__in'] = enrolled_candidate_ids
            else:
                # No enrollments found, return empty queryset
                filter_params['id__in'] = []
        elif registration_category == 'workers_pas':
            # Workers PAS without level filter - get all enrolled in this series
            from candidates.models import CandidateEnrollment
            enrollments = CandidateEnrollment.objects.filter(
                assessment_series=assessment_series
            )
            enrolled_candidate_ids = list(enrollments.values_list('candidate_id', flat=True))
            
            print(f"DEBUG: Workers PAS without level - Found {len(enrolled_candidate_ids)} enrollments")
            
            if enrolled_candidate_ids:
                filter_params['id__in'] = enrolled_candidate_ids
            else:
                filter_params['id__in'] = []
            
        candidates = Candidate.objects.filter(**filter_params).select_related(
            'occupation', 'assessment_center'
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
            bottomMargin=0.5*inch
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
            table_data = [['S/N', 'PHOTO', 'REG NO.', 'FULL NAME', 'GENDER', 'OCCUPATION', 'REG TYPE', 'ENROLLMENT', 'SPECIAL NEEDS', 'SIGNATURE']]
        else:
            table_data = [['S/N', 'PHOTO', 'REG NO.', 'FULL NAME', 'GENDER', 'OCCUPATION', 'REG TYPE', 'SPECIAL NEEDS', 'SIGNATURE']]

        for idx, candidate in enumerate(candidates, start=1):
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
                            pass  # If EXIF handling fails, use image as-is
                        
                        # Save to temporary buffer
                        from io import BytesIO as ImgBuffer
                        img_buffer = ImgBuffer()
                        pil_img.save(img_buffer, format='JPEG')
                        img_buffer.seek(0)
                        
                        # Create ReportLab image from buffer
                        img = Image(img_buffer, width=0.8*inch, height=1*inch)
                        photo_cell = img
                    else:
                        photo_cell = Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER))
                except Exception as e:
                    photo_cell = Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER))
            else:
                photo_cell = Paragraph("NO PHOTO", ParagraphStyle('Small', fontSize=6, alignment=TA_CENTER))

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
                    candidate.registration_number or '',
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
                    candidate.registration_number or '',
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
            # S/N, PHOTO, REG NO, FULL NAME, GENDER, OCCUPATION, REG TYPE, ENROLLMENT, SPECIAL NEEDS, SIGNATURE
            col_widths = [0.3*inch, 0.85*inch, 1.3*inch, 1.6*inch, 0.6*inch, 1.1*inch, 0.85*inch, 1.8*inch, 0.9*inch, 0.85*inch]
        else:
            # S/N, PHOTO, REG NO, FULL NAME, GENDER, OCCUPATION, REG TYPE, SPECIAL NEEDS, SIGNATURE
            col_widths = [0.4*inch, 1*inch, 1.5*inch, 2*inch, 0.8*inch, 1.5*inch, 1*inch, 1.2*inch, 1*inch]
        
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
        filename = f"candidate_album_{assessment_center.center_number}_{occupation.occ_code}_{assessment_series.name.replace(' ', '_')}.pdf"

        # Return PDF response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
