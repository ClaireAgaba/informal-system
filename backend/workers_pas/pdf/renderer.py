"""
Worker's PAS booklet PDF renderer.

The booklet is rendered at A5 portrait. Page composition is fixed and driven
by the candidate, occupation, levels, and modules supplied by the caller.
"""
from io import BytesIO
from datetime import date

from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame
from reportlab.lib import colors

# A5 portrait dimensions in points
PAGE_W, PAGE_H = A5
MARGIN_X = 12 * mm
MARGIN_Y = 12 * mm

# Palette
GREY_COVER = colors.HexColor('#7d7d7d')
BLACK = colors.black


# -----------------------------------------------------------------------------
# Paragraph styles
# -----------------------------------------------------------------------------

def _styles():
    return {
        'cover_title_lg': ParagraphStyle(
            'cover_title_lg', fontName='Helvetica-Bold', fontSize=22,
            alignment=TA_CENTER, leading=26, textColor=colors.white,
        ),
        'cover_title_md': ParagraphStyle(
            'cover_title_md', fontName='Helvetica-Bold', fontSize=16,
            alignment=TA_CENTER, leading=20, textColor=colors.white,
        ),
        'cover_subtitle': ParagraphStyle(
            'cover_subtitle', fontName='Helvetica', fontSize=10,
            alignment=TA_CENTER, leading=13, textColor=colors.white,
        ),
        'cover_label': ParagraphStyle(
            'cover_label', fontName='Helvetica-Bold', fontSize=11,
            alignment=TA_CENTER, leading=14, textColor=colors.black,
            backColor=colors.white,
        ),
        'h1': ParagraphStyle(
            'h1', fontName='Helvetica-Bold', fontSize=12,
            alignment=TA_CENTER, leading=15,
        ),
        'h2': ParagraphStyle(
            'h2', fontName='Helvetica-Bold', fontSize=11,
            alignment=TA_LEFT, leading=14,
        ),
        'body': ParagraphStyle(
            'body', fontName='Helvetica', fontSize=9.5,
            alignment=TA_LEFT, leading=12,
        ),
        'body_center': ParagraphStyle(
            'body_center', fontName='Helvetica', fontSize=9.5,
            alignment=TA_CENTER, leading=12,
        ),
        'body_italic': ParagraphStyle(
            'body_italic', fontName='Helvetica-Oblique', fontSize=9.5,
            alignment=TA_LEFT, leading=12,
        ),
        'body_italic_center': ParagraphStyle(
            'body_italic_center', fontName='Helvetica-Oblique', fontSize=9.5,
            alignment=TA_CENTER, leading=12,
        ),
        'small': ParagraphStyle(
            'small', fontName='Helvetica', fontSize=8,
            alignment=TA_LEFT, leading=11,
        ),
        'page_number': ParagraphStyle(
            'page_number', fontName='Helvetica', fontSize=9,
            alignment=TA_CENTER, leading=11,
        ),
    }


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def _draw_paragraph(c, html, style, x, y, width, height):
    """Draw a Paragraph into a fixed Frame on the canvas."""
    p = Paragraph(html, style)
    f = Frame(x, y, width, height, leftPadding=0, rightPadding=0,
              topPadding=0, bottomPadding=0, showBoundary=0)
    f.addFromList([p], c)


def _draw_page_number(c, num):
    s = _styles()['page_number']
    _draw_paragraph(c, str(num), s, 0, 8 * mm, PAGE_W, 12)


def _hardcoded_intro_text(occupation_name):
    return (
        f"This Worker&rsquo;s PAS offers employers and employees a structured record of "
        f"the skills the holder has obtained during his or her time working as a "
        f"{occupation_name}.<br/><br/>"
        f"The booklet will accompany the holder through the learning stages of the "
        f"profession, and will document the training which the holder has received with "
        f"the first employer and with any subsequent employers. It may be carried "
        f"forward to new places of work, where the certification of acquired skills "
        f"will be continued.<br/><br/>"
        f"<i>The Worker&rsquo;s PAS for {occupation_name} is recognised and supported by "
        f"the private sector in Uganda</i>"
    )


