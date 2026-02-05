from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import HttpResponse
from .models import ModularResult, WorkersPasResult
from .serializers import WorkersPasResultSerializer, WorkersPasResultCreateUpdateSerializer
from candidates.models import Candidate, EnrollmentModule, EnrollmentPaper, CandidateActivity
from occupations.models import OccupationModule, ModuleLWA, OccupationPaper
from assessment_series.models import AssessmentSeries


def _log_candidate_activity(request, candidate, action, description='', details=None):
    actor = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    CandidateActivity.objects.create(
        candidate=candidate,
        actor=actor,
        action=action,
        description=description or '',
        details=details,
    )


class ModularResultViewSet(viewsets.ViewSet):
    """
    ViewSet for managing modular assessment results
    """
    permission_classes = [AllowAny]  # Temporarily allow all to test
    
    @action(detail=False, methods=['post'], url_path='add')
    def add_results(self, request):
        """Add modular results for a candidate"""
        candidate_id = request.data.get('candidate_id')
        assessment_series_id = request.data.get('assessment_series')
        results_data = request.data.get('results', [])
        
        if not candidate_id:
            return Response(
                {'error': 'Candidate ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not assessment_series_id:
            return Response(
                {'error': 'Assessment series is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not results_data:
            return Response(
                {'error': 'No results data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get candidate
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify candidate is modular
        if candidate.registration_category != 'modular':
            return Response(
                {'error': 'Candidate is not registered for modular assessment'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get assessment series
        try:
            assessment_series = AssessmentSeries.objects.get(id=assessment_series_id)
        except AssessmentSeries.DoesNotExist:
            return Response(
                {'error': 'Assessment series not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        created_results = []
        created_count = 0
        updated_count = 0
        for result_data in results_data:
            module_id = result_data.get('module_id')
            mark = result_data.get('mark')
            result_type = result_data.get('type', 'practical')
            
            # Get the module
            try:
                module = OccupationModule.objects.get(id=module_id)
                
                # Create or update result
                defaults_data = {
                    'mark': mark,
                    'status': 'normal',
                }
                
                # Only set entered_by if user is authenticated
                if request.user and request.user.is_authenticated:
                    defaults_data['entered_by'] = request.user
                
                result, created = ModularResult.objects.update_or_create(
                    candidate=candidate,
                    assessment_series=assessment_series,
                    module=module,
                    type=result_type,
                    defaults=defaults_data
                )
                created_results.append(result)
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except OccupationModule.DoesNotExist:
                return Response(
                    {'error': f'Module with id {module_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {'error': f'Error creating result: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        _log_candidate_activity(
            request,
            candidate,
            'modular_results_saved',
            'Modular results saved',
            details={
                'assessment_series_id': assessment_series.id,
                'assessment_series_name': assessment_series.name,
                'created': created_count,
                'updated': updated_count,
            },
        )

        return Response(
            {
                'message': f'{len(created_results)} results added successfully',
                'count': len(created_results)
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['put'], url_path='update')
    def update_results(self, request):
        """Update existing modular results"""
        candidate_id = request.data.get('candidate_id')
        results_data = request.data.get('results', [])
        
        if not candidate_id:
            return Response(
                {'error': 'Candidate ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not results_data:
            return Response(
                {'error': 'No results data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get candidate
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update results
        updated_count = 0
        for result_data in results_data:
            result_id = result_data.get('result_id')
            mark = result_data.get('mark')
            
            try:
                result = ModularResult.objects.get(id=result_id, candidate=candidate)
                result.mark = mark
                
                # Update entered_by if user is authenticated
                if request.user and request.user.is_authenticated:
                    result.entered_by = request.user
                
                result.save()
                updated_count += 1
            except ModularResult.DoesNotExist:
                return Response(
                    {'error': f'Result with id {result_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {'error': f'Error updating result: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        _log_candidate_activity(
            request,
            candidate,
            'modular_results_updated',
            'Modular results updated',
            details={'updated': updated_count},
        )

        return Response(
            {
                'message': f'{updated_count} results updated successfully',
                'count': updated_count
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='enrollment-modules')
    def enrollment_modules(self, request):
        """Get modules for candidate's enrollments in a specific series"""
        candidate_id = request.query_params.get('candidate_id')
        series_id = request.query_params.get('series_id')
        
        if not candidate_id:
            return Response(
                {'error': 'candidate_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not series_id:
            return Response(
                {'error': 'series_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get candidate
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get enrollments for this candidate and series
        enrollments = candidate.enrollments.filter(assessment_series_id=series_id)
        
        # Get all modules from these enrollments
        enrollment_modules = EnrollmentModule.objects.filter(
            enrollment__in=enrollments
        ).select_related('module')
        
        modules_data = []
        for em in enrollment_modules:
            modules_data.append({
                'id': em.module.id,
                'module_code': em.module.module_code,
                'module_name': em.module.module_name,
            })
        
        return Response(modules_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='verified-pdf')
    def verified_results_pdf(self, request):
        """Generate verified results PDF for candidate"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from io import BytesIO
        from datetime import datetime
        from django.conf import settings
        import os
        
        candidate_id = request.query_params.get('candidate_id')
        
        if not candidate_id:
            return Response(
                {'error': 'candidate_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=20,
            spaceBefore=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.black,
            spaceAfter=10,
            spaceBefore=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Title at top
        elements.append(Paragraph("UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD", title_style))
        elements.append(Spacer(1, 0.15*inch))
        
        # Header with logo and contact info
        header_data = []
        
        # Try to add logo
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
        logo = None
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=0.7*inch, height=0.7*inch)
            except:
                logo = None
        
        if logo:
            header_data = [[
                Paragraph("Plot 7, Valley Drive, Ntinda-Kyambogo<br/>Road<br/>Email: info@uvtab.go.ug", 
                         ParagraphStyle('small', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT)),
                logo,
                Paragraph("P.O.Box 1499, Kampala,<br/>Tel: +256392002468", 
                         ParagraphStyle('small', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT))
            ]]
        else:
            header_data = [[
                Paragraph("Plot 7, Valley Drive, Ntinda-Kyambogo Road<br/>Email: info@uvtab.go.ug", 
                         ParagraphStyle('small', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT)),
                "",
                Paragraph("P.O.Box 1499, Kampala,<br/>Tel: +256392002468", 
                         ParagraphStyle('small', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT))
            ]]
        
        header_table = Table(header_data, colWidths=[2.3*inch, 2.4*inch, 2.3*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Title
        elements.append(Paragraph("VERIFICATION OF RESULTS", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("TO WHOM IT MAY CONCERN", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Intro text
        intro_style = ParagraphStyle('Intro', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Oblique')
        elements.append(Paragraph(
            "This is to verify that this candidate registered and sat for UVTAB assessments with the following particulars and obtained the following",
            intro_style
        ))
        elements.append(Spacer(1, 0.3*inch))
        
        # Candidate info with photo
        # Try to get candidate photo
        candidate_photo = None
        if candidate.passport_photo:
            photo_path = os.path.join(settings.MEDIA_ROOT, str(candidate.passport_photo))
            if os.path.exists(photo_path):
                try:
                    from PIL import Image as PILImage
                    
                    # Open image with PIL to handle rotation
                    pil_image = PILImage.open(photo_path)
                    
                    # Handle EXIF orientation
                    try:
                        from PIL import ImageOps
                        pil_image = ImageOps.exif_transpose(pil_image)
                    except:
                        pass
                    
                    # Save corrected image to temporary buffer
                    img_buffer = BytesIO()
                    pil_image.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    # Create ReportLab image from buffer
                    candidate_photo = Image(img_buffer, width=1.2*inch, height=1.5*inch)
                except Exception as e:
                    print(f"Error loading photo: {e}")
                    candidate_photo = None
        
        # Build info data - single block layout like reference
        info_data = [
            ["NAME:", candidate.full_name or "", "NATIONALITY:", candidate.nationality or "Uganda"],
            ["REG NO:", candidate.registration_number or "", "BIRTHDATE:", candidate.date_of_birth.strftime("%d %b, %Y") if candidate.date_of_birth else ""],
            ["GENDER:", candidate.gender.capitalize() if candidate.gender else "", "PRINTDATE:", datetime.now().strftime("%d-%b-%Y")],
            ["CENTER NAME:", candidate.assessment_center.center_name if candidate.assessment_center else "", "", ""],
            ["CATEGORY:", candidate.get_registration_category_display() if candidate.registration_category else "", "", ""],
            ["OCCUPATION:", candidate.occupation.occ_name if candidate.occupation else "", "", ""],
        ]
        
        # Create info table
        info_table = Table(info_data, colWidths=[1.15*inch, 1.85*inch, 1.15*inch, 1.35*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (0, -1), 5),
            ('RIGHTPADDING', (1, 0), (1, -1), 10),
            ('RIGHTPADDING', (2, 0), (2, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        # Combine photo and info table
        if candidate_photo:
            combined_data = [[candidate_photo, info_table]]
            combined_table = Table(combined_data, colWidths=[1.3*inch, 6.5*inch])
            combined_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (0, -1), 10),
            ]))
            elements.append(combined_table)
        else:
            elements.append(info_table)
        
        elements.append(Spacer(1, 0.4*inch))
        
        # Results section
        elements.append(Paragraph("ASSESSMENT RESULTS", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Check if candidate is formal
        is_formal = candidate.registration_category == 'formal'
        
        if is_formal:
            # Get formal results
            from results.models import FormalResult
            formal_results = FormalResult.objects.filter(candidate=candidate).select_related(
                'exam', 'exam__level', 'paper', 'paper__level', 'assessment_series'
            )
            
            if formal_results.exists():
                # Determine if module-based or paper-based
                first_result = formal_results.first()
                is_paper_based = first_result.paper is not None
                
                if is_paper_based:
                    # Paper-based formal results table (Image 5 format)
                    results_data = [["Paper\nCode", "Paper Name", "Level", "Assessment\nType", "Grade", "Comment"]]
                    for result in formal_results:
                        paper = result.paper
                        results_data.append([
                            paper.paper_code if paper else "",
                            paper.paper_name if paper else "",
                            f"Level {paper.level.level_name}" if paper and paper.level else "",
                            result.get_type_display().capitalize(),
                            result.grade or "-",
                            result.comment or "-"
                        ])
                    
                    results_table = Table(results_data, colWidths=[0.8*inch, 2.5*inch, 1.2*inch, 1.2*inch, 0.8*inch, 1.5*inch])
                else:
                    # Module-based formal results table (Image 4 format - simplified)
                    results_data = [["ASSESSMENT TYPE", "GRADE", "COMMENT"]]
                    for result in formal_results:
                        results_data.append([
                            result.get_type_display().capitalize(),
                            result.grade or "-",
                            result.comment or "-"
                        ])
                    
                    results_table = Table(results_data, colWidths=[3.5*inch, 1.5*inch, 3*inch])
                
                # Common table styling
                results_table.setStyle(TableStyle([
                    # Header row
                    ('BACKGROUND', (0, 0), (-1, 0), colors.black),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    # Data rows
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                    # Borders
                    ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
                    ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.black),
                ]))
                elements.append(results_table)
            else:
                elements.append(Paragraph("No results available", styles['Normal']))
        else:
            # Modular/Workers PAS results
            results = ModularResult.objects.filter(candidate=candidate).select_related('module', 'assessment_series')
            
            if results.exists():
                # Results table - cleaner design
                results_data = [["MODULE NAME", "ASSESSMENT\nTYPE", "GRADE", "COMMENT"]]
                for result in results:
                    results_data.append([
                        result.module.module_name if result.module else "",
                        result.get_type_display().capitalize(),
                        result.grade or "-",
                        result.comment or "-"
                    ])
                
                results_table = Table(results_data, colWidths=[3.5*inch, 1.8*inch, 1.2*inch, 1.5*inch])
                results_table.setStyle(TableStyle([
                    # Header row
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    # Data rows
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                    # Borders
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                    ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ]))
                elements.append(results_table)
            else:
                elements.append(Paragraph("No results available", styles['Normal']))
        
        # Add LWAs section (only for modular candidates, not formal or workers_pas)
        if candidate.registration_category == 'modular':
            elements.append(Spacer(1, 0.3*inch))
            
            # Get LWAs for enrolled modules
            enrollment_modules = EnrollmentModule.objects.filter(
                enrollment__candidate=candidate
            ).select_related('module').distinct()
            
            if enrollment_modules.exists():
                # LWAs heading
                lwa_heading_style = ParagraphStyle(
                    'LWAHeading',
                    parent=styles['Heading3'],
                    fontSize=12,
                    textColor=colors.black,
                    spaceAfter=10,
                    alignment=TA_LEFT,
                    fontName='Helvetica-Bold'
                )
                elements.append(Paragraph("Candidate Trained in the following:", lwa_heading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                # Collect all LWAs
                lwa_list = []
                for em in enrollment_modules:
                    module = em.module
                    # Get LWAs for this module
                    lwas = ModuleLWA.objects.filter(module=module).order_by('lwa_name')
                    for lwa in lwas:
                        lwa_list.append(f"• {lwa.lwa_name}")
                
                if lwa_list:
                    # Create LWA list
                    lwa_style = ParagraphStyle(
                        'LWAList',
                        parent=styles['Normal'],
                        fontSize=10,
                        leftIndent=20,
                        spaceAfter=4,
                        fontName='Helvetica'
                    )
                    
                    for lwa_text in lwa_list:
                        elements.append(Paragraph(lwa_text, lwa_style))
                else:
                    elements.append(Paragraph("No LWAs defined for enrolled modules", styles['Normal']))
        
        # Add footer section with moderate spacing
        elements.append(Spacer(1, 0.3*inch))
        
        # Footer disclaimer text
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            fontName='Helvetica',
            alignment=TA_LEFT,
            spaceAfter=3
        )
        
        italic_style = ParagraphStyle(
            'Italic',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            fontName='Helvetica-Oblique',
            alignment=TA_LEFT,
            spaceAfter=3
        )
        
        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            spaceAfter=3
        )
        
        # Try to load signature
        signature_img = None
        signature_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'es_signature.jpg')
        if os.path.exists(signature_path):
            try:
                signature_img = Image(signature_path, width=1.5*inch, height=0.8*inch)
            except:
                signature_img = None
        
        # Create footer layout
        footer_left_text = [
            Paragraph("THIS IS NOT A TRANSCRIPT", disclaimer_style),
            Paragraph("OFFICIAL TRANSCRIPT SHALL BE ISSUED AS SOON AS IT IS READY", disclaimer_style),
            Paragraph("<i>*The medium of instruction is ENGLISH*</i>", italic_style),
            Paragraph("<b>ANY ALTERATIONS WHATSOEVER RENDERS THIS VERIFICATION INVALID</b>", bold_style),
            Paragraph("See Reverse for Key Grades", disclaimer_style),
        ]
        
        footer_right_text = [
            Paragraph("<b>EXECUTIVE SECRETARY</b>", 
                     ParagraphStyle('ESTitle', parent=styles['Normal'], fontSize=9, 
                                  fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph("<font color='red'>Not Valid Without Official Stamp</font>", 
                     ParagraphStyle('Stamp', parent=styles['Normal'], fontSize=8, 
                                  fontName='Helvetica', alignment=TA_CENTER, textColor=colors.red)),
        ]
        
        # Build footer table
        if signature_img:
            footer_data = [[
                [footer_left_text[0], footer_left_text[1], footer_left_text[2], 
                 footer_left_text[3], footer_left_text[4]],
                [signature_img] + footer_right_text
            ]]
            footer_table = Table(footer_data, colWidths=[4.5*inch, 3*inch])
            footer_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ]))
        else:
            # Without signature
            footer_data = [[
                [footer_left_text[0], footer_left_text[1], footer_left_text[2], 
                 footer_left_text[3], footer_left_text[4]],
                footer_right_text
            ]]
            footer_table = Table(footer_data, colWidths=[4.5*inch, 3*inch])
            footer_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ]))
        
        elements.append(footer_table)
        
        # Add page break for back page
        elements.append(PageBreak())
        
        # Back page - Grading Key
        elements.append(Spacer(1, 0.3*inch))
        
        # Add logo on back page
        if os.path.exists(logo_path):
            try:
                back_logo = Image(logo_path, width=0.8*inch, height=0.8*inch)
                elements.append(back_logo)
                elements.append(Spacer(1, 0.2*inch))
            except:
                pass
        
        # Key: Grading heading
        key_title_style = ParagraphStyle(
            'KeyTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD", key_title_style))
        elements.append(Paragraph("KEY TO GRADES and QUALIFICATIONS AWARD", key_title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Theory and Practical scores table
        grading_header_style = ParagraphStyle(
            'GradingHeader',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )
        
        # Combined table with Theory and Practical side by side
        grading_data = [
            [Paragraph("<b>THEORY SCORES</b>", grading_header_style), "", 
             Paragraph("<b>PRACTICAL SCORES</b>", grading_header_style), ""],
            ["Grade", "Scores%", "Grade", "Scores%"],
            ["A+", "85-100", "A+", "90-100"],
            ["A", "80-84", "A", "85-89"],
            ["B", "70-79", "B+", "75-84"],
            ["B-", "60-69", "B", "65-74"],
            ["C", "50-59", "B-", "60-64"],
            ["C-", "40-49", "C", "55-59"],
            ["D", "30-39", "C-", "50-54"],
            ["E", "0-29", "D", "40-49"],
            ["", "", "D-", "30-39"],
            ["", "", "E", "0-29"],
        ]
        
        grading_table = Table(grading_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        grading_table.setStyle(TableStyle([
            # Header row spanning
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (2, 0), (3, 0)),
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#d3d3d3')),
            ('BACKGROUND', (2, 0), (3, 0), colors.HexColor('#d3d3d3')),
            # Column headers
            ('BACKGROUND', (0, 1), (1, 1), colors.white),
            ('BACKGROUND', (2, 1), (3, 1), colors.white),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            # All cells
            ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(grading_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Pass mark note
        pass_mark_style = ParagraphStyle(
            'PassMark',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=20
        )
        elements.append(Paragraph("Pass mark is 50% in theory and 65% in practical assessment", pass_mark_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Key Acronyms section
        acronym_heading_style = ParagraphStyle(
            'AcronymHeading',
            parent=styles['Heading3'],
            fontSize=12,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            spaceAfter=10
        )
        elements.append(Paragraph("KEY ACRONYMS:", acronym_heading_style))
        
        acronym_style = ParagraphStyle(
            'Acronym',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            alignment=TA_LEFT,
            spaceAfter=4,
            leftIndent=20
        )
        
        acronyms = [
            "• <b>Ms</b> - Missing",
        ]
        
        for acronym in acronyms:
            elements.append(Paragraph(acronym, acronym_style))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Footer copyright
        copyright_style = ParagraphStyle(
            'Copyright',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
            alignment=TA_CENTER,
            textColor=colors.black
        )
        
        elements.append(Paragraph(
            '© 2025 Uganda Vocational and Technical Assessments Board, P.O.Box 1499 Kampala - Uganda',
            copyright_style
        ))
        elements.append(Paragraph(
            '"Setting Pace for Quality Assessment"',
            ParagraphStyle('Slogan', parent=copyright_style, fontName='Helvetica-Oblique')
        ))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF value
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = HttpResponse(content_type='application/pdf')
        filename = f"Verifiedresults_{candidate.full_name.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf)
        
        return response

    @action(detail=False, methods=['get'], url_path='transcript-pdf')
    def transcript_pdf(self, request):
        """Generate official transcript PDF for candidate"""
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm, inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, Frame, PageTemplate, NextPageTemplate
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
        from reportlab.lib.utils import ImageReader
        from io import BytesIO
        from datetime import datetime
        from django.conf import settings
        import os
        import qrcode
        
        candidate_id = request.query_params.get('candidate_id')
        
        if not candidate_id:
            return Response(
                {'error': 'candidate_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if candidate qualifies for transcript (ALL results must be successful)
        modular_results = ModularResult.objects.filter(candidate=candidate)
        if not modular_results.exists():
            return Response(
                {'error': 'Candidate does not qualify for transcript. No results found.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        all_successful = all(r.comment == 'Success' for r in modular_results)
        
        if not all_successful:
            return Response(
                {'error': 'Candidate does not qualify for transcript. No successful results found.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Generate QR Code with candidate info
        qr_data = f"Name: {candidate.full_name}\nReg No: {candidate.registration_number}\nOccupation: {candidate.occupation.occ_name if candidate.occupation else ''}\nInstitution: {candidate.assessment_center.center_name if candidate.assessment_center else ''}\nAward: {candidate.occupation.award_modular if candidate.occupation else ''}\nCompletion Year: {datetime.now().year}"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=6, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Define Page Templates for mixed orientation
        def onFirstPage(canvas, doc):
            canvas.saveState()
            # Draw QR Code at top right (smaller size)
            qr_buffer.seek(0)
            canvas.drawImage(ImageReader(qr_buffer), A4[0] - 2.5*cm, A4[1] - 2.5*cm, width=1.5*cm, height=1.5*cm)
            
            # Signature at bottom right (no EXECUTIVE SECRETARY text)
            signature_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'es_signature.jpg')
            if os.path.exists(signature_path):
                try:
                    canvas.drawImage(signature_path, A4[0] - 6*cm, 1.5*cm, width=4*cm, height=2*cm, mask='auto', preserveAspectRatio=True)
                except:
                    pass
            canvas.restoreState()

        def onLaterPages(canvas, doc):
            pass

        def onPortraitBack(canvas, doc):
            # Rotate content -90 degrees (Clockwise)
            canvas.translate(0, A4[1])
            canvas.rotate(-90)

        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=2.5*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
        
        # Create Frames
        frame_portrait = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='portrait')
        frame_landscape = Frame(doc.leftMargin, doc.bottomMargin, landscape(A4)[0]-2*doc.leftMargin, landscape(A4)[1]-2*doc.bottomMargin, id='landscape')
        
        doc.addPageTemplates([
            PageTemplate(id='portrait', frames=frame_portrait, onPage=onFirstPage),
            # Landscape content frame on Portrait page with -90 rotation
            PageTemplate(id='portrait_back', frames=frame_landscape, onPage=onPortraitBack, pagesize=A4)
        ])

        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles with Serif font (Times-Roman) - smaller fonts for neat layout
        title_style = ParagraphStyle(
            'TranscriptTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=10,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        )
        
        info_label_style = ParagraphStyle(
            'InfoLabel',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Times-Bold',
            alignment=TA_LEFT
        )
        
        info_value_style = ParagraphStyle(
            'InfoValue',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Times-Roman',
            alignment=TA_LEFT
        )

        section_heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=8,
            spaceBefore=10,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        )

        # Content - Page 1 (No TRANSCRIPT title - paper already has it printed)
        elements.append(Spacer(1, 7.5*cm))

        # Photo with reg no caption (smaller font 6pt to fit on one line)
        photo_cell = None
        if candidate.passport_photo:
            photo_path = os.path.join(settings.MEDIA_ROOT, str(candidate.passport_photo))
            if os.path.exists(photo_path):
                try:
                    from PIL import Image as PILImage
                    from PIL import ImageOps
                    pil_image = PILImage.open(photo_path)
                    pil_image = ImageOps.exif_transpose(pil_image)
                    img_buffer = BytesIO()
                    pil_image.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    candidate_photo = Image(img_buffer, width=2.8*cm, height=3.5*cm)
                    # Photo with reg no below in smaller font
                    photo_caption_style = ParagraphStyle('PhotoCaption', parent=styles['Normal'], fontSize=6, fontName='Times-Roman', alignment=TA_LEFT)
                    photo_data = [[candidate_photo], [Paragraph(candidate.registration_number or "", photo_caption_style)]]
                    photo_cell = Table(photo_data, colWidths=[3.2*cm])
                    photo_cell.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('TOPPADDING', (0, 1), (0, 1), 2),
                    ]))
                except Exception as e:
                    print(f"Error loading photo: {e}")

        # Bio data table - NAME/values on left, NATIONALITY on right
        info_data = [
            [Paragraph("<b>NAME:</b>", info_label_style), Paragraph(candidate.full_name or "", info_value_style), 
             Paragraph("<b>NATIONALITY:</b>", info_label_style), Paragraph(candidate.nationality or "Ugandan", info_value_style)],
            [Paragraph("<b>REG NO:</b>", info_label_style), Paragraph(candidate.registration_number or "", info_value_style),
             Paragraph("<b>BIRTHDATE:</b>", info_label_style), Paragraph(candidate.date_of_birth.strftime("%d %b, %Y") if candidate.date_of_birth else "", info_value_style)],
            [Paragraph("<b>GENDER:</b>", info_label_style), Paragraph(candidate.gender.capitalize() if candidate.gender else "", info_value_style),
             Paragraph("<b>PRINTDATE:</b>", info_label_style), Paragraph(datetime.now().strftime("%d-%b-%Y"), info_value_style)],
            [Paragraph("<b>CENTER NAME:</b>", info_label_style), Paragraph(candidate.assessment_center.center_name if candidate.assessment_center else "", info_value_style), "", ""],
            [Paragraph("<b>OCCUPATION:</b>", info_label_style), Paragraph(candidate.occupation.occ_name if candidate.occupation else "", info_value_style), "", ""],
        ]

        info_table = Table(info_data, colWidths=[2.8*cm, 4.5*cm, 2.8*cm, 3.5*cm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('SPAN', (1, 3), (3, 3)), # Span center name
            ('SPAN', (1, 4), (3, 4)), # Span occupation
        ]))

        # Combine photo and bio data side by side
        if photo_cell:
            combined = Table([[photo_cell, info_table]], colWidths=[3.5*cm, 14*cm])
            combined.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(combined)
        else:
            elements.append(info_table)

        elements.append(Spacer(1, 0.2*cm))
        elements.append(Paragraph("ASSESSMENT RESULTS", section_heading_style))
        elements.append(Spacer(1, 0.1*cm))

        # Results Table - Modular (Code, Module Name, CU, Grade)
        results = ModularResult.objects.filter(candidate=candidate).select_related('module', 'module__level', 'assessment_series')
        
        candidate_total_cus = 0
        level_total_cus = 0
        completion_date = None
        
        if results.exists():
            results_data = [[
                Paragraph("CODE", info_label_style),
                Paragraph("MODULE NAME", info_label_style),
                Paragraph("CU", info_label_style),
                Paragraph("GRADE", info_label_style)
            ]]
            
            for result in results:
                module_code = result.module.module_code if result.module else ""
                module_name = result.module.module_name if result.module else ""
                module_cu = result.module.credit_units if result.module and result.module.credit_units else 0
                candidate_total_cus += module_cu
                
                # Get completion date from assessment_series (name already contains full info like "March 2025")
                if result.assessment_series and not completion_date:
                    completion_date = result.assessment_series.name
                
                results_data.append([
                    Paragraph(module_code, info_value_style),
                    Paragraph(module_name, info_value_style),
                    Paragraph(str(module_cu) if module_cu else "-", info_value_style),
                    Paragraph(result.grade or "-", info_value_style)
                ])
            
            t = Table(results_data, colWidths=[2.5*cm, 9*cm, 1.5*cm, 2*cm], repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),  # CU column centered
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph("No results found.", info_value_style))

        # Calculate level total CUs
        if candidate.occupation:
            from occupations.models import OccupationModule
            level_modules = OccupationModule.objects.filter(occupation=candidate.occupation)
            for mod in level_modules:
                if mod.credit_units:
                    level_total_cus += mod.credit_units

        # LWAs - Candidate trained in the following
        elements.append(Spacer(1, 0.3*cm))
        enrollment_modules = EnrollmentModule.objects.filter(
            enrollment__candidate=candidate
        ).select_related('module').distinct()
        
        if enrollment_modules.exists():
            elements.append(Paragraph("<b>Candidate trained in the following:</b>", ParagraphStyle('SubHeading', parent=styles['Normal'], fontName='Times-Roman', fontSize=9)))
            
            lwa_list = []
            for em in enrollment_modules:
                lwas = ModuleLWA.objects.filter(module=em.module).order_by('lwa_name')
                for lwa in lwas:
                    if lwa.lwa_name not in lwa_list:
                        lwa_list.append(lwa.lwa_name)
            
            lwa_text = ", ".join(lwa_list) if lwa_list else "-"
            elements.append(Paragraph(lwa_text, ParagraphStyle('LWA', parent=styles['Normal'], fontName='Times-Roman', fontSize=9)))

        # Credit Units summary
        elements.append(Spacer(1, 0.2*cm))
        cu_summary = Table([
            [Paragraph(f"<b>Total Credit Units:</b> {level_total_cus}", info_value_style),
             Paragraph(f"<b>Credit Units:</b> {candidate_total_cus}", info_value_style)]
        ], colWidths=[8*cm, 7*cm])
        cu_summary.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0)]))
        elements.append(cu_summary)

        # Duration (Contact hours from level - get from first module's level)
        duration = "-"
        level_award = "-"
        if results.exists():
            first_result = results.first()
            if first_result.module and first_result.module.level:
                level = first_result.module.level
                duration = level.contact_hours if level.contact_hours else "-"
                level_award = level.award if level.award else "-"
        elements.append(Paragraph(f"<b>Duration:</b> {duration}", info_value_style))

        # Award (Modular award from occupation - stays on occupation for modular candidates)
        award = candidate.occupation.award_modular if candidate.occupation and candidate.occupation.award_modular else level_award
        elements.append(Paragraph(f"<b>Award:</b> {award}", info_value_style))

        # Completion Year (from assessment series)
        elements.append(Paragraph(f"<b>Completion Year:</b> {completion_date or '-'}", info_value_style))

        elements.append(Spacer(1, 0.5*cm))

        # Page Break (Starts using portrait_back template)
        elements.append(NextPageTemplate('portrait_back'))
        elements.append(PageBreak())
        
        # Page 2 - Header (Logo + Title)
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=1.5*cm, height=1.5*cm)
                elements.append(logo)
                elements.append(Spacer(1, 0.2*cm))
            except:
                pass
        
        elements.append(Paragraph("UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD", ParagraphStyle(
            'Page2Title', parent=styles['Heading1'], fontSize=12, alignment=TA_CENTER, fontName='Times-Bold', spaceAfter=10
        )))

        # Key to Grades Title
        heading2_style = ParagraphStyle(
            'Heading2Center', 
            parent=styles['Heading2'], 
            alignment=TA_CENTER, 
            fontName='Times-Bold',
            fontSize=16,
            spaceAfter=15
        )
        
        elements.append(Paragraph("KEY TO GRADES and QUALIFICATIONS AWARD", heading2_style))
        elements.append(Spacer(1, 0.5*cm))

        # Grading Table (Fitted for Portrait - 4.25cm * 4 = 17cm)
        grading_data = [
            [Paragraph("<b>THEORY SCORES</b>", info_label_style), "", 
             Paragraph("<b>PRACTICAL SCORES</b>", info_label_style), ""],
            ["Grade", "Scores%", "Grade", "Scores%"],
            ["A+", "85-100", "A+", "90-100"],
            ["A", "80-84", "A", "85-89"],
            ["B", "70-79", "B+", "75-84"],
            ["B-", "60-69", "B", "65-74"],
            ["C", "50-59", "B-", "60-64"],
            ["C-", "40-49", "C", "55-59"],
            ["D", "30-39", "C-", "50-54"],
            ["E", "0-29", "D", "40-49"],
            ["", "", "D-", "30-39"],
            ["", "", "E", "0-29"],
        ]
        
        # Widths adjusted for Portrait (Max ~18cm)
        grading_table = Table(grading_data, colWidths=[4.2*cm, 4.2*cm, 4.2*cm, 4.2*cm])
        grading_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (2, 0), (3, 0)),
            ('BACKGROUND', (0, 0), (3, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ('FONTNAME', (0, 1), (-1, 1), 'Times-Bold'), # Header row
        ]))
        
        elements.append(grading_table)
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph("Pass mark is 50% in theory and 65% in practical assessment", ParagraphStyle('PassMark', parent=styles['Normal'], alignment=TA_CENTER, fontName='Times-Bold', fontSize=12)))

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        filename = f"Transcript_{candidate.full_name.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response.write(pdf)
        
        return response


class FormalResultViewSet(viewsets.ViewSet):
    """
    ViewSet for managing formal assessment results
    Supports both module-based and paper-based structures
    """
    permission_classes = [AllowAny]  # Temporarily allow all to test
    
    @action(detail=False, methods=['post'], url_path='add')
    def add_results(self, request):
        """Add formal results for a candidate"""
        from .models import FormalResult
        from occupations.models import OccupationLevel, OccupationModule, OccupationPaper
        
        candidate_id = request.data.get('candidate_id')
        assessment_series_id = request.data.get('assessment_series')
        level_id = request.data.get('level_id')
        structure_type = request.data.get('structure_type')  # 'modules' or 'papers'
        results_data = request.data.get('results', [])
        
        if not candidate_id:
            return Response(
                {'error': 'Candidate ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not assessment_series_id:
            return Response(
                {'error': 'Assessment series is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not level_id:
            return Response(
                {'error': 'Level ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not structure_type:
            return Response(
                {'error': 'Structure type is required (modules or papers)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not results_data:
            return Response(
                {'error': 'No results data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get candidate
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify candidate is formal
        if candidate.registration_category != 'formal':
            return Response(
                {'error': 'Candidate is not registered for formal assessment'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get assessment series
        try:
            assessment_series = AssessmentSeries.objects.get(id=assessment_series_id)
        except AssessmentSeries.DoesNotExist:
            return Response(
                {'error': 'Assessment series not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get level
        try:
            level = OccupationLevel.objects.get(id=level_id)
        except OccupationLevel.DoesNotExist:
            return Response(
                {'error': 'Level not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        created_results = []
        created_count = 0
        updated_count = 0
        
        if structure_type == 'modules':
            # Module-based: Get the first exam for this level if not provided
            for result_data in results_data:
                exam_id = result_data.get('exam_id')
                result_type = result_data.get('type')  # 'theory' or 'practical'
                mark = result_data.get('mark')
                
                # If no exam_id provided, get the first exam for this level
                if not exam_id:
                    first_exam = level.modules.first()
                    if not first_exam:
                        return Response(
                            {'error': 'No exams found for this level'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    exam_id = first_exam.id
                
                try:
                    exam = OccupationModule.objects.get(id=exam_id)
                    
                    # Create or update result
                    defaults_data = {
                        'mark': mark,
                        'status': 'normal',
                    }
                    
                    if request.user and request.user.is_authenticated:
                        defaults_data['entered_by'] = request.user
                    
                    result, created = FormalResult.objects.update_or_create(
                        candidate=candidate,
                        assessment_series=assessment_series,
                        level=level,
                        exam=exam,
                        type=result_type,
                        defaults=defaults_data
                    )
                    created_results.append(result)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                except OccupationModule.DoesNotExist:
                    return Response(
                        {'error': f'Exam with id {exam_id} not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                except Exception as e:
                    return Response(
                        {'error': f'Error creating result: {str(e)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        elif structure_type == 'papers':
            # Paper-based: Get the first paper for this level if not provided
            for result_data in results_data:
                paper_id = result_data.get('paper_id')
                result_type = result_data.get('type')  # 'theory' or 'practical'
                mark = result_data.get('mark')
                
                # If no paper_id provided, get the first paper for this level
                if not paper_id:
                    first_paper = level.papers.first()
                    if not first_paper:
                        return Response(
                            {'error': 'No papers found for this level'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    paper_id = first_paper.id
                
                try:
                    paper = OccupationPaper.objects.get(id=paper_id)
                    
                    # Create or update result
                    defaults_data = {
                        'mark': mark,
                        'status': 'normal',
                    }
                    
                    if request.user and request.user.is_authenticated:
                        defaults_data['entered_by'] = request.user
                    
                    result, created = FormalResult.objects.update_or_create(
                        candidate=candidate,
                        assessment_series=assessment_series,
                        level=level,
                        paper=paper,
                        type=result_type,
                        defaults=defaults_data
                    )
                    created_results.append(result)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                except OccupationPaper.DoesNotExist:
                    return Response(
                        {'error': f'Paper with id {paper_id} not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                except Exception as e:
                    return Response(
                        {'error': f'Error creating result: {str(e)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        else:
            return Response(
                {'error': 'Invalid structure type. Must be "modules" or "papers"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        _log_candidate_activity(
            request,
            candidate,
            'formal_results_saved',
            'Formal results saved',
            details={
                'assessment_series_id': assessment_series.id,
                'assessment_series_name': assessment_series.name,
                'level_id': level.id,
                'level_name': level.level_name,
                'structure_type': structure_type,
                'created': created_count,
                'updated': updated_count,
            },
        )
        
        return Response(
            {
                'message': f'{len(created_results)} results added successfully',
                'count': len(created_results)
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['put'], url_path='update')
    def update_results(self, request):
        """Update existing formal results"""
        from .models import FormalResult
        
        candidate_id = request.data.get('candidate_id')
        results_data = request.data.get('results', [])
        
        if not candidate_id:
            return Response(
                {'error': 'Candidate ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not results_data:
            return Response(
                {'error': 'No results data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get candidate
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update results
        updated_count = 0
        for result_data in results_data:
            result_id = result_data.get('result_id')
            mark = result_data.get('mark')
            
            try:
                result = FormalResult.objects.get(id=result_id, candidate=candidate)
                result.mark = mark
                
                # Update entered_by if user is authenticated
                if request.user and request.user.is_authenticated:
                    result.entered_by = request.user
                
                result.save()
                updated_count += 1
            except FormalResult.DoesNotExist:
                return Response(
                    {'error': f'Result with id {result_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {'error': f'Error updating result: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        _log_candidate_activity(
            request,
            candidate,
            'formal_results_updated',
            'Formal results updated',
            details={
                'updated': updated_count,
            },
        )
        
        return Response(
            {
                'message': f'{updated_count} results updated successfully',
                'count': updated_count
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='list')
    def list_results(self, request):
        """List formal results for a candidate"""
        from .models import FormalResult
        
        candidate_id = request.query_params.get('candidate_id')
        series_id = request.query_params.get('series_id')
        
        if not candidate_id:
            return Response(
                {'error': 'candidate_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get candidate
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Build query
        query = FormalResult.objects.filter(candidate=candidate)
        
        if series_id:
            query = query.filter(assessment_series_id=series_id)
        
        results = query.select_related(
            'assessment_series', 'level', 'exam', 'paper', 'entered_by'
        ).order_by('level', 'exam', 'paper', 'type')
        
        # Format results
        results_data = []
        for result in results:
            exam_or_paper_name = ''
            exam_or_paper_id = None
            
            if result.exam:
                exam_or_paper_name = result.exam.module_name
                exam_or_paper_id = result.exam.id
            elif result.paper:
                exam_or_paper_name = result.paper.paper_name
                exam_or_paper_id = result.paper.id
            
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
                'exam_or_paper': {
                    'id': exam_or_paper_id,
                    'name': exam_or_paper_name,
                    'is_exam': result.exam is not None,
                },
                'type': result.type,
                'mark': float(result.mark) if result.mark is not None else None,
                'grade': result.grade,
                'comment': result.comment,
                'status': result.status,
                'entered_by': result.entered_by.get_full_name() if result.entered_by else None,
                'entered_at': result.entered_at,
            })
        
        return Response(results_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='transcript-pdf')
    def transcript_pdf(self, request):
        """Generate official transcript PDF for formal candidate"""
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm, inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, Frame, PageTemplate, NextPageTemplate
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
        from reportlab.lib.utils import ImageReader
        from io import BytesIO
        from datetime import datetime
        from django.conf import settings
        import os
        import qrcode
        from .models import FormalResult
        
        candidate_id = request.query_params.get('candidate_id')
        
        if not candidate_id:
            return Response(
                {'error': 'candidate_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if candidate qualifies for transcript (ALL results must be successful)
        formal_results = FormalResult.objects.filter(candidate=candidate)
        if not formal_results.exists():
            return Response(
                {'error': 'Candidate does not qualify for transcript. No results found.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        all_successful = all(r.comment == 'Successful' for r in formal_results)
        
        if not all_successful:
            return Response(
                {'error': 'Candidate does not qualify for transcript. No successful results found.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Generate QR Code with candidate info (award now comes from level, determined later)
        qr_data = f"Name: {candidate.full_name}\nReg No: {candidate.registration_number}\nOccupation: {candidate.occupation.occ_name if candidate.occupation else ''}\nInstitution: {candidate.assessment_center.center_name if candidate.assessment_center else ''}\nCompletion Year: {datetime.now().year}"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=6, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Define Page Templates for mixed orientation
        def onFirstPage(canvas, doc):
            canvas.saveState()
            # Draw QR Code at top right (smaller size)
            qr_buffer.seek(0)
            canvas.drawImage(ImageReader(qr_buffer), A4[0] - 2.5*cm, A4[1] - 2.5*cm, width=1.5*cm, height=1.5*cm)
            
            # Signature at bottom right (no EXECUTIVE SECRETARY text)
            signature_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'es_signature.jpg')
            if os.path.exists(signature_path):
                try:
                    canvas.drawImage(signature_path, A4[0] - 6*cm, 1.5*cm, width=4*cm, height=2*cm, mask='auto', preserveAspectRatio=True)
                except:
                    pass
            canvas.restoreState()

        def onLaterPages(canvas, doc):
            pass

        def onPortraitBack(canvas, doc):
            # Rotate content -90 degrees (Clockwise)
            canvas.translate(0, A4[1])
            canvas.rotate(-90)

        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=2.5*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
        
        # Create Frames
        frame_portrait = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='portrait')
        frame_landscape = Frame(doc.leftMargin, doc.bottomMargin, landscape(A4)[0]-2*doc.leftMargin, landscape(A4)[1]-2*doc.bottomMargin, id='landscape')
        
        doc.addPageTemplates([
            PageTemplate(id='portrait', frames=frame_portrait, onPage=onFirstPage),
            # Landscape content frame on Portrait page with -90 rotation
            PageTemplate(id='portrait_back', frames=frame_landscape, onPage=onPortraitBack, pagesize=A4)
        ])

        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles - smaller fonts for neat layout
        title_style = ParagraphStyle(
            'TranscriptTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=10,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        )
        
        info_label_style = ParagraphStyle(
            'InfoLabel',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Times-Bold',
            alignment=TA_LEFT
        )
        
        info_value_style = ParagraphStyle(
            'InfoValue',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Times-Roman',
            alignment=TA_LEFT
        )

        section_heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=8,
            spaceBefore=10,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        )

        # Content - Page 1 (No TRANSCRIPT title - paper already has it printed)
        elements.append(Spacer(1, 7.5*cm))

        # Photo with reg no caption (smaller font 6pt to fit on one line)
        photo_cell = None
        if candidate.passport_photo:
            photo_path = os.path.join(settings.MEDIA_ROOT, str(candidate.passport_photo))
            if os.path.exists(photo_path):
                try:
                    from PIL import Image as PILImage
                    from PIL import ImageOps
                    pil_image = PILImage.open(photo_path)
                    pil_image = ImageOps.exif_transpose(pil_image)
                    img_buffer = BytesIO()
                    pil_image.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    candidate_photo = Image(img_buffer, width=2.8*cm, height=3.5*cm)
                    # Photo with reg no below in smaller font
                    photo_caption_style = ParagraphStyle('PhotoCaption', parent=styles['Normal'], fontSize=6, fontName='Times-Roman', alignment=TA_LEFT)
                    photo_data = [[candidate_photo], [Paragraph(candidate.registration_number or "", photo_caption_style)]]
                    photo_cell = Table(photo_data, colWidths=[3.2*cm])
                    photo_cell.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('TOPPADDING', (0, 1), (0, 1), 2),
                    ]))
                except Exception as e:
                    print(f"Error loading photo: {e}")

        # Bio data table - NAME/values on left, NATIONALITY on right
        info_data = [
            [Paragraph("<b>NAME:</b>", info_label_style), Paragraph(candidate.full_name or "", info_value_style), 
             Paragraph("<b>NATIONALITY:</b>", info_label_style), Paragraph(candidate.nationality or "Ugandan", info_value_style)],
            [Paragraph("<b>REG NO:</b>", info_label_style), Paragraph(candidate.registration_number or "", info_value_style),
             Paragraph("<b>BIRTHDATE:</b>", info_label_style), Paragraph(candidate.date_of_birth.strftime("%d %b, %Y") if candidate.date_of_birth else "", info_value_style)],
            [Paragraph("<b>GENDER:</b>", info_label_style), Paragraph(candidate.gender.capitalize() if candidate.gender else "", info_value_style),
             Paragraph("<b>PRINTDATE:</b>", info_label_style), Paragraph(datetime.now().strftime("%d-%b-%Y"), info_value_style)],
            [Paragraph("<b>CENTER NAME:</b>", info_label_style), Paragraph(candidate.assessment_center.center_name if candidate.assessment_center else "", info_value_style), "", ""],
            [Paragraph("<b>OCCUPATION:</b>", info_label_style), Paragraph(candidate.occupation.occ_name if candidate.occupation else "", info_value_style), "", ""],
        ]

        info_table = Table(info_data, colWidths=[2.8*cm, 4.5*cm, 2.8*cm, 3.5*cm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('SPAN', (1, 3), (3, 3)), # Span center name
            ('SPAN', (1, 4), (3, 4)), # Span occupation
        ]))

        # Combine photo and bio data side by side
        if photo_cell:
            combined = Table([[photo_cell, info_table]], colWidths=[3.5*cm, 14*cm])
            combined.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(combined)
        else:
            elements.append(info_table)

        elements.append(Spacer(1, 0.2*cm))
        elements.append(Paragraph("ASSESSMENT RESULTS", section_heading_style))
        elements.append(Spacer(1, 0.1*cm))

        # Formal Results - check level structure type
        results = FormalResult.objects.filter(candidate=candidate).select_related(
            'level', 'exam', 'exam__level', 'paper', 'assessment_series'
        ).order_by('level', 'type')
        
        completion_date = None
        level_total_cus = 0
        
        if results.exists():
            # Get first result to determine structure type
            first_result = results.first()
            is_paper_based = first_result.level and first_result.level.structure_type == 'papers'
            
            # Get completion date from assessment series
            if first_result.assessment_series:
                completion_date = first_result.assessment_series.name
            
            # Calculate level total CUs
            if first_result.level:
                if is_paper_based:
                    from occupations.models import OccupationPaper
                    level_papers = OccupationPaper.objects.filter(level=first_result.level)
                    for paper in level_papers:
                        if paper.credit_units:
                            level_total_cus += paper.credit_units
                else:
                    from occupations.models import OccupationModule
                    level_modules = OccupationModule.objects.filter(level=first_result.level)
                    for mod in level_modules:
                        if mod.credit_units:
                            level_total_cus += mod.credit_units
            
            if is_paper_based:
                # PAPER-BASED: Split table - Theory | Practical (each with Code, Module, CU, Grade)
                theory_results = [r for r in results if r.type == 'theory']
                practical_results = [r for r in results if r.type == 'practical']
                
                # Build theory side
                theory_data = [[
                    Paragraph("<b>Code</b>", info_label_style),
                    Paragraph("<b>Module</b>", info_label_style),
                    Paragraph("<b>CU</b>", info_label_style),
                    Paragraph("<b>Grade</b>", info_label_style)
                ]]
                for r in theory_results:
                    code = r.paper.paper_code if r.paper else "-"
                    name = r.paper.paper_name if r.paper else "-"
                    cu = r.paper.credit_units if r.paper and r.paper.credit_units else "-"
                    theory_data.append([
                        Paragraph(code, info_value_style),
                        Paragraph(name, info_value_style),
                        Paragraph(str(cu), info_value_style),
                        Paragraph(r.grade or "-", info_value_style)
                    ])
                
                # Build practical side
                practical_data = [[
                    Paragraph("<b>Code</b>", info_label_style),
                    Paragraph("<b>Module</b>", info_label_style),
                    Paragraph("<b>CU</b>", info_label_style),
                    Paragraph("<b>Grade</b>", info_label_style)
                ]]
                for r in practical_results:
                    code = r.paper.paper_code if r.paper else "-"
                    name = r.paper.paper_name if r.paper else "-"
                    cu = r.paper.credit_units if r.paper and r.paper.credit_units else "-"
                    practical_data.append([
                        Paragraph(code, info_value_style),
                        Paragraph(name, info_value_style),
                        Paragraph(str(cu), info_value_style),
                        Paragraph(r.grade or "-", info_value_style)
                    ])
                
                # Create side-by-side tables
                theory_table = Table(theory_data, colWidths=[1.8*cm, 3.5*cm, 1*cm, 1.2*cm])
                theory_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                ]))
                
                practical_table = Table(practical_data, colWidths=[1.8*cm, 3.5*cm, 1*cm, 1.2*cm])
                practical_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                ]))
                
                # Combine with headers
                combined_header = Table([
                    [Paragraph("<b>THEORY</b>", ParagraphStyle('Header', parent=styles['Normal'], fontSize=9, fontName='Times-Bold', alignment=TA_CENTER)),
                     Paragraph("<b>PRACTICAL</b>", ParagraphStyle('Header', parent=styles['Normal'], fontSize=9, fontName='Times-Bold', alignment=TA_CENTER))]
                ], colWidths=[7.5*cm, 7.5*cm])
                combined_header.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
                elements.append(combined_header)
                
                combined_tables = Table([[theory_table, practical_table]], colWidths=[7.5*cm, 7.5*cm])
                combined_tables.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
                elements.append(combined_tables)
                
            else:
                # MODULE-BASED: Simple 2-column table (Theory Grade | Practical Grade)
                # Group results by module
                module_results = {}
                modules_trained = []
                for r in results:
                    if r.exam:
                        mod_id = r.exam.id
                        if mod_id not in module_results:
                            module_results[mod_id] = {'module': r.exam, 'theory': '-', 'practical': '-'}
                            modules_trained.append(f"{r.exam.module_name} ({r.exam.credit_units or 0} CU)")
                        if r.type == 'theory':
                            module_results[mod_id]['theory'] = r.grade or '-'
                        else:
                            module_results[mod_id]['practical'] = r.grade or '-'
                
                # Build table
                module_table_data = [[
                    Paragraph("<b>Theory</b>", info_label_style),
                    Paragraph("<b>Grade</b>", info_label_style),
                    Paragraph("<b>Practical</b>", info_label_style),
                    Paragraph("<b>Grade</b>", info_label_style)
                ]]
                for mod_id, data in module_results.items():
                    module_table_data.append([
                        Paragraph("Theory", info_value_style),
                        Paragraph(data['theory'], info_value_style),
                        Paragraph("Practical", info_value_style),
                        Paragraph(data['practical'], info_value_style)
                    ])
                
                t = Table(module_table_data, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm], repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
                ]))
                elements.append(t)
                
                # Modules trained
                if modules_trained:
                    elements.append(Spacer(1, 0.2*cm))
                    elements.append(Paragraph(f"<b>Modules trained:</b> {', '.join(modules_trained)}", info_value_style))
        else:
            elements.append(Paragraph("No results found.", info_value_style))
        
        # Footer info - get duration and award from level
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(f"<b>Total Credit Units:</b> {level_total_cus}", info_value_style))
        
        # Get duration and award from level
        duration = "-"
        award = "-"
        if results.exists():
            first_result = results.first()
            if first_result.level:
                duration = first_result.level.contact_hours if first_result.level.contact_hours else "-"
                award = first_result.level.award if first_result.level.award else "-"
        elements.append(Paragraph(f"<b>Duration:</b> {duration}", info_value_style))
        elements.append(Paragraph(f"<b>Award:</b> {award}", info_value_style))
        
        elements.append(Paragraph(f"<b>Completion Year:</b> {completion_date or '-'}", info_value_style))
            
        elements.append(Spacer(1, 0.5*cm))

        # Page Break (Stays Portrait but uses portrait_back template with rotation)
        elements.append(NextPageTemplate('portrait_back'))
        elements.append(PageBreak())
        
        # Page 2 - Header (Logo + Title)
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=1.5*cm, height=1.5*cm)
                elements.append(logo)
                elements.append(Spacer(1, 0.2*cm))
            except:
                pass
        
        elements.append(Paragraph("UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD", ParagraphStyle(
            'Page2Title', parent=styles['Heading1'], fontSize=12, alignment=TA_CENTER, fontName='Times-Bold', spaceAfter=10
        )))

        # Key to Grades Title
        heading2_style = ParagraphStyle(
            'Heading2Center', 
            parent=styles['Heading2'], 
            alignment=TA_CENTER, 
            fontName='Times-Bold',
            fontSize=16,
            spaceAfter=15
        )
        
        elements.append(Paragraph("KEY TO GRADES and QUALIFICATIONS AWARD", heading2_style))
        elements.append(Spacer(1, 0.5*cm))

        # Grading Table
        grading_data = [
            [Paragraph("<b>THEORY SCORES</b>", info_label_style), "", 
             Paragraph("<b>PRACTICAL SCORES</b>", info_label_style), ""],
            ["Grade", "Scores%", "Grade", "Scores%"],
            ["A+", "85-100", "A+", "90-100"],
            ["A", "80-84", "A", "85-89"],
            ["B", "70-79", "B+", "75-84"],
            ["B-", "60-69", "B", "65-74"],
            ["C", "50-59", "B-", "60-64"],
            ["C-", "40-49", "C", "55-59"],
            ["D", "30-39", "C-", "50-54"],
            ["E", "0-29", "D", "40-49"],
            ["", "", "D-", "30-39"],
            ["", "", "E", "0-29"],
        ]
        
        grading_table = Table(grading_data, colWidths=[4.2*cm, 4.2*cm, 4.2*cm, 4.2*cm])
        grading_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (2, 0), (3, 0)),
            ('BACKGROUND', (0, 0), (3, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ('FONTNAME', (0, 1), (-1, 1), 'Times-Bold'), # Header row
        ]))
        
        elements.append(grading_table)
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph("Pass mark is 50% in theory and 65% in practical assessment", ParagraphStyle('PassMark', parent=styles['Normal'], alignment=TA_CENTER, fontName='Times-Bold', fontSize=12)))

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        filename = f"Transcript_{candidate.full_name.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response.write(pdf)
        
        return response




class WorkersPasResultViewSet(viewsets.ViewSet):
    """
    ViewSet for managing Worker's PAS assessment results
    """
    permission_classes = [AllowAny]  # Temporarily allow all to test
    
    @action(detail=False, methods=['post'], url_path='add')
    def add_results(self, request):
        """Add Workers PAS results for a candidate"""
        candidate_id = request.data.get('candidate_id')
        assessment_series_id = request.data.get('assessment_series')
        results_data = request.data.get('results', [])
        
        if not candidate_id:
            return Response(
                {'error': 'Candidate ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not assessment_series_id:
            return Response(
                {'error': 'Assessment series is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not results_data:
            return Response(
                {'error': 'No results data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get candidate
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify candidate is Workers PAS
        if candidate.registration_category != 'workers_pas':
            return Response(
                {'error': 'Candidate is not registered for Workers PAS assessment'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get assessment series
        try:
            assessment_series = AssessmentSeries.objects.get(id=assessment_series_id)
        except AssessmentSeries.DoesNotExist:
            return Response(
                {'error': 'Assessment series not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        created_results = []
        errors = []
        
        for result_data in results_data:
            serializer = WorkersPasResultCreateUpdateSerializer(data=result_data)
            
            if not serializer.is_valid():
                errors.append({
                    'paper_id': result_data.get('paper_id'),
                    'errors': serializer.errors
                })
                continue
            
            paper_id = serializer.validated_data['paper_id']
            mark = serializer.validated_data.get('mark')
            result_status = serializer.validated_data.get('status', 'normal')
            
            # Get the paper
            try:
                paper = OccupationPaper.objects.select_related('level', 'module').get(id=paper_id)
                
                # Debug logging
                print(f"Paper: {paper.paper_code}, Level: {paper.level}, Module: {paper.module}")
                
                # Validate that paper has a module (required for Workers PAS)
                if not paper.module:
                    errors.append({
                        'paper_id': paper_id,
                        'errors': {'paper_id': [f'Paper {paper.paper_code} does not have a module assigned. Please assign a module in the admin panel.']}
                    })
                    continue
                
                # Create or update result
                defaults_data = {
                    'level': paper.level,
                    'module': paper.module,
                    'mark': mark,
                    'status': result_status,
                }
                
                # Only set entered_by if user is authenticated
                if request.user and request.user.is_authenticated:
                    defaults_data['entered_by'] = request.user
                
                result, created = WorkersPasResult.objects.update_or_create(
                    candidate=candidate,
                    assessment_series=assessment_series,
                    paper=paper,
                    defaults=defaults_data
                )
                created_results.append(result)
            except OccupationPaper.DoesNotExist:
                errors.append({
                    'paper_id': paper_id,
                    'errors': {'paper_id': [f'Paper with id {paper_id} not found']}
                })
        
        if errors:
            return Response(
                {
                    'message': 'Some results could not be saved',
                    'created': len(created_results),
                    'errors': errors
                },
                status=status.HTTP_207_MULTI_STATUS
            )
        
        # Serialize the created results
        serializer = WorkersPasResultSerializer(created_results, many=True)
        
        _log_candidate_activity(
            request,
            candidate,
            'workers_pas_results_saved',
            "Worker's PAS results saved",
            details={
                'assessment_series_id': assessment_series.id,
                'assessment_series_name': assessment_series.name,
                'saved': len(created_results),
            },
        )

        return Response(
            {
                'message': f'{len(created_results)} result(s) saved successfully',
                'results': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], url_path='candidate/(?P<candidate_id>[^/.]+)')
    def get_candidate_results(self, request, candidate_id=None):
        """Get all Workers PAS results for a candidate"""
        series_id = request.query_params.get('series')
        
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Build query
        query = WorkersPasResult.objects.filter(candidate=candidate)
        
        if series_id:
            query = query.filter(assessment_series_id=series_id)
        
        results = query.select_related(
            'assessment_series', 'level', 'module', 'paper', 'entered_by'
        ).order_by('assessment_series', 'level', 'module', 'paper')
        
        serializer = WorkersPasResultSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='verified-pdf')
    def verified_results_pdf(self, request):
        """Generate verified results PDF for Workers PAS candidate"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from io import BytesIO
        from datetime import datetime
        from django.conf import settings
        import os
        
        candidate_id = request.query_params.get('candidate_id')
        
        if not candidate_id:
            return Response(
                {'error': 'candidate_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=20,
            spaceBefore=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.black,
            spaceAfter=10,
            spaceBefore=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Title at top
        elements.append(Paragraph("UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD", title_style))
        elements.append(Spacer(1, 0.15*inch))
        
        # Header with logo and contact info
        header_data = []
        
        # Try to add logo
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
        logo = None
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=0.7*inch, height=0.7*inch)
            except:
                logo = None
        
        if logo:
            header_data = [[
                Paragraph("Plot 7, Valley Drive, Ntinda-Kyambogo<br/>Road<br/>Email: info@uvtab.go.ug", 
                         ParagraphStyle('small', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT)),
                logo,
                Paragraph("P.O.Box 1499, Kampala,<br/>Tel: +256392002468", 
                         ParagraphStyle('small', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT))
            ]]
        else:
            header_data = [[
                Paragraph("Plot 7, Valley Drive, Ntinda-Kyambogo Road<br/>Email: info@uvtab.go.ug", 
                         ParagraphStyle('small', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT)),
                "",
                Paragraph("P.O.Box 1499, Kampala,<br/>Tel: +256392002468", 
                         ParagraphStyle('small', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT))
            ]]
        
        header_table = Table(header_data, colWidths=[2.3*inch, 2.4*inch, 2.3*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Title
        elements.append(Paragraph("VERIFICATION OF RESULTS", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("TO WHOM IT MAY CONCERN", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Intro text
        intro_style = ParagraphStyle('Intro', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Oblique')
        elements.append(Paragraph(
            "This is to verify that this candidate registered and sat for UVTAB assessments with the following particulars and obtained the following",
            intro_style
        ))
        elements.append(Spacer(1, 0.3*inch))
        
        # Candidate info with photo
        candidate_photo = None
        if candidate.passport_photo:
            photo_path = os.path.join(settings.MEDIA_ROOT, str(candidate.passport_photo))
            if os.path.exists(photo_path):
                try:
                    from PIL import Image as PILImage
                    from PIL import ImageOps
                    
                    pil_image = PILImage.open(photo_path)
                    pil_image = ImageOps.exif_transpose(pil_image)
                    
                    img_buffer = BytesIO()
                    pil_image.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    candidate_photo = Image(img_buffer, width=1.2*inch, height=1.5*inch)
                except Exception as e:
                    print(f"Error loading photo: {e}")
                    candidate_photo = None
        
        # Build info data
        info_data = [
            ["NAME:", candidate.full_name or "", "NATIONALITY:", candidate.nationality or "Uganda"],
            ["REG NO:", candidate.registration_number or "", "BIRTHDATE:", candidate.date_of_birth.strftime("%d %b, %Y") if candidate.date_of_birth else ""],
            ["GENDER:", candidate.gender.capitalize() if candidate.gender else "", "PRINTDATE:", datetime.now().strftime("%d-%b-%Y")],
            ["CENTER NAME:", candidate.assessment_center.center_name if candidate.assessment_center else "", "", ""],
            ["CATEGORY:", candidate.get_registration_category_display() if candidate.registration_category else "", "", ""],
            ["OCCUPATION:", candidate.occupation.occ_name if candidate.occupation else "", "", ""],
        ]
        
        info_table = Table(info_data, colWidths=[1.15*inch, 1.85*inch, 1.15*inch, 1.35*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (0, -1), 5),
            ('RIGHTPADDING', (1, 0), (1, -1), 10),
            ('RIGHTPADDING', (2, 0), (2, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        # Combine photo and info table
        if candidate_photo:
            combined_data = [[candidate_photo, info_table]]
            combined_table = Table(combined_data, colWidths=[1.3*inch, 6.5*inch])
            combined_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (0, -1), 10),
            ]))
            elements.append(combined_table)
        else:
            elements.append(info_table)
        
        elements.append(Spacer(1, 0.4*inch))
        
        # Results section
        elements.append(Paragraph("ASSESSMENT RESULTS", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Get Workers PAS results
        results = WorkersPasResult.objects.filter(candidate=candidate).select_related(
            'level', 'module', 'paper', 'assessment_series'
        ).order_by('level', 'module', 'paper')
        
        if results.exists():
            # Results table with Level, Module, Paper, Type, Grade, Comment
            results_data = [["LEVEL", "MODULE", "PAPER", "TYPE", "GRADE", "COMMENT"]]
            for result in results:
                results_data.append([
                    result.level.level_name if result.level else "-",
                    f"{result.module.module_code}\n{result.module.module_name}" if result.module else "-",
                    f"{result.paper.paper_code}\n{result.paper.paper_name}" if result.paper else "-",
                    "Practical",
                    result.grade or "-",
                    result.comment or "-"
                ])
            
            results_table = Table(results_data, colWidths=[1.2*inch, 1.8*inch, 1.8*inch, 1.0*inch, 0.9*inch, 1.3*inch])
            results_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                # Data rows
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                # Borders
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            ]))
            elements.append(results_table)
        else:
            elements.append(Paragraph("No results available", styles['Normal']))
        
        # Add footer section
        elements.append(Spacer(1, 0.5*inch))
        
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            fontName='Helvetica',
            alignment=TA_LEFT,
            spaceAfter=3
        )
        
        italic_style = ParagraphStyle(
            'Italic',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            fontName='Helvetica-Oblique',
            alignment=TA_LEFT,
            spaceAfter=3
        )
        
        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            spaceAfter=3
        )
        
        # Try to load signature
        signature_img = None
        signature_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'es_signature.jpg')
        if os.path.exists(signature_path):
            try:
                signature_img = Image(signature_path, width=1.5*inch, height=0.8*inch)
            except:
                signature_img = None
        
        footer_left_text = [
            Paragraph("THIS IS NOT A TRANSCRIPT", disclaimer_style),
            Paragraph("OFFICIAL TRANSCRIPT SHALL BE ISSUED AS SOON AS IT IS READY", disclaimer_style),
            Paragraph("<i>*The medium of instruction is ENGLISH*</i>", italic_style),
            Paragraph("<b>ANY ALTERATIONS WHATSOEVER RENDERS THIS VERIFICATION INVALID</b>", bold_style),
            Paragraph("See Reverse for Key Grades", disclaimer_style),
        ]
        
        footer_right_text = [
            Paragraph("<b>EXECUTIVE SECRETARY</b>", 
                     ParagraphStyle('ESTitle', parent=styles['Normal'], fontSize=9, 
                                  fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph("<font color='red'>Not Valid Without Official Stamp</font>", 
                     ParagraphStyle('Stamp', parent=styles['Normal'], fontSize=8, 
                                  fontName='Helvetica', alignment=TA_CENTER, textColor=colors.red)),
        ]
        
        if signature_img:
            footer_data = [[
                [footer_left_text[0], footer_left_text[1], footer_left_text[2], 
                 footer_left_text[3], footer_left_text[4]],
                [signature_img] + footer_right_text
            ]]
            footer_table = Table(footer_data, colWidths=[4.5*inch, 3*inch])
            footer_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ]))
        else:
            footer_data = [[
                [footer_left_text[0], footer_left_text[1], footer_left_text[2], 
                 footer_left_text[3], footer_left_text[4]],
                footer_right_text
            ]]
            footer_table = Table(footer_data, colWidths=[5*inch, 2.5*inch])
            footer_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ]))
        
        elements.append(footer_table)
        
        # Add page break for back page
        elements.append(PageBreak())
        
        # Back page - Grading Key
        elements.append(Spacer(1, 0.3*inch))
        
        # Add logo on back page
        if os.path.exists(logo_path):
            try:
                back_logo = Image(logo_path, width=0.8*inch, height=0.8*inch)
                elements.append(back_logo)
                elements.append(Spacer(1, 0.2*inch))
            except:
                pass
        
        # Key: Grading heading
        key_title_style = ParagraphStyle(
            'KeyTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD", key_title_style))
        elements.append(Paragraph("KEY TO GRADES and QUALIFICATIONS AWARD", key_title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Theory and Practical scores table
        grading_header_style = ParagraphStyle(
            'GradingHeader',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )
        
        # Combined table with Theory and Practical side by side
        grading_data = [
            [Paragraph("<b>THEORY SCORES</b>", grading_header_style), "", 
             Paragraph("<b>PRACTICAL SCORES</b>", grading_header_style), ""],
            ["Grade", "Scores%", "Grade", "Scores%"],
            ["A+", "85-100", "A+", "90-100"],
            ["A", "80-84", "A", "85-89"],
            ["B", "70-79", "B+", "75-84"],
            ["B-", "60-69", "B", "65-74"],
            ["C", "50-59", "B-", "60-64"],
            ["C-", "40-49", "C", "55-59"],
            ["D", "30-39", "C-", "50-54"],
            ["E", "0-29", "D", "40-49"],
            ["", "", "D-", "30-39"],
            ["", "", "E", "0-29"],
        ]
        
        grading_table = Table(grading_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        grading_table.setStyle(TableStyle([
            # Header row spanning
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (2, 0), (3, 0)),
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#d3d3d3')),
            ('BACKGROUND', (2, 0), (3, 0), colors.HexColor('#d3d3d3')),
            # Column headers
            ('BACKGROUND', (0, 1), (1, 1), colors.white),
            ('BACKGROUND', (2, 1), (3, 1), colors.white),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            # All cells
            ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(grading_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Pass mark note
        pass_mark_style = ParagraphStyle(
            'PassMark',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=20
        )
        elements.append(Paragraph("Pass mark is 50% in theory and 65% in practical assessment", pass_mark_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Key Acronyms section
        acronym_heading_style = ParagraphStyle(
            'AcronymHeading',
            parent=styles['Heading3'],
            fontSize=12,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            spaceAfter=10
        )
        elements.append(Paragraph("KEY ACRONYMS:", acronym_heading_style))
        
        acronym_style = ParagraphStyle(
            'Acronym',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            alignment=TA_LEFT,
            spaceAfter=4,
            leftIndent=20
        )
        
        acronyms = [
            "• <b>Ms</b> - Missing",
        ]
        
        for acronym in acronyms:
            elements.append(Paragraph(acronym, acronym_style))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Footer copyright
        copyright_style = ParagraphStyle(
            'Copyright',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
            alignment=TA_CENTER,
            textColor=colors.black
        )
        
        elements.append(Paragraph(
            '© 2025 Uganda Vocational and Technical Assessments Board, P.O.Box 1499 Kampala - Uganda',
            copyright_style
        ))
        elements.append(Paragraph(
            '"Setting Pace for Quality Assessment"',
            ParagraphStyle('Slogan', parent=copyright_style, fontName='Helvetica-Oblique')
        ))
        
        # Build PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = HttpResponse(content_type='application/pdf')
        filename = f"Verifiedresults_{candidate.full_name.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf)
        
        return response

    @action(detail=False, methods=['get'], url_path='transcript-pdf')
    def transcript_pdf(self, request):
        """Generate official transcript PDF for Workers PAS candidate"""
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm, inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, Frame, PageTemplate, NextPageTemplate
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from io import BytesIO
        from datetime import datetime
        from django.conf import settings
        import os
        
        candidate_id = request.query_params.get('candidate_id')
        
        if not candidate_id:
            return Response(
                {'error': 'candidate_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Define Page Templates for mixed orientation
        def onFirstPage(canvas, doc):
            canvas.saveState()
            # Signature at absolute bottom
            signature_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'es_signature.jpg')
            if os.path.exists(signature_path):
                try:
                    # Draw signature image
                    canvas.drawImage(signature_path, A4[0] - 6*cm, 2*cm, width=4*cm, height=2*cm, mask='auto')
                except:
                    pass
            
            # Draw "EXECUTIVE SECRETARY" text centered under signature
            canvas.setFont("Times-Bold", 10)
            canvas.drawCentredString(A4[0] - 4*cm, 1.8*cm, "EXECUTIVE SECRETARY")
            canvas.restoreState()

        def onLaterPages(canvas, doc):
            pass

        def onPortraitBack(canvas, doc):
            # Rotate content -90 degrees (Clockwise)
            canvas.translate(0, A4[1])
            canvas.rotate(-90)

        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=3*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
        
        # Create Frames
        frame_portrait = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='portrait')
        frame_landscape = Frame(doc.leftMargin, doc.bottomMargin, landscape(A4)[0]-2*doc.leftMargin, landscape(A4)[1]-2*doc.bottomMargin, id='landscape')
        
        doc.addPageTemplates([
            PageTemplate(id='portrait', frames=frame_portrait, onPage=onFirstPage),
            # Landscape content frame on Portrait page with -90 rotation
            PageTemplate(id='portrait_back', frames=frame_landscape, onPage=onPortraitBack, pagesize=A4)
        ])

        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'TranscriptTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.black,
            spaceAfter=20,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        )
        
        info_label_style = ParagraphStyle(
            'InfoLabel',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Times-Bold',
            alignment=TA_LEFT
        )
        
        info_value_style = ParagraphStyle(
            'InfoValue',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Times-Roman',
            alignment=TA_LEFT
        )

        section_heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=10,
            spaceBefore=15,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        )

        # Content - Page 1
        elements.append(Spacer(1, 9*cm))
        elements.append(Paragraph("TRANSCRIPT", title_style))
        elements.append(Spacer(1, 0.5*cm))

        # Candidate Info
        candidate_photo = None
        if candidate.passport_photo:
            photo_path = os.path.join(settings.MEDIA_ROOT, str(candidate.passport_photo))
            if os.path.exists(photo_path):
                try:
                    from PIL import Image as PILImage
                    from PIL import ImageOps
                    pil_image = PILImage.open(photo_path)
                    pil_image = ImageOps.exif_transpose(pil_image)
                    img_buffer = BytesIO()
                    pil_image.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    candidate_photo = Image(img_buffer, width=3.5*cm, height=4.5*cm)
                except Exception as e:
                    print(f"Error loading photo: {e}")
                    candidate_photo = None

        info_data = [
            [Paragraph("NAME:", info_label_style), Paragraph(candidate.full_name or "", info_value_style), 
             Paragraph("NATIONALITY:", info_label_style), Paragraph(candidate.nationality or "Uganda", info_value_style)],
            [Paragraph("REG NO:", info_label_style), Paragraph(candidate.registration_number or "", info_value_style),
             Paragraph("BIRTHDATE:", info_label_style), Paragraph(candidate.date_of_birth.strftime("%d %b, %Y") if candidate.date_of_birth else "", info_value_style)],
            [Paragraph("GENDER:", info_label_style), Paragraph(candidate.gender.capitalize() if candidate.gender else "", info_value_style),
             Paragraph("PRINTDATE:", info_label_style), Paragraph(datetime.now().strftime("%d-%b-%Y"), info_value_style)],
            [Paragraph("CENTER:", info_label_style), Paragraph(candidate.assessment_center.center_name if candidate.assessment_center else "", info_value_style), "", ""],
            [Paragraph("OCCUPATION:", info_label_style), Paragraph(candidate.occupation.occ_name if candidate.occupation else "", info_value_style), "", ""],
        ]

        info_table = Table(info_data, colWidths=[2.5*cm, 6*cm, 3*cm, 4*cm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('SPAN', (1, 3), (3, 3)), # Span center name
            ('SPAN', (1, 4), (3, 4)), # Span occupation
        ]))

        if candidate_photo:
            combined_data = [[candidate_photo, info_table]]
            combined_table = Table(combined_data, colWidths=[4*cm, 14*cm])
            combined_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(combined_table)
        else:
            elements.append(info_table)

        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("ASSESSMENT RESULTS", section_heading_style))
        elements.append(Spacer(1, 0.2*cm))
        
        # Workers PAS Results
        results = WorkersPasResult.objects.filter(candidate=candidate).select_related(
            'level', 'module', 'paper', 'assessment_series'
        ).order_by('level', 'module', 'paper')
        
        if results.exists():
            results_data = [[
                Paragraph("LEVEL", info_label_style),
                Paragraph("MODULE CODE", info_label_style),
                Paragraph("MODULE NAME", info_label_style),
                Paragraph("PAPER", info_label_style),
                Paragraph("GRADE", info_label_style)
            ]]
            
            for result in results:
                results_data.append([
                    Paragraph(result.level.level_name if result.level else "-", info_value_style),
                    Paragraph(result.module.module_code if result.module else "-", info_value_style),
                    Paragraph(result.module.module_name if result.module else "-", info_value_style),
                    Paragraph(result.paper.paper_code if result.paper else "-", info_value_style),
                    Paragraph(result.grade or "-", info_value_style)
                ])
            
            t = Table(results_data, colWidths=[2*cm, 3*cm, 5*cm, 3*cm, 2*cm], repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph("No results found.", info_value_style))
            
        # Footer - Removed (handled in onFirstPage)
        elements.append(Spacer(1, 1*cm))

        # Page Break (Stays Portrait)
        elements.append(NextPageTemplate('portrait_back'))
        elements.append(PageBreak())

        # Page 2 - Header (Logo + Title)
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=1.5*cm, height=1.5*cm)
                elements.append(logo)
                elements.append(Spacer(1, 0.2*cm))
            except:
                pass
        
        elements.append(Paragraph("UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD", ParagraphStyle(
            'Page2Title', parent=styles['Heading1'], fontSize=12, alignment=TA_CENTER, fontName='Times-Bold', spaceAfter=10
        )))

        # Page 2 - Key to Grades
        heading2_style = ParagraphStyle(
            'Heading2Center', 
            parent=styles['Heading2'], 
            alignment=TA_CENTER, 
            fontName='Times-Bold',
            fontSize=16,
            spaceAfter=15
        )
        
        elements.append(Paragraph("KEY TO GRADES and QUALIFICATIONS AWARD", heading2_style))
        elements.append(Spacer(1, 0.5*cm))

        grading_data = [
            [Paragraph("<b>THEORY SCORES</b>", info_label_style), "", 
             Paragraph("<b>PRACTICAL SCORES</b>", info_label_style), ""],
            ["Grade", "Scores%", "Grade", "Scores%"],
            ["A+", "85-100", "A+", "90-100"],
            ["A", "80-84", "A", "85-89"],
            ["B", "70-79", "B+", "75-84"],
            ["B-", "60-69", "B", "65-74"],
            ["C", "50-59", "B-", "60-64"],
            ["C-", "40-49", "C", "55-59"],
            ["D", "30-39", "C-", "50-54"],
            ["E", "0-29", "D", "40-49"],
            ["", "", "D-", "30-39"],
            ["", "", "E", "0-29"],
        ]
        
        grading_table = Table(grading_data, colWidths=[4.2*cm, 4.2*cm, 4.2*cm, 4.2*cm])
        grading_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (2, 0), (3, 0)),
            ('BACKGROUND', (0, 0), (3, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ('FONTNAME', (0, 1), (-1, 1), 'Times-Bold'),
        ]))
        
        elements.append(grading_table)
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph("Pass mark is 50% in theory and 65% in practical assessment", ParagraphStyle('PassMark', parent=styles['Normal'], alignment=TA_CENTER, fontName='Times-Bold', fontSize=12)))

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        filename = f"Transcript_{candidate.full_name.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response.write(pdf)
        
        return response
    
    @action(detail=False, methods=['put'], url_path='update/(?P<result_id>[^/.]+)')
    def update_result(self, request, result_id=None):
        """Update a single Workers PAS result"""
        try:
            result = WorkersPasResult.objects.get(id=result_id)
        except WorkersPasResult.DoesNotExist:
            return Response(
                {'error': 'Result not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update mark and status
        mark = request.data.get('mark')
        result_status = request.data.get('status')
        
        if mark is not None:
            result.mark = mark
        if result_status:
            result.status = result_status
        
        # Update entered_by if user is authenticated
        if request.user and request.user.is_authenticated:
            result.entered_by = request.user
        
        result.save()
        
        serializer = WorkersPasResultSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)
