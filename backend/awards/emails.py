import logging
import os
import threading
from io import BytesIO

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
)

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)

DESIGNATION_LABELS = {
    'head_teacher': 'Head Teacher',
    'deputy_head_teacher': 'Deputy Head Teacher',
    'center_administrator': 'Center Administrator',
    'candidate': 'Candidate',
    'other_person': 'Other Person',
}


def _build_receipt_pdf(receipt_data):
    """
    Generate a PDF receipt matching the printed receipt layout.
    Returns a BytesIO buffer containing the PDF.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=1 * cm, bottomMargin=1 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    elements = []

    # -- Styles --
    title_style = ParagraphStyle(
        'ReceiptTitle', parent=styles['Normal'],
        fontSize=14, fontName='Times-Bold',
        alignment=TA_CENTER, spaceAfter=4,
        textColor=colors.HexColor('#1a237e'),
    )
    subtitle_style = ParagraphStyle(
        'ReceiptSubtitle', parent=styles['Normal'],
        fontSize=12, fontName='Times-Bold',
        alignment=TA_CENTER, spaceAfter=6,
        textColor=colors.HexColor('#1a237e'),
    )
    small_style = ParagraphStyle(
        'Small', parent=styles['Normal'],
        fontSize=9, fontName='Times-Roman', leading=13,
    )
    label_style = ParagraphStyle(
        'Label', parent=styles['Normal'],
        fontSize=10, fontName='Times-Bold', textColor=colors.HexColor('#555555'),
    )
    value_style = ParagraphStyle(
        'Value', parent=styles['Normal'],
        fontSize=10, fontName='Times-Roman',
    )
    section_title = ParagraphStyle(
        'SectionTitle', parent=styles['Normal'],
        fontSize=12, fontName='Times-Bold', spaceAfter=4,
    )

    # -- Header with logo --
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'uvtab-logo.png')
    logo = None
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=0.7 * inch, height=0.7 * inch)
        except Exception:
            logo = None

    left_addr = Paragraph(
        "Address: P.O.Box 1499,<br/>Kampala,<br/>Email: info@uvtab.go.ug",
        ParagraphStyle('ha', parent=small_style, alignment=TA_RIGHT),
    )
    right_addr = Paragraph(
        "Tel: 0392002468",
        ParagraphStyle('hb', parent=small_style, alignment=TA_LEFT),
    )

    if logo:
        header_data = [[left_addr, logo, right_addr]]
        header_widths = [5.5 * cm, 2.5 * cm, 5.5 * cm]
    else:
        header_data = [[left_addr, right_addr]]
        header_widths = [7 * cm, 7 * cm]

    elements.append(Paragraph("UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD", title_style))
    elements.append(Spacer(1, 0.1 * inch))

    header_table = Table(header_data, colWidths=header_widths)
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.05 * inch))

    # Divider line
    divider = Table([['']], colWidths=[doc.width])
    divider.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1a237e')),
    ]))
    elements.append(divider)
    elements.append(Spacer(1, 0.15 * inch))

    elements.append(Paragraph("Transcript Collection Receipt", subtitle_style))
    elements.append(Spacer(1, 0.15 * inch))

    # -- Info grid (2-column layout) --
    designation_display = DESIGNATION_LABELS.get(
        receipt_data['designation'], receipt_data['designation']
    )
    info_items = [
        ('Reference:', receipt_data['receipt_number']),
        ('Collection Date:', receipt_data['collection_date']),
        ('Collector Name:', receipt_data['collector_name']),
        ('Center:', receipt_data['center_name']),
        ('NIN:', receipt_data['nin']),
        ('Candidates:', str(receipt_data['candidate_count'])),
        ('Designation:', designation_display),
        ('Phone:', receipt_data['collector_phone']),
        ('Email:', receipt_data.get('email', '')),
    ]

    info_rows = []
    for i in range(0, len(info_items), 2):
        row = []
        for j in range(2):
            if i + j < len(info_items):
                lbl, val = info_items[i + j]
                row.append(Paragraph(f"<b>{lbl}</b>", label_style))
                row.append(Paragraph(val or '-', value_style))
            else:
                row.extend(['', ''])
        info_rows.append(row)

    col_w = doc.width / 4
    info_table = Table(info_rows, colWidths=[col_w * 0.8, col_w * 1.2, col_w * 0.8, col_w * 1.2])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#eeeeee')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.2 * inch))

    # -- Candidates table --
    elements.append(Paragraph(f"Candidates ({receipt_data['candidate_count']})", section_title))
    elements.append(Spacer(1, 0.05 * inch))

    table_header = [
        Paragraph('<b>#</b>', ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName='Times-Bold')),
        Paragraph('<b>Reg No</b>', ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName='Times-Bold')),
        Paragraph('<b>Name</b>', ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName='Times-Bold')),
        Paragraph('<b>TR SNo</b>', ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName='Times-Bold')),
    ]
    table_data = [table_header]
    for i, c in enumerate(receipt_data['candidates'], 1):
        table_data.append([
            str(i),
            c.get('registration_number') or '-',
            c.get('full_name') or '-',
            c.get('tr_sno') or '-',
        ])

    cand_table = Table(table_data, colWidths=[0.6 * cm, 4.5 * cm, 7 * cm, 4 * cm])
    cand_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ]))
    elements.append(cand_table)
    elements.append(Spacer(1, 0.3 * inch))

    # -- Signature section --
    sig_data = [[
        Paragraph('_' * 35 + '<br/><font size="9" color="#666666">Collector Signature</font>', 
                  ParagraphStyle('sig', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)),
        Paragraph('_' * 35 + '<br/><font size="9" color="#666666">Authorized Officer</font>',
                  ParagraphStyle('sig', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)),
    ]]
    sig_table = Table(sig_data, colWidths=[doc.width / 2, doc.width / 2])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 0.2 * inch))

    # -- Official / Issued By --
    divider2 = Table([['']], colWidths=[doc.width])
    divider2.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.HexColor('#dddddd')),
    ]))
    elements.append(divider2)
    elements.append(Spacer(1, 0.1 * inch))

    issued_by = receipt_data.get('issued_by', 'UVTAB Staff')
    elements.append(Paragraph('<i><b>Official</b></i>', ParagraphStyle(
        'off', parent=styles['Normal'], fontSize=11, fontName='Times-BoldItalic',
    )))
    elements.append(Paragraph(f'Issued By: <b><i>{issued_by}</i></b>', ParagraphStyle(
        'ib', parent=styles['Normal'], fontSize=10, fontName='Times-Roman',
    )))
    elements.append(Spacer(1, 0.15 * inch))

    # -- QR Code --
    try:
        qr_text = (
            f"Collection Reference: {receipt_data['receipt_number']}\n"
            f"Collector Name: {receipt_data['collector_name']}\n"
            f"Center: {receipt_data['center_name']}\n"
            f"Collection Date: {receipt_data['collection_date']}\n"
            f"Designation: {receipt_data['designation']}"
        )
        qr_img = qrcode.make(qr_text, box_size=4, border=1)
        qr_buf = BytesIO()
        qr_img.save(qr_buf, format='PNG')
        qr_buf.seek(0)

        qr_table = Table(
            [[Image(qr_buf, width=1.2 * inch, height=1.2 * inch)]],
            colWidths=[doc.width],
        )
        qr_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
        elements.append(qr_table)
    except Exception as e:
        logger.warning(f"QR code generation failed: {e}")

    doc.build(elements)
    buf.seek(0)
    return buf


def send_collection_receipt_email(receipt_data, recipient_email):
    """
    Send the transcript collection receipt as a PDF attachment.
    Runs in a background thread so it doesn't block the API response.
    """
    def _send():
        try:
            receipt_number = receipt_data['receipt_number']
            subject = f"Transcript Collection Receipt - {receipt_number}"
            body = (
                f"Dear {receipt_data['collector_name']},\n\n"
                f"Please find attached your transcript collection receipt ({receipt_number}).\n\n"
                f"Center: {receipt_data['center_name']}\n"
                f"Collection Date: {receipt_data['collection_date']}\n"
                f"Candidates Collected: {receipt_data['candidate_count']}\n\n"
                f"This is an official receipt from UVTAB EMIS.\n"
                f"For any inquiries, contact us at 0392002468.\n\n"
                f"Regards,\nUVTAB EMIS"
            )

            pdf_buffer = _build_receipt_pdf(receipt_data)
            filename = f"Collection_Receipt_{receipt_number}.pdf"

            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            email.attach(filename, pdf_buffer.getvalue(), 'application/pdf')
            email.send(fail_silently=False)

            logger.info(f"Receipt PDF emailed to {recipient_email} for {receipt_number}")

        except Exception as e:
            logger.error(f"Failed to send receipt email to {recipient_email}: {e}")

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