CERTIFIED_TRAINING_TEXT = (
    "<b>Certified training on the job</b><br/><br/>"
    "This Worker&rsquo;s PAS was designed as a reference document for assessors, "
    "employees and employers. It certifies specific qualifications obtained during "
    "the holder&rsquo;s period of practice.<br/><br/>"
    "<b><i>For the assessor</i></b><br/>"
    "This booklet is a guideline of available skills within the scope of the "
    "occupation, which the assessor will be able to validate and certify.<br/><br/>"
    "<b><i>For the worker</i></b><br/>"
    "This booklet describes the skills and knowledge which the holder has had the "
    "Opportunity to acquire during his or her practical career.<br/><br/>"
    "<b><i>For employers</i></b><br/>"
    "This booklet provides a record of the skills the holder has acquired during "
    "his or her time of training and employment, as well as the level of "
    "proficiency achieved."
)

ACHIEVEMENT_TAIL_TEXT = (
    "The worker will be rated for each skill with one or two achievement levels;<br/>"
    "&bull; <i>Qualified to work with assistance</i><br/>"
    "&bull; <i>Qualified to work independently</i><br/><br/>"
    "With each endorsement, the assessor certifies that the relevant task has been "
    "performed to the occupational standard.<br/><br/>"
    "All skills that may be obtained in the occupation are listed in this booklet. "
    "The achievement of a particular skill will be confirmed by the assessor "
    "through the signing and stamping of the relevant page. Even if all items or "
    "sections are not completed, each confirmation by the assessor should be seen "
    "as a validation of the holder&rsquo;s proficiency in the respective test area."
)

GRADING_ROWS = [
    ('90% - 100%', 'A+'),
    ('85% - 89%', 'A'),
    ('75% - 84%', 'B+'),
    ('65% - 74%', 'B'),
    ('60% - 64%', 'B-'),
    ('55% - 59%', 'C'),
    ('50% - 54%', 'C-'),
    ('40% - 49%', 'D'),
    ('30% - 39%', 'D-'),
    ('Below 29%', 'E'),
]

GRADING_QUALIFICATION_ROWS = [
    ('75% - 100%', 'Qualified to work independently'),
    ('65% - 74%', 'Qualified to work with assistance'),
    ('Below 65%', 'Advised to retrain'),
]

UVTAB_INFO = {
    'name': 'UGANDA VOCATIONAL AND TECHNICAL ASSESSMENT BOARD',
    'address': 'Plot 891, Kigobe Road, Kyambogo Hill',
    'po_box': 'P.O Box 1499 Kampala, Uganda',
    'tel': 'Tel: 0392-002468, 0392-002467',
    'email': 'Email: info@uvtab.go.ug',
    'website': 'Website: www.uvtab.go.ug',
    'vision': 'To be a centre of excellence for competence-based curriculum '
              'development, assessment and certification for a productive '
              'global Workforce.',
    'mission': 'To develop an industry-led TVET curricula, conduct competence-based '
               'assessments, certification and issue awards meeting the needs of '
               'World of Work.',
    'motto': 'Assessment for Employable Skills',
    'core_values': [
        'Transparency and Accountability', 'Teamwork and Collaborations',
        'Quality, and Innovation', 'Professionalism', 'Confidentiality', 'Integrity',
    ],
}


# -----------------------------------------------------------------------------
# Page renderers
# -----------------------------------------------------------------------------

def _draw_cover(c, ctx):
    """Page 1 - Cover."""
    s = _styles()
    # Grey background
    c.setFillColor(GREY_COVER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(BLACK)

    # Coat of arms (try to load)
    coat = ctx.get('coat_of_arms_path')
    if coat:
        try:
            c.drawImage(coat, (PAGE_W - 30 * mm) / 2, PAGE_H - 50 * mm,
                        width=30 * mm, height=30 * mm, mask='auto',
                        preserveAspectRatio=True)
        except Exception:
            pass

    # WORKER'S PAS - Uganda
    _draw_paragraph(
        c, "<u>WORKER&rsquo;S PAS</u> - Uganda", s['cover_title_md'],
        MARGIN_X, PAGE_H - 70 * mm, PAGE_W - 2 * MARGIN_X, 20,
    )
    # Occupation name (large)
    _draw_paragraph(
        c, ctx['occupation_name'], s['cover_title_lg'],
        MARGIN_X, PAGE_H - 90 * mm, PAGE_W - 2 * MARGIN_X, 30,
    )
    # LEVEL I & II
    _draw_paragraph(
        c, ctx['levels_label'], s['cover_subtitle'],
        MARGIN_X, PAGE_H - 100 * mm, PAGE_W - 2 * MARGIN_X, 16,
    )

    # UVTAB logo
    logo = ctx.get('uvtab_logo_path')
    if logo:
        try:
            c.drawImage(logo, (PAGE_W - 30 * mm) / 2, PAGE_H - 135 * mm,
                        width=30 * mm, height=30 * mm, mask='auto',
                        preserveAspectRatio=True)
        except Exception:
            pass

    _draw_paragraph(
        c, "Uganda Vocational and Technical<br/>Assessment Board",
        s['cover_subtitle'],
        MARGIN_X, PAGE_H - 152 * mm, PAGE_W - 2 * MARGIN_X, 28,
    )
    _draw_paragraph(
        c, "<i>Validation of Informally Acquired Skills</i>",
        s['cover_subtitle'],
        MARGIN_X, PAGE_H - 168 * mm, PAGE_W - 2 * MARGIN_X, 14,
    )

    # Book number label - white box near bottom
    label_w, label_h = 70 * mm, 10 * mm
    label_x = (PAGE_W - label_w) / 2
    label_y = 25 * mm
    c.setFillColor(colors.white)
    c.rect(label_x, label_y, label_w, label_h, fill=1, stroke=0)
    c.setFillColor(BLACK)
    _draw_paragraph(
        c, f"<b>{ctx['full_label']}</b>", s['cover_label'],
        label_x, label_y + 1.5 * mm, label_w, label_h - 3 * mm,
    )


def _draw_page2_intro(c, ctx):
    s = _styles()
    # Bordered box
    box_x, box_y = 18 * mm, 35 * mm
    box_w, box_h = PAGE_W - 36 * mm, PAGE_H - 70 * mm
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.5)
    c.rect(box_x, box_y, box_w, box_h, fill=0, stroke=1)
    c.rect(box_x + 1.5 * mm, box_y + 1.5 * mm,
           box_w - 3 * mm, box_h - 3 * mm, fill=0, stroke=1)

    _draw_paragraph(
        c, _hardcoded_intro_text(ctx['occupation_name']),
        s['body_italic_center'],
        box_x + 6 * mm, box_y + 30 * mm,
        box_w - 12 * mm, box_h - 60 * mm,
    )

    _draw_paragraph(
        c,
        "For verification of authenticity of holder, please visit data base at:<br/>"
        "<b>www.uvtab.go.ug</b>",
        s['body_center'],
        box_x + 6 * mm, box_y + 6 * mm,
        box_w - 12 * mm, 20 * mm,
    )

    _draw_page_number(c, 2)


def _draw_page3_biodata(c, ctx):
    s = _styles()

    # Top section: "Worker's PAS issued to:"
    y = PAGE_H - 30 * mm
    _draw_paragraph(
        c, "<b>Worker&rsquo;s PAS issued to:</b>", s['body'],
        MARGIN_X, y, 70 * mm, 12,
    )
    y -= 8 * mm

    # Name (printed on a line)
    _draw_paragraph(
        c, f"<b>{ctx['candidate_name']}</b>", s['body'],
        MARGIN_X, y, 80 * mm, 14,
    )
    c.setLineWidth(0.5)
    c.line(MARGIN_X, y - 1, MARGIN_X + 80 * mm, y - 1)
    y -= 8 * mm

    _draw_paragraph(
        c, f"Date of birth: <u>{ctx['date_of_birth']}</u>", s['body'],
        MARGIN_X, y, 80 * mm, 12,
    )
    y -= 10 * mm

    fields = [
        ('REG No.', ctx.get('reg_no', '')),
        ('GENDER', ctx.get('gender', '')),
        ('CENTRE NAME', ctx.get('centre_name', '')),
        ('OCCUPATION', ctx.get('occupation_name', '')),
        ('NATIONALITY', ctx.get('nationality', '')),
        ('PRINT DATE', ctx.get('print_date', '')),
    ]
    for label, value in fields:
        _draw_paragraph(
            c, f"<b>{label}:</b> {value}", s['body'],
            MARGIN_X, y, 90 * mm, 12,
        )
        y -= 6 * mm

    # Photo placeholder (top right)
    photo_x = PAGE_W - MARGIN_X - 30 * mm
    photo_y = PAGE_H - 70 * mm
    photo_w = photo_h = 30 * mm
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.6)
    c.rect(photo_x, photo_y, photo_w, photo_h, fill=0, stroke=1)
    if ctx.get('photo_path'):
        try:
            c.drawImage(ctx['photo_path'], photo_x, photo_y,
                        width=photo_w, height=photo_h, mask='auto',
                        preserveAspectRatio=True)
        except Exception:
            pass

    # Issued by section
    y -= 4 * mm
    _draw_paragraph(
        c,
        "<b>Worker&rsquo;s PAS issued by</b><br/>"
        "Uganda Vocational and Technical&nbsp;&nbsp;Assessment Board (UVTAB)",
        s['body'],
        MARGIN_X, y - 12 * mm, PAGE_W - 2 * MARGIN_X, 18 * mm,
    )
    y -= 26 * mm

    # Signatures
    sig_w = 55 * mm
    es_x = MARGIN_X
    cp_x = PAGE_W - MARGIN_X - sig_w
    sig_y = y

    if ctx.get('es_signature_path'):
        try:
            c.drawImage(ctx['es_signature_path'], es_x, sig_y,
                        width=sig_w, height=14 * mm, mask='auto',
                        preserveAspectRatio=True)
        except Exception:
            pass
    if ctx.get('cp_signature_path'):
        try:
            c.drawImage(ctx['cp_signature_path'], cp_x, sig_y,
                        width=sig_w, height=14 * mm, mask='auto',
                        preserveAspectRatio=True)
        except Exception:
            pass

    line_y = sig_y - 1
    c.line(es_x, line_y, es_x + sig_w, line_y)
    c.line(cp_x, line_y, cp_x + sig_w, line_y)
    _draw_paragraph(
        c, "<b>Executive Secretary</b>", s['body'],
        es_x, line_y - 6 * mm, sig_w, 12,
    )
    _draw_paragraph(
        c, "<b>Board Chairperson</b>", s['body'],
        cp_x, line_y - 6 * mm, sig_w, 12,
    )

    _draw_paragraph(
        c, "For changes of employer or assessor please see employment history "
           "P.26.",
        s['small'],
        MARGIN_X, line_y - 18 * mm, PAGE_W - 2 * MARGIN_X, 12 * mm,
    )

    _draw_page_number(c, 3)


def _draw_page4_levels(c, ctx):
    """Level descriptions - one paragraph per level."""
    s = _styles()
    y_top = PAGE_H - 25 * mm
    avail_h = y_top - 25 * mm

    # Build the HTML
    parts = ["<b>LEVELS OF COMPETENCE</b><br/><br/>"]
    for lvl in ctx['levels']:
        parts.append(f"<b>{lvl['level_name']}</b><br/>")
        parts.append((lvl.get('level_description') or '').replace('\n', '<br/>'))
        parts.append("<br/><br/>")
    html = ''.join(parts)

    _draw_paragraph(c, html, s['body'],
                    MARGIN_X, 20 * mm, PAGE_W - 2 * MARGIN_X, avail_h)
    _draw_page_number(c, 4)


def _draw_page5_certified(c):
    s = _styles()
    _draw_paragraph(
        c, CERTIFIED_TRAINING_TEXT, s['body'],
        MARGIN_X, 20 * mm, PAGE_W - 2 * MARGIN_X, PAGE_H - 40 * mm,
    )
    _draw_page_number(c, 5)


def _draw_page6_sections(c, ctx):
    s = _styles()
    parts = ["This Worker&rsquo;s PAS has been structured in sections:<br/><br/>"]
    for idx, lvl in enumerate(ctx['levels'], start=1):
        page_ref = lvl.get('section_start_page', '')
        parts.append(
            f"<b>Section {_ordinal(idx)}</b> (p. {page_ref}) - "
            f"<b>COMPETENCE LEVEL {idx}</b><br/>"
        )
        parts.append(
            f"<i>{(lvl.get('competence_description') or '').strip()}</i><br/><br/>"
        )
    parts.append(ACHIEVEMENT_TAIL_TEXT)
    _draw_paragraph(
        c, ''.join(parts), s['body'],
        MARGIN_X, 18 * mm, PAGE_W - 2 * MARGIN_X, PAGE_H - 35 * mm,
    )
    _draw_page_number(c, 6)


def _draw_section_index_page(c, level_idx, level, page_num):
    s = _styles()
    _draw_paragraph(
        c, f"<b>Section {_ordinal(level_idx)}</b>", s['h1'],
        MARGIN_X, PAGE_H - 30 * mm, PAGE_W - 2 * MARGIN_X, 14,
    )
    _draw_paragraph(
        c, f"<b>COMPETENCE LEVEL {level_idx}</b>", s['h1'],
        MARGIN_X, PAGE_H - 38 * mm, PAGE_W - 2 * MARGIN_X, 14,
    )
    _draw_paragraph(
        c, "<i>TEST AREAS</i>", s['h2'],
        MARGIN_X, PAGE_H - 50 * mm, PAGE_W - 2 * MARGIN_X, 14,
    )
    rows = []
    for i, m in enumerate(level['modules'], start=1):
        rows.append(f"&nbsp;&nbsp;{i}.&nbsp;&nbsp;{m['module_name']}")
    _draw_paragraph(
        c, '<br/>'.join(rows), s['body'],
        MARGIN_X, 20 * mm, PAGE_W - 2 * MARGIN_X, PAGE_H - 75 * mm,
    )
    _draw_page_number(c, page_num)


def _draw_test_area_detail(c, area_no, module, page_num):
    s = _styles()
    _draw_paragraph(
        c, f"<b>Test area {area_no}: {module['module_name']}</b>", s['h1'],
        MARGIN_X, PAGE_H - 25 * mm, PAGE_W - 2 * MARGIN_X, 14,
    )
    desc = module.get('wp_description') or (
        f"The Worker has acquired adequate knowledge and skills to perform "
        f"{module['module_name']}.")
    items = [i.strip() for i in (module.get('wp_competence_items') or '').splitlines() if i.strip()]
    bullet_html = ''.join(f"&bull;&nbsp;{item}<br/>" for item in items)
    _draw_paragraph(
        c, f"{desc}<br/><br/>{bullet_html}", s['body'],
        MARGIN_X, 20 * mm, PAGE_W - 2 * MARGIN_X, PAGE_H - 45 * mm,
    )
    _draw_page_number(c, page_num)


def _draw_achievement_stamp(c, page_num):
    s = _styles()
    y_top = PAGE_H - 35 * mm
    _draw_paragraph(
        c, "<i>ACHIEVEMENT LEVEL</i>", s['h2'],
        MARGIN_X, y_top, 70 * mm, 14,
    )
    _draw_paragraph(
        c, "<i>STAMP</i>", s['h2'],
        PAGE_W - MARGIN_X - 30 * mm, y_top, 30 * mm, 14,
    )

    rows = [
        ('Qualified to work independently', 'Assessment Period'),
        ('Qualified to work with assistance', 'Assessment Period'),
    ]
    y = y_top - 15 * mm
    for line1, line2 in rows:
        _draw_paragraph(c, line1, s['body'],
                        MARGIN_X, y, 80 * mm, 12)
        c.setLineWidth(0.4)
        c.line(MARGIN_X + 60 * mm, y - 1, PAGE_W - MARGIN_X - 35 * mm, y - 1)
        y -= 8 * mm
        _draw_paragraph(c, line2, s['body'],
                        MARGIN_X, y, 80 * mm, 12)
        c.line(MARGIN_X + 35 * mm, y - 1, PAGE_W - MARGIN_X - 35 * mm, y - 1)
        y -= 14 * mm
    # Horizontal divider line
    c.setLineWidth(0.6)
    c.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)
    _draw_page_number(c, page_num)


def _draw_grading(c, page_num):
    s = _styles()
    _draw_paragraph(
        c, "<b>Grading of Scores:</b>", s['h2'],
        MARGIN_X, PAGE_H - 25 * mm, PAGE_W - 2 * MARGIN_X, 14,
    )
    rows = ["<b>Score&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Grade</b>"]
    for score, grade in GRADING_ROWS:
        rows.append(f"{score}&nbsp;&nbsp;&nbsp;&nbsp;{grade}")
    _draw_paragraph(
        c, '<br/>'.join(rows), s['body'],
        MARGIN_X, PAGE_H - 95 * mm, 60 * mm, 60 * mm,
    )

    qual_lines = []
    for score, qual in GRADING_QUALIFICATION_ROWS:
        qual_lines.append(f"{score} &nbsp;-&nbsp; {qual}")
    _draw_paragraph(
        c, '<br/><br/>'.join(qual_lines), s['body'],
        MARGIN_X, PAGE_H - 130 * mm, PAGE_W - 2 * MARGIN_X, 30 * mm,
    )
    _draw_page_number(c, page_num)


def _draw_employment_history(c, page_num, rows_per_page=5, page_index=0):
    s = _styles()
    if page_index == 0:
        _draw_paragraph(
            c, "<b>Employment History</b>", s['h2'],
            MARGIN_X, PAGE_H - 22 * mm, 80 * mm, 14,
        )
        _draw_paragraph(
            c, "<i>STAMP</i>", s['h2'],
            PAGE_W - MARGIN_X - 25 * mm, PAGE_H - 22 * mm, 25 * mm, 14,
        )

    y = PAGE_H - 30 * mm
    box_h = (y - 25 * mm) / rows_per_page

    for _ in range(rows_per_page):
        # outer divider
        c.setLineWidth(0.5)
        c.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)
        # row content
        labels = [
            "Company/Employer:",
            "Contact (Tel. Email etc.):",
            "Starting date:           Finishing date:",
            "Authorised assessor:",
            "Position with firm:           Name/Signature:",
        ]
        ly = y - 5 * mm
        for lbl in labels:
            _draw_paragraph(c, lbl, s['small'],
                            MARGIN_X + 1 * mm, ly, PAGE_W - 2 * MARGIN_X - 22 * mm, 10)
            ly -= 4.5 * mm
        # stamp box (right)
        sx = PAGE_W - MARGIN_X - 18 * mm
        sy = y - box_h + 3 * mm
        c.setDash(2, 2)
        c.rect(sx, sy, 16 * mm, box_h - 6 * mm, stroke=1, fill=0)
        c.setDash()
        y -= box_h
    c.setLineWidth(0.5)
    c.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)
    _draw_page_number(c, page_num)


def _draw_back_cover(c):
    s = _styles()
    logo = None  # back of front cover (UVTAB info) - hardcoded text
    y = PAGE_H - 30 * mm
    _draw_paragraph(
        c, f"<b>{UVTAB_INFO['name']}</b>", s['body_center'],
        MARGIN_X, y, PAGE_W - 2 * MARGIN_X, 14,
    )
    y -= 8 * mm
    info_lines = [
        UVTAB_INFO['address'], UVTAB_INFO['po_box'], UVTAB_INFO['tel'],
        UVTAB_INFO['email'], UVTAB_INFO['website'],
    ]
    _draw_paragraph(
        c, '<br/>'.join(info_lines), s['body_center'],
        MARGIN_X, y - 25 * mm, PAGE_W - 2 * MARGIN_X, 25 * mm,
    )
    y -= 32 * mm

    blocks = [
        ('Vision', UVTAB_INFO['vision']),
        ('Mission', UVTAB_INFO['mission']),
        ('Motto', UVTAB_INFO['motto']),
    ]
    for title, body in blocks:
        _draw_paragraph(
            c, f"<b>{title}</b><br/>{body}", s['body_center'],
            MARGIN_X, y - 16 * mm, PAGE_W - 2 * MARGIN_X, 16 * mm,
        )
        y -= 20 * mm
    _draw_paragraph(
        c, "<b>Core Values</b><br/>" + '<br/>'.join(UVTAB_INFO['core_values']),
        s['body_center'],
        MARGIN_X, 20 * mm, PAGE_W - 2 * MARGIN_X, y - 20 * mm,
    )


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

_ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
_ENGLISH = ['', 'One', 'Two', 'Three', 'Four', 'Five',
            'Six', 'Seven', 'Eight', 'Nine', 'Ten']


def _ordinal(n):
    if 0 < n < len(_ENGLISH):
        return _ENGLISH[n]
    return str(n)


def _roman(n):
    if 0 < n < len(_ROMAN):
        return _ROMAN[n]
    return str(n)


def _build_levels_label(levels):
    if not levels:
        return ''
    if len(levels) == 1:
        return f"LEVEL {_roman(1)}"
    return "LEVEL " + ' &amp; '.join(_roman(i) for i in range(1, len(levels) + 1))


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

def generate_book_pdf(book_data):
    """
    Generate the full A5 booklet PDF for a single candidate.

    ``book_data`` is a dict with the following keys:
      candidate_name, date_of_birth, gender, reg_no, centre_name, nationality,
      print_date, photo_path,
      occupation_name, occupation_wp_code, full_label,
      levels: [{level_name, level_description, competence_description,
                modules: [{module_name, wp_description, wp_competence_items}, ...]}, ...],
      es_signature_path, cp_signature_path,
      coat_of_arms_path, uvtab_logo_path,
      employment_history_pages: int (default 4 -> 20 rows at 5/page)
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A5)
    c.setTitle(f"Worker's PAS - {book_data.get('candidate_name', '')}")

    # Pre-compute section start pages so the table-of-sections on page 6 is correct.
    page_num = 6  # sections page itself
    levels = list(book_data['levels'])
    page_cursor = 7  # first content page after sections page
    for lvl in levels:
        lvl['section_start_page'] = page_cursor
        # Section index page + 2 pages per module (detail + achievement/stamp)
        page_cursor += 1 + 2 * len(lvl.get('modules', []))

    book_data['levels_label'] = _build_levels_label(levels)

    # Page 1 - Cover
    _draw_cover(c, book_data)
    c.showPage()

    # Page 2 - Intro
    _draw_page2_intro(c, book_data)
    c.showPage()

    # Page 3 - Biodata
    _draw_page3_biodata(c, book_data)
    c.showPage()

    # Page 4 - Levels
    _draw_page4_levels(c, book_data)
    c.showPage()

    # Page 5 - Certified training
    _draw_page5_certified(c)
    c.showPage()

    # Page 6 - Sections list
    _draw_page6_sections(c, book_data)
    c.showPage()

    # Sections (per level)
    current_page = 7
    for level_idx, lvl in enumerate(levels, start=1):
        _draw_section_index_page(c, level_idx, lvl, current_page)
        c.showPage()
        current_page += 1

        for area_no, module in enumerate(lvl.get('modules', []), start=1):
            _draw_test_area_detail(c, area_no, module, current_page)
            c.showPage()
            current_page += 1
            _draw_achievement_stamp(c, current_page)
            c.showPage()
            current_page += 1

    # Grading
    _draw_grading(c, current_page)
    c.showPage()
    current_page += 1

    # Employment history (split across multiple pages)
    rows_per_page = 5
    eh_pages = max(1, book_data.get('employment_history_pages', 4))
    for i in range(eh_pages):
        _draw_employment_history(c, current_page, rows_per_page=rows_per_page,
                                 page_index=i)
        c.showPage()
        current_page += 1

    # Back cover (UVTAB info)
    _draw_back_cover(c)
    c.showPage()

    c.save()
    return buf.getvalue()
