"""
Worker's PAS booklet PDF renderer.

The booklet is rendered at passport/pocket size (100 × 133.5 mm). When imposed
2-up on A4 and cut along the guide lines, two pocket-sized booklets are
produced per A4 sheet.
"""
import re
from io import BytesIO
from datetime import date

import qrcode
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.utils import ImageReader
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, Flowable, PageTemplate,
    Paragraph, Spacer, PageBreak, NextPageTemplate, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors

from .constants import BOOKLET_W, BOOKLET_H

# Passport-sized booklet page
PAGE_W, PAGE_H = BOOKLET_W, BOOKLET_H
MARGIN_X = 12 * mm
MARGIN_Y = 20 * mm        # bottom content margin
TOP_MARGIN = 24 * mm      # top safe zone (content starts ≥24 mm from top edge)

# Palette
DEFAULT_COVER_COLOR = '#7d7d7d'
GREY_COVER = colors.HexColor(DEFAULT_COVER_COLOR)  # legacy default
BLACK = colors.black


def _resolve_cover_color(book_data):
    """Return a reportlab Color for the booklet cover.

    Accepts ``book_data['cover_color']`` as a hex string ('#RRGGBB' or
    'RRGGBB'); falls back to the default grey if missing/invalid.
    """
    raw = (book_data or {}).get('cover_color') or DEFAULT_COVER_COLOR
    raw = raw.strip()
    if not raw.startswith('#'):
        raw = '#' + raw
    try:
        return colors.HexColor(raw)
    except Exception:
        return colors.HexColor(DEFAULT_COVER_COLOR)


# -----------------------------------------------------------------------------
# Paragraph styles
# -----------------------------------------------------------------------------

def _styles():
    return {
        'cover_title_xl': ParagraphStyle(
            'cover_title_xl', fontName='Helvetica-Bold', fontSize=17,
            alignment=TA_CENTER, leading=20, textColor=colors.white,
        ),
        'cover_title_lg': ParagraphStyle(
            'cover_title_lg', fontName='Helvetica-Bold', fontSize=15,
            alignment=TA_CENTER, leading=18, textColor=colors.white,
        ),
        'cover_title_md': ParagraphStyle(
            'cover_title_md', fontName='Helvetica-Bold', fontSize=12,
            alignment=TA_CENTER, leading=15, textColor=colors.white,
        ),
        'cover_subtitle': ParagraphStyle(
            'cover_subtitle', fontName='Helvetica', fontSize=9,
            alignment=TA_CENTER, leading=11, textColor=colors.white,
        ),
        'cover_label': ParagraphStyle(
            'cover_label', fontName='Helvetica-Bold', fontSize=11.5,
            alignment=TA_CENTER, leading=14, textColor=colors.black,
        ),
        'h1': ParagraphStyle(
            'h1', fontName='Helvetica-Bold', fontSize=9,
            alignment=TA_CENTER, leading=11,
        ),
        'h2': ParagraphStyle(
            'h2', fontName='Helvetica-Bold', fontSize=8,
            alignment=TA_LEFT, leading=10,
        ),
        'body': ParagraphStyle(
            'body', fontName='Helvetica', fontSize=7.5,
            alignment=TA_LEFT, leading=9,
        ),
        'body_center': ParagraphStyle(
            'body_center', fontName='Helvetica', fontSize=7.5,
            alignment=TA_CENTER, leading=9,
        ),
        'body_italic': ParagraphStyle(
            'body_italic', fontName='Helvetica-Oblique', fontSize=7.5,
            alignment=TA_LEFT, leading=9,
        ),
        'body_italic_center': ParagraphStyle(
            'body_italic_center', fontName='Helvetica-Oblique', fontSize=7.5,
            alignment=TA_CENTER, leading=9,
        ),
        'body_justify': ParagraphStyle(
            'body_justify', fontName='Helvetica', fontSize=7.5,
            alignment=TA_JUSTIFY, leading=9,
        ),
        'h1_center': ParagraphStyle(
            'h1_center', fontName='Helvetica-Bold', fontSize=9,
            alignment=TA_CENTER, leading=11,
        ),
        'h2_center': ParagraphStyle(
            'h2_center', fontName='Helvetica-Bold', fontSize=8,
            alignment=TA_CENTER, leading=10,
        ),
        'small': ParagraphStyle(
            'small', fontName='Helvetica', fontSize=6.5,
            alignment=TA_LEFT, leading=8,
        ),
        'small_center': ParagraphStyle(
            'small_center', fontName='Helvetica', fontSize=6.5,
            alignment=TA_CENTER, leading=8,
        ),
        'page_number': ParagraphStyle(
            'page_number', fontName='Helvetica', fontSize=7,
            alignment=TA_CENTER, leading=9,
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


def _draw_transparent_image(c, path, x, y, width, height, bg_color=None):
    """Draw an image preserving its true 8-bit alpha channel by compositing over the background color."""
    try:
        img = Image.open(path)
        
        # Fallback to mask='auto' for images without an alpha channel
        if img.mode not in ('RGBA', 'LA', 'P') or (img.mode == 'P' and 'transparency' not in img.info):
            c.drawImage(path, x, y, width=width, height=height, preserveAspectRatio=True, mask='auto')
            return

        # Image has an alpha channel. Composite it over the target background color for perfect blending.
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        if bg_color is None:
            bg_color = colors.white
            
        bg_rgb = (int(bg_color.red * 255), int(bg_color.green * 255), int(bg_color.blue * 255), 255)
        bg = Image.new('RGBA', img.size, bg_rgb)
        
        composited = Image.alpha_composite(bg, img)
        c.drawImage(ImageReader(composited.convert('RGB')), x, y, width=width, height=height, preserveAspectRatio=True)
    except Exception as e:
        print(f"Error drawing composite image: {e}")




def _draw_page_number(c, num):
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(BLACK)
    label_y = PAGE_H - TOP_MARGIN - 4 * mm
    # Draw right-aligned at the right margin, visually aligned with the header text
    c.drawRightString(PAGE_W - MARGIN_X, label_y + 4, str(num))


def _draw_page_header(c, occupation_name):
    """Top-of-page header: occupation name + horizontal line.

    Drawn on every interior page (not on the front cover, not on trailing
    blank). Content should start below ``HEADER_BOTTOM_Y`` to avoid overlap.
    """
    s = _styles()
    label_y = PAGE_H - TOP_MARGIN - 4 * mm   # label top ≈ TOP_MARGIN from page top
    _draw_paragraph(
        c, f"<b>{occupation_name}</b>", s['body'],
        MARGIN_X, label_y, PAGE_W - 2 * MARGIN_X, 12,
    )
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.5)
    c.line(MARGIN_X, label_y - 2, PAGE_W - MARGIN_X, label_y - 2)


# Y below which body content should start so it does not overlap the header.
HEADER_BOTTOM_Y = PAGE_H - TOP_MARGIN - 6 * mm


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
    """Page 1 - Cover (100 × 133.5 mm passport-sized layout).

    All y-coordinates are absolute from page bottom to avoid cascade drift.
    Layout (bottom → top, ~4-5 mm gaps):
      book label (4 mm), validation (14 mm), logo (24 mm),
      issued-by (49 mm), level (59 mm), occupation (68 mm),
      title (90 mm), coat (100.5 mm).
    """
    s = _styles()
    c.setFillColor(_resolve_cover_color(ctx))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(BLACK)

    coat_w = 54 * mm
    coat_h = 29 * mm
    logo_w = 34 * mm
    logo_h = 30 * mm
    
    cover_bg = _resolve_cover_color(ctx)

    # Coat of arms
    coat = ctx.get('coat_of_arms_path')
    if coat:
        _draw_transparent_image(c, coat, (PAGE_W - coat_w) / 2,
                                94 * mm, coat_w, coat_h, bg_color=cover_bg)

    # Dynamic layout for the text block to eliminate extra spaces
    p_title = Paragraph("<u>Worker&rsquo;s PAS</u> - Uganda", s['cover_title_xl'])
    w_title, h_title = p_title.wrap(PAGE_W - 2 * MARGIN_X, PAGE_H)

    p_occ = Paragraph(ctx['occupation_name'], s['cover_title_lg'])
    w_occ, h_occ = p_occ.wrap(PAGE_W - 2 * MARGIN_X, PAGE_H)

    p_lvl = Paragraph(ctx['levels_label'], s['cover_subtitle'])
    w_lvl, h_lvl = p_lvl.wrap(PAGE_W - 2 * MARGIN_X, PAGE_H)

    p_iss = Paragraph("<b>Issued by:</b>", s['cover_subtitle'])
    w_iss, h_iss = p_iss.wrap(PAGE_W - 2 * MARGIN_X, PAGE_H)

    gap1, gap2, gap3 = 1.5 * mm, 2 * mm, 1.5 * mm

    # Anchor the text block directly below the Coat of Arms (no break lines)
    current_y = 94 * mm

    p_title.drawOn(c, MARGIN_X, current_y - h_title)
    current_y -= h_title + gap1

    p_occ.drawOn(c, MARGIN_X, current_y - h_occ)
    current_y -= h_occ + gap2

    p_lvl.drawOn(c, MARGIN_X, current_y - h_lvl)
    current_y -= h_lvl + gap3

    p_iss.drawOn(c, MARGIN_X, current_y - h_iss)

    # UVTAB logo
    logo = ctx.get('uvtab_logo_path')
    if logo:
        _draw_transparent_image(c, logo, (PAGE_W - logo_w) / 2,
                                26 * mm, logo_w, logo_h, bg_color=cover_bg)

    # Validation tagline
    _draw_paragraph(
        c,
        "<i>Validation of Non-formal and Informally Acquired Skills</i>",
        s['cover_subtitle'],
        MARGIN_X, 22 * mm, PAGE_W - 2 * MARGIN_X, 4 * mm,
    )

    # Book number label
    label_w, label_h = 65 * mm, 9 * mm
    label_x = (PAGE_W - label_w) / 2
    c.setFillColor(colors.white)
    c.rect(label_x, 11.5 * mm, label_w, label_h, fill=1, stroke=0)
    c.setFillColor(BLACK)
    
    # Nudge the frame's top edge down to properly vertically center the text
    _draw_paragraph(
        c, f"<b>{ctx['full_label']}</b>", s['cover_label'],
        label_x, 11.5 * mm, label_w, 7.5 * mm,
    )


def _draw_page2_intro(c, ctx):
    s = _styles()
    _draw_page_header(c, ctx['occupation_name'])
    box_x, box_y = 12 * mm, 14 * mm
    box_w, box_h = PAGE_W - 24 * mm, HEADER_BOTTOM_Y - box_y
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.5)
    c.rect(box_x, box_y, box_w, box_h, fill=0, stroke=1)
    c.rect(box_x + 1 * mm, box_y + 1 * mm,
           box_w - 2 * mm, box_h - 2 * mm, fill=0, stroke=1)

    _draw_paragraph(
        c, _hardcoded_intro_text(ctx['occupation_name']),
        s['body_italic_center'],
        box_x + 3 * mm, box_y + 16 * mm,
        box_w - 6 * mm, box_h - 28 * mm,
    )

    _draw_paragraph(
        c,
        "For verification of authenticity of holder, please visit data base at:<br/>"
        "<b>www.uvtab.go.ug</b>",
        s['body_center'],
        box_x + 3 * mm, box_y + 3 * mm,
        box_w - 6 * mm, 13 * mm,
    )

    _draw_page_number(c, 2)


def _draw_page3_biodata(c, ctx):
    s = _styles()
    _draw_page_header(c, ctx['occupation_name'])

    y = HEADER_BOTTOM_Y - 5 * mm
    _draw_paragraph(
        c, "<b>Worker&rsquo;s PAS issued to:</b>", s['body'],
        MARGIN_X, y, 60 * mm, 10,
    )
    y -= 7 * mm

    # Photo placeholder (top right, 25x30mm)
    photo_w, photo_h = 25 * mm, 30 * mm
    photo_x = PAGE_W - MARGIN_X - photo_w
    
    # Text column width (leaving a 3mm gap before the photo)
    text_w = photo_x - MARGIN_X - 3 * mm

    # Save the current y so the photo can be perfectly aligned with the "Full names:" row
    # The photo will hang down from this point. We subtract photo_h to get the bottom-left coordinate.
    # Paragraphs are drawn such that `y` is the bottom of the text block. To align the top of the photo 
    # with the top of the text block, we adjust slightly. The text block is 10pt high.
    photo_y = y - photo_h + 10

    _draw_paragraph(
        c, f"<b>Full names:</b> &nbsp;{ctx['candidate_name']}", s['body'],
        MARGIN_X, y, text_w, 10,
    )
    c.setLineWidth(0.5)
    c.line(MARGIN_X, y - 1, MARGIN_X + text_w, y - 1)
    y -= 8 * mm

    _draw_paragraph(
        c, f"<b>Date of birth:</b> &nbsp;<u>{ctx['date_of_birth']}</u>", s['body'],
        MARGIN_X, y, text_w, 10,
    )
    y -= 8 * mm

    fields = [
        ('GENDER', ctx.get('gender', '')),
        ('NATIONALITY', ctx.get('nationality', '')),
        ('PRINT DATE', ctx.get('print_date', '')),
    ]
    for label, value in fields:
        _draw_paragraph(
            c, f"<b>{label}:</b> {value}", s['body'],
            MARGIN_X, y, text_w, 10,
        )
        y -= 6 * mm

    # Draw the photo
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.6)
    c.rect(photo_x, photo_y, photo_w, photo_h, fill=0, stroke=1)
    if ctx.get('photo_path'):
        _draw_transparent_image(c, ctx['photo_path'], photo_x, photo_y,
                                photo_w, photo_h, bg_color=colors.white)

    y -= 3 * mm
    _draw_paragraph(
        c,
        "<b>Worker&rsquo;s PAS issued by</b><br/>"
        "Uganda Vocational and Technical Assessment Board (UVTAB)",
        s['body'],
        MARGIN_X, y - 7 * mm, PAGE_W - 2 * MARGIN_X, 10 * mm,
    )
    y -= 20 * mm

    sig_w = 47 * mm
    es_x = (PAGE_W - sig_w) / 2
    sig_y = y

    if ctx.get('es_signature_path'):
        _draw_transparent_image(c, ctx['es_signature_path'], es_x, sig_y,
                                sig_w, 11 * mm, bg_color=colors.white)

    line_y = sig_y - 1
    c.line(es_x, line_y, es_x + sig_w, line_y)
    _draw_paragraph(
        c, "<b>Executive Secretary</b>", s['body_center'],
        es_x, line_y - 4 * mm, sig_w, 10,
    )

    _draw_paragraph(
        c, "<i>For changes of employer or assessor please see employment history</i>",
        s['small'],
        MARGIN_X, line_y - 11 * mm, PAGE_W - 2 * MARGIN_X, 8 * mm,
    )
    _draw_page_number(c, 3)


def _draw_page4_levels(c, ctx):
    """Levels of competence page.

    Layout:
      <centred heading, 3 lines>
      <centred "Information" sub-heading>
      <justified intro paragraph>

      (a)   Level 1:
            <justified description paragraph>

      (b)   Level 2:
            <justified description paragraph>

    The left column holds the ordered-list marker ("(a)", "(b)", ...) and
    the right column holds the bold label followed by a wrapping description.
    """
    s = _styles()
    _draw_page_header(c, ctx['occupation_name'])

    letters = 'abcdefghijklmnopqrstuvwxyz'
    content_w = PAGE_W - 2 * MARGIN_X

    # Centred heading (three lines)
    heading_h = 14 * mm
    heading_y = HEADER_BOTTOM_Y - heading_h
    _draw_paragraph(
        c,
        "LEVELS OF COMPETENCE ASSESSED AND CERTIFIED<br/>"
        "BY THE UGANDA VOCATIONAL AND TECHNICAL<br/>"
        "ASSESSMENT BOARD (UVTAB)",
        s['h1_center'], MARGIN_X, heading_y, content_w, heading_h,
    )

    # "Information" sub-heading
    sub_y = heading_y - 5 * mm
    _draw_paragraph(
        c, "Information", s['h2_center'],
        MARGIN_X, sub_y, content_w, 10,
    )

    # Intro paragraph
    intro = (
        "The holder of this Worker&rsquo;s PAS has practiced the skills, "
        "as far as they have been certified, on the following levels:"
    )
    intro_p = Paragraph(intro, s['body'])
    _, intro_h = intro_p.wrap(content_w, 25 * mm)
    intro_top = sub_y - 3 * mm
    intro_p.drawOn(c, MARGIN_X, intro_top - intro_h)

    # Ordered-list items
    marker_col_w = 8 * mm
    body_col_x = MARGIN_X + marker_col_w + 2 * mm
    body_col_w = PAGE_W - MARGIN_X - body_col_x

    y_cursor = intro_top - intro_h - 5 * mm
    for idx, lvl in enumerate(ctx['levels']):
        label = f"({letters[idx] if idx < len(letters) else str(idx + 1)})"
        desc = (lvl.get('level_description') or '').replace('\n', '<br/>')

        # Right-column paragraph: bold label + wrapping description.
        html = (
            f"<b>{lvl['level_name']}:</b> &nbsp;{desc}"
        )
        item_p = Paragraph(html, s['body_justify'])
        _, item_h = item_p.wrap(body_col_w, 200 * mm)

        # Draw marker at the top of the right-column paragraph.
        _draw_paragraph(
            c, label, s['body'],
            MARGIN_X, y_cursor - 12, marker_col_w, 14,
        )
        item_p.drawOn(c, body_col_x, y_cursor - item_h)

        y_cursor -= item_h + 4 * mm

    _draw_page_number(c, 4)


def _draw_page5_certified(c, ctx):
    """Certified training on the job.

    Tight flowing layout:
      - Bold heading "Certified training on the job"
      - Justified intro paragraph
      - Three sub-blocks ("For the assessor" / "For the worker" /
        "For employers"), each with a bold-italic title and a justified
        body, slightly indented from the page margin.
    """
    s = _styles()
    _draw_page_header(c, ctx['occupation_name'])

    content_w = PAGE_W - 2 * MARGIN_X
    indent = 3 * mm
    block_w = content_w - indent

    y = HEADER_BOTTOM_Y - 5 * mm

    def _flow(html, style, width, x):
        """Draw a paragraph starting at current ``y`` and advance ``y``."""
        nonlocal y
        p = Paragraph(html, style)
        _, h = p.wrap(width, PAGE_H)
        p.drawOn(c, x, y - h)
        y -= h

    # Main heading
    _flow("<b>Certified training on the job</b>", s['body'], content_w, MARGIN_X)
    y -= 1 * mm

    # Intro paragraph (justified)
    _flow(
        "This Worker&rsquo;s PAS was designed as a reference document for "
        "assessors, employees and employers. It certifies specific "
        "qualifications obtained during the holder&rsquo;s period of practice.",
        s['body_justify'], content_w, MARGIN_X,
    )
    y -= 2 * mm

    blocks = [
        ("For the assessor",
         "This booklet is a guideline of available skills within the scope "
         "of the occupation, which the assessor will be able to validate "
         "and certify."),
        ("For the worker",
         "This booklet describes the skills and knowledge which the holder "
         "has had the Opportunity to acquire during his or her practical "
         "career."),
        ("For employers",
         "This booklet provides a record of the skills the holder has "
         "acquired during his or her time of training and employment, as "
         "well as the level of proficiency achieved."),
    ]
    for title, body in blocks:
        _flow(f"<b><i>{title}</i></b>", s['body'], block_w, MARGIN_X + indent)
        y -= 0.5 * mm
        _flow(body, s['body_justify'], block_w, MARGIN_X + indent)
        y -= 2 * mm

    _draw_page_number(c, 5)


def _draw_page6_sections(c, ctx):
    s = _styles()
    _draw_page_header(c, ctx['occupation_name'])
    parts = ["This Worker&rsquo;s PAS has been structured in sections:<br/><br/>"]
    for idx, lvl in enumerate(ctx['levels'], start=1):
        page_ref = lvl.get('section_start_page', '')
        ref_text = f" (p. {page_ref})" if page_ref else ""
        level_num = _extract_level_number(lvl['level_name']) or idx
        parts.append(
            f"<b>Section {_ordinal(idx)}</b>{ref_text} - "
            f"<b>COMPETENCE LEVEL {level_num}</b><br/>"
        )
        parts.append(
            f"<i>{(lvl.get('competence_description') or '').strip()}</i><br/><br/>"
        )
    parts.append(ACHIEVEMENT_TAIL_TEXT)
    _draw_paragraph(
        c, ''.join(parts), s['body'],
        MARGIN_X, 10 * mm, PAGE_W - 2 * MARGIN_X,
        HEADER_BOTTOM_Y - 10 * mm,
    )
    _draw_page_number(c, 6)


def _draw_section_index_page(c, level_idx, level, page_num, occupation_name):
    s = _styles()
    _draw_page_header(c, occupation_name)

    content_w = PAGE_W - 2 * MARGIN_X
    y = HEADER_BOTTOM_Y - 8 * mm

    def _flow(html, style, width=content_w, x=MARGIN_X):
        nonlocal y
        p = Paragraph(html, style)
        _, h = p.wrap(width, PAGE_H)
        p.drawOn(c, x, y - h)
        y -= h

    # Centred section title + competence level
    level_num = _extract_level_number(level.get('level_name', '')) or level_idx
    _flow(f"<b>Section {_ordinal(level_idx)}</b>", s['h1_center'])
    y -= 2 * mm
    _flow(f"<b>COMPETENCE LEVEL {level_num}</b>", s['h2_center'])
    y -= 6 * mm

    # TEST AREAS label (left-aligned, bold italic)
    _flow("<b><i>TEST AREAS</i></b>", s['h2'])
    y -= 2 * mm

    # Numbered list of modules
    for i, m in enumerate(level['modules'], start=1):
        _flow(f"&nbsp;&nbsp;{i}.&nbsp;&nbsp;{m['module_name']}", s['body'])
        y -= 1 * mm

    _draw_page_number(c, page_num)


def _draw_test_area_detail(c, area_no, module, page_num, occupation_name):
    s = _styles()
    _draw_page_header(c, occupation_name)

    content_w = PAGE_W - 2 * MARGIN_X
    y = HEADER_BOTTOM_Y - 8 * mm

    def _flow(html, style, width=content_w, x=MARGIN_X):
        nonlocal y
        p = Paragraph(html, style)
        _, h = p.wrap(width, PAGE_H)
        p.drawOn(c, x, y - h)
        y -= h

    # Centred heading
    _flow(f"<b>Test area {area_no}: {module['module_name']}</b>",
          s['h1_center'])
    y -= 5 * mm

    # Intro description (justified)
    desc = module.get('wp_description') or (
        f"The Worker has acquired adequate knowledge and skills to perform "
        f"{module['module_name']}.")
    _flow(desc, s['body_justify'])
    y -= 2 * mm

    # Bullet list of competence items
    items = [i.strip() for i in (module.get('wp_competence_items') or '').splitlines() if i.strip()]
    for item in items:
        _flow(f"&bull;&nbsp;{item}", s['body'])

    _draw_page_number(c, page_num)


def _draw_achievement_stamp(c, page_num, occupation_name):
    s = _styles()
    _draw_page_header(c, occupation_name)
    y_top = HEADER_BOTTOM_Y - 10 * mm
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


def _draw_grading(c, page_num, occupation_name):
    s = _styles()
    _draw_page_header(c, occupation_name)
    _draw_paragraph(
        c, "<b>Grading of Scores:</b>", s['h2'],
        MARGIN_X, HEADER_BOTTOM_Y - 8 * mm, PAGE_W - 2 * MARGIN_X, 14,
    )
    rows = ["<b>Score&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Grade</b>"]
    for score, grade in GRADING_ROWS:
        rows.append(f"{score}&nbsp;&nbsp;&nbsp;&nbsp;{grade}")
    # Frame bottom at HEADER_BOTTOM_Y-50mm, height 40mm → text starts just below heading
    _draw_paragraph(
        c, '<br/>'.join(rows), s['body'],
        MARGIN_X, HEADER_BOTTOM_Y - 50 * mm, 40 * mm, 40 * mm,
    )

    qual_lines = []
    for score, qual in GRADING_QUALIFICATION_ROWS:
        qual_lines.append(f"{score} &nbsp;-&nbsp; {qual}")
    _draw_paragraph(
        c, '<br/><br/>'.join(qual_lines), s['body'],
        MARGIN_X, MARGIN_Y, PAGE_W - 2 * MARGIN_X, 25 * mm,
    )
    _draw_page_number(c, page_num)


def _draw_employment_history(c, page_num, occupation_name,
                             rows_per_page=5, page_index=0):
    s = _styles()
    _draw_page_header(c, occupation_name)
    _draw_paragraph(
        c, "<b>Employment History</b>", s['h2'],
        MARGIN_X, HEADER_BOTTOM_Y - 6 * mm, 60 * mm, 14,
    )
    _draw_paragraph(
        c, "<i>STAMP</i>", s['h2'],
        PAGE_W - MARGIN_X - 18 * mm, HEADER_BOTTOM_Y - 6 * mm, 18 * mm, 14,
    )

    y = HEADER_BOTTOM_Y - 12 * mm
    bottom_y = 8 * mm
    box_h = (y - bottom_y) / rows_per_page

    label_x = MARGIN_X + 1 * mm
    line_right = PAGE_W - MARGIN_X - 14 * mm  # leave room for STAMP box

    def _label(text, x, ly, line_x_start, line_x_end):
        c.setFont('Helvetica', 6)
        c.setFillColor(BLACK)
        c.drawString(x, ly + 1, text)
        c.setLineWidth(0.3)
        c.line(line_x_start, ly, line_x_end, ly)

    for _ in range(rows_per_page):
        c.setLineWidth(0.5)
        c.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)

        sub_h = (box_h - 3 * mm) / 5
        ly = y - sub_h

        _label("Company/Employer:", label_x, ly,
               MARGIN_X + 22 * mm, line_right)
        ly -= sub_h

        _label("Contact (Tel./Email):", label_x, ly,
               MARGIN_X + 28 * mm, line_right)
        ly -= sub_h

        _label("Starting date:", label_x, ly,
               MARGIN_X + 13 * mm, MARGIN_X + 30 * mm)
        _label("Finishing date:", MARGIN_X + 32 * mm, ly,
               MARGIN_X + 46 * mm, line_right)
        ly -= sub_h

        _label("Authorised assessor:", label_x, ly,
               MARGIN_X + 22 * mm, line_right)
        ly -= sub_h

        _label("Position with firm:", label_x, ly,
               MARGIN_X + 17 * mm, MARGIN_X + 33 * mm)
        _label("Name/Signature:", MARGIN_X + 35 * mm, ly,
               MARGIN_X + 49 * mm, line_right)

        sx = PAGE_W - MARGIN_X - 11 * mm
        sy = y - box_h + 2 * mm
        c.setDash(2, 2)
        c.rect(sx, sy, 9 * mm, box_h - 4 * mm, stroke=1, fill=0)
        c.setDash()
        y -= box_h

    c.setLineWidth(0.5)
    c.line(MARGIN_X, y, PAGE_W - MARGIN_X, y)
    _draw_page_number(c, page_num)


def _draw_back_cover(c, occupation_name, logo_path=None, cover_color=None):
    s = _styles()

    logo_h = 24 * mm
    logo_y = PAGE_H - TOP_MARGIN - logo_h  # respect top safe zone
    if logo_path:
        _draw_transparent_image(c, logo_path, (PAGE_W - logo_h) / 2, logo_y,
                                logo_h, logo_h, bg_color=colors.white)

    content_top = logo_y - 3 * mm
    cv = ', '.join(UVTAB_INFO['core_values'])
    _draw_paragraph(
        c,
        f"<b>{UVTAB_INFO['name']}</b><br/>"
        f"{UVTAB_INFO['address']}<br/>{UVTAB_INFO['po_box']}<br/>"
        f"{UVTAB_INFO['tel']}<br/>{UVTAB_INFO['email']}<br/>"
        f"{UVTAB_INFO['website']}<br/><br/>"
        f"<b>Vision:</b> {UVTAB_INFO['vision']}<br/><br/>"
        f"<b>Mission:</b> {UVTAB_INFO['mission']}<br/><br/>"
        f"<b>Motto:</b> {UVTAB_INFO['motto']}<br/><br/>"
        f"<b>Core Values:</b> {cv}",
        s['small_center'],
        MARGIN_X, MARGIN_Y, PAGE_W - 2 * MARGIN_X, content_top - MARGIN_Y,
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


def _extract_level_number(level_name):
    """Extract level number — handles Arabic ('Level 4') and Roman ('Level IV')."""
    name = level_name or ''
    m = re.search(r'(\d+)', name)
    if m:
        return int(m.group(1))
    # Check Roman numerals longest-first so 'IV' isn't shadowed by 'I'
    roman_map = [
        ('VIII', 8), ('VII', 7), ('VI', 6), ('IV', 4),
        ('III', 3), ('IX', 9), ('II', 2), ('X', 10),
        ('V', 5), ('I', 1),
    ]
    upper = name.upper()
    for roman, val in roman_map:
        if re.search(r'\b' + roman + r'\b', upper):
            return val
    return None


def _build_levels_label(levels):
    if not levels:
        return ''
    nums = [_extract_level_number(lvl['level_name']) for lvl in levels]
    nums = [n for n in nums if n is not None]
    if not nums:
        # Fallback: use positional
        if len(levels) == 1:
            return f"LEVEL {_roman(1)}"
        return "LEVEL " + ' &amp; '.join(_roman(i) for i in range(1, len(levels) + 1))
    if len(nums) == 1:
        return f"LEVEL {_roman(nums[0])}"
    return "LEVEL " + ' &amp; '.join(_roman(n) for n in sorted(nums))


# -----------------------------------------------------------------------------
# QR code helpers
# -----------------------------------------------------------------------------

def _make_qr_image(text, error_correction=None):
    """Return a ReportLab ImageReader containing a QR code PNG for *text*."""
    if error_correction is None:
        error_correction = qrcode.constants.ERROR_CORRECT_H
    qr = qrcode.QRCode(
        version=None,
        error_correction=error_correction,
        box_size=10,
        border=2,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return ImageReader(buf)


def _draw_outer_back_cover(c, book_data):
    """Draw the outer back cover: solid occupation colour with a centred QR code.

    The QR code encodes the verify URL so anyone can scan and confirm the holder.
    Falls back to plain text if no verify_url is present.
    """
    # Solid colour background
    cover_color = _resolve_cover_color(book_data)
    c.setFillColor(cover_color)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Prefer the verify URL; fall back to plain text for offline-generated PDFs
    verify_url = book_data.get('verify_url')
    if verify_url:
        qr_content = verify_url
    else:
        qr_content = (
            "UVTAB Worker's PAS\n"
            f"Book: {book_data.get('full_label', '')}\n"
            f"Name: {book_data.get('candidate_name', '')}\n"
            f"Reg:  {book_data.get('registration_number', '')}"
        )

    try:
        qr_img = _make_qr_image(qr_content)
    except Exception:
        return  # if QR generation fails, leave the cover as plain colour

    # --- QR code and ISO text centred on the page ---
    qr_size = 40 * mm
    shift_up = 5 * mm
    qr_x = (PAGE_W - qr_size) / 2
    qr_y = (PAGE_H - qr_size) / 2 + shift_up
    c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)

    s = _styles()
    
    if verify_url:
        verify_base = verify_url.split('/verify/')[0] + '/verify' if '/verify/' in verify_url else verify_url
        verify_base = verify_base.replace('https://', '').replace('http://', '')
        _draw_paragraph(
            c, verify_base, s['cover_subtitle'],
            MARGIN_X, qr_y - 7 * mm, PAGE_W - 2 * MARGIN_X, 6 * mm,
        )

    _draw_paragraph(
        c, "ISO 9001:2015", s['cover_title_md'],
        MARGIN_X, qr_y - 17 * mm, PAGE_W - 2 * MARGIN_X, 10 * mm,
    )


# -----------------------------------------------------------------------------
# Platypus: achievement stamp flowable
# -----------------------------------------------------------------------------

class AchievementStampFlowable(Flowable):
    """Fixed-height flowable that draws the achievement level / stamp block.

    Coordinate origin (0, 0) is the bottom-left of this flowable — the
    horizontal divider line.  Labels sit at y_top=33mm; two rows descend in
    5mm + 7mm steps so the divider lands exactly at y=0 (HEIGHT=37mm).
    """
    HEIGHT = 37 * mm

    def __init__(self):
        Flowable.__init__(self)
        self.width = PAGE_W - 2 * MARGIN_X
        self.height = self.HEIGHT

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return self.width, self.height

    def draw(self):
        c = self.canv
        s = _styles()
        W = self.width
        y_top = 33 * mm

        _draw_paragraph(c, "<i>ACHIEVEMENT LEVEL</i>", s['h2'],
                        0, y_top, 70 * mm, 14)
        _draw_paragraph(c, "<i>STAMP</i>", s['h2'],
                        W - 20 * mm, y_top, 20 * mm, 14)

        rows = [
            ('Qualified to work independently',  'Assessment Period'),
            ('Qualified to work with assistance', 'Assessment Period'),
        ]
        y = y_top - 9 * mm
        for line1, line2 in rows:
            _draw_paragraph(c, line1, s['body'], 0, y, W, 12)
            c.setLineWidth(0.4)
            c.line(W - 20 * mm, y - 1, W, y - 1)
            y -= 5 * mm
            _draw_paragraph(c, line2, s['body'], 0, y, W, 12)
            c.line(W - 20 * mm, y - 1, W, y - 1)
            y -= 7 * mm

        c.setLineWidth(0.6)
        c.line(0, 0, W, 0)


# -----------------------------------------------------------------------------
# Platypus: story builder helpers
# -----------------------------------------------------------------------------

def _section_index_flowables(level_idx, lvl):
    s = _styles()
    level_num = _extract_level_number(lvl.get('level_name', '')) or level_idx
    items = [
        Spacer(1, 4 * mm),
        Paragraph(f"<b>Section {_ordinal(level_idx)}</b>", s['h1_center']),
        Spacer(1, 2 * mm),
        Paragraph(f"<b>COMPETENCE LEVEL {level_num}</b>", s['h2_center']),
        Spacer(1, 6 * mm),
        Paragraph("<b><i>TEST AREAS</i></b>", s['h2']),
        Spacer(1, 2 * mm),
    ]
    for i, m in enumerate(lvl.get('modules', []), start=1):
        items.append(Paragraph(
            f"&nbsp;&nbsp;{i}.&nbsp;&nbsp;{m['module_name']}", s['body']))
        items.append(Spacer(1, 1 * mm))
    return items


def _module_left_flowables(area_no, module):
    s = _styles()
    items = [
        Paragraph(
            f"<b>Test area {area_no}: {module['module_name']}</b>",
            s['h1_center']),
        Spacer(1, 5 * mm),
    ]
    desc = module.get('wp_description') or (
        f"The Worker has acquired adequate knowledge and skills to perform "
        f"{module['module_name']}.")
    items.append(Paragraph(desc, s['body_justify']))
    items.append(Spacer(1, 2 * mm))

    for item_text in [
        i.strip()
        for i in (module.get('wp_competence_items') or '').splitlines()
        if i.strip()
    ]:
        items.append(Paragraph(f"&bull;&nbsp;{item_text}", s['body']))

    items.append(Spacer(1, 8 * mm))
    return items


def _module_right_flowables():
    return [Spacer(1, 10 * mm), AchievementStampFlowable(), Spacer(1, 8 * mm)]


def _build_sections_story(book_data):
    levels = book_data['levels']
    story = []
    
    col_w = PAGE_W - 2 * MARGIN_X
    gap_w = 2 * MARGIN_X
    
    for level_idx, lvl in enumerate(levels, start=1):
        # Section index always gets its own page (Left side of double-wide)
        idx_flowables = _section_index_flowables(level_idx, lvl)
        story.append(Table(
            [[idx_flowables, '', '']], 
            colWidths=[col_w, gap_w, col_w],
            style=[('VALIGN', (0,0), (-1,-1), 'TOP')]
        ))
        story.append(PageBreak())
        
        # Modules: Table rows wrap them to the Left and Right cells
        for area_no, module in enumerate(lvl.get('modules', []), start=1):
            left_f = _module_left_flowables(area_no, module)
            right_f = _module_right_flowables()
            story.append(KeepTogether(Table(
                [[left_f, '', right_f]],
                colWidths=[col_w, gap_w, col_w],
                style=[('VALIGN', (0,0), (-1,-1), 'TOP')]
            )))
    return story


# -----------------------------------------------------------------------------
# Platypus: per-part PDF builders
# -----------------------------------------------------------------------------

def _build_front_matter_pdf(book_data):
    """Pages 1–6 via canvas (all existing functions, zero change)."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    c.setTitle(f"Worker's PAS - {book_data.get('candidate_name', '')}")
    _draw_cover(c, book_data);          c.showPage()
    _draw_page2_intro(c, book_data);    c.showPage()
    _draw_page3_biodata(c, book_data);  c.showPage()
    _draw_page4_levels(c, book_data);   c.showPage()
    _draw_page5_certified(c, book_data); c.showPage()
    _draw_page6_sections(c, book_data); c.showPage()
    c.save()
    return buf.getvalue()


def _build_sections_pdf(book_data):
    """Dynamic section content via Platypus — modules flow down a double-wide spread."""
    buf = BytesIO()
    occ_name = book_data['occupation_name']
    
    DOUBLE_PAGE_W = PAGE_W * 2

    content_frame = Frame(
        MARGIN_X, MARGIN_Y,
        DOUBLE_PAGE_W - 2 * MARGIN_X, HEADER_BOTTOM_Y - MARGIN_Y,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id='content',
    )
    blank_frame = Frame(
        0, 0, DOUBLE_PAGE_W, PAGE_H,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id='blank',
    )

    def on_content(canvas_obj, doc):
        left_pg = (doc.page - 1) * 2 + 1 + 6
        right_pg = (doc.page - 1) * 2 + 2 + 6
        
        # Left half header
        _draw_page_header(canvas_obj, occ_name)
        _draw_page_number(canvas_obj, left_pg)
        
        # Right half header (shift origin)
        canvas_obj.saveState()
        canvas_obj.translate(PAGE_W, 0)
        _draw_page_header(canvas_obj, occ_name)
        _draw_page_number(canvas_obj, right_pg)
        canvas_obj.restoreState()

    templates = [
        PageTemplate(id='Content', frames=[content_frame], onPage=on_content),
        PageTemplate(id='Blank',   frames=[blank_frame],   onPage=lambda c, d: None),
    ]
    doc = BaseDocTemplate(
        buf, pagesize=(DOUBLE_PAGE_W, PAGE_H), pageTemplates=templates,
        leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0,
    )
    doc.build(_build_sections_story(book_data))
    
    # Split the double-wide pages into sequential Left and Right pages
    from pypdf import PdfReader, PdfWriter, PageObject, Transformation
    from pypdf.generic import RectangleObject, FloatObject
    
    reader1 = PdfReader(BytesIO(buf.getvalue()))
    reader2 = PdfReader(BytesIO(buf.getvalue()))
    writer = PdfWriter()
    
    for p_left, p_right in zip(reader1.pages, reader2.pages):
        # Left page: crop the left half
        p_left.mediabox = RectangleObject((FloatObject(0), FloatObject(0), FloatObject(PAGE_W), FloatObject(PAGE_H)))
        p_left.cropbox = p_left.mediabox
        writer.add_page(p_left)
        
        # Right page: translate left by PAGE_W, then crop to same window
        p_right.add_transformation(Transformation().translate(float(-PAGE_W), 0))
        p_right.mediabox = RectangleObject((FloatObject(0), FloatObject(0), FloatObject(PAGE_W), FloatObject(PAGE_H)))
        p_right.cropbox = p_right.mediabox
        writer.add_page(p_right)
        
    out_buf = BytesIO()
    writer.write(out_buf)
    return out_buf.getvalue()


def _build_back_matter_pdf(book_data, start_page):
    """Grading + employment history via canvas (existing functions unchanged)."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    occ_name = book_data['occupation_name']
    pg = start_page

    _draw_grading(c, pg, occ_name);  c.showPage();  pg += 1

    rows_per_page = 5
    eh_pages = max(1, book_data.get('employment_history_pages', 4))
    for i in range(eh_pages):
        _draw_employment_history(c, pg, occ_name,
                                 rows_per_page=rows_per_page, page_index=i)
        c.showPage();  pg += 1

    c.save()
    return buf.getvalue()


def _build_back_covers_pdf(book_data):
    """UVTAB info page + outer back cover (existing functions unchanged)."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    _draw_back_cover(c, book_data['occupation_name'], book_data.get('uvtab_logo_path'))
    c.showPage()
    _draw_outer_back_cover(c, book_data)
    c.showPage()
    c.save()
    return buf.getvalue()


def _count_pages(pdf_bytes):
    return len(PdfReader(BytesIO(pdf_bytes)).pages)


def _merge_all(front_pdf, sections_pdf, back_matter_pdf, covers_pdf):
    """Merge all parts, inserting blank padding pages before covers so that
    the total page count is a multiple of 4 (saddle-stitch requirement)."""
    n_content = (_count_pages(front_pdf)
                 + _count_pages(sections_pdf)
                 + _count_pages(back_matter_pdf))
    padding = (4 - (n_content + 2) % 4) % 4  # 2 cover pages

    writer = PdfWriter()
    for pdf in (front_pdf, sections_pdf, back_matter_pdf):
        for page in PdfReader(BytesIO(pdf)).pages:
            writer.add_page(page)
    for _ in range(padding):
        writer.add_blank_page(width=PAGE_W, height=PAGE_H)
    for page in PdfReader(BytesIO(covers_pdf)).pages:
        writer.add_page(page)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

def generate_book_pdf(book_data):
    """
    Generate the full A5 booklet PDF for a single candidate.

    ``book_data`` is a dict with the following keys:
      candidate_name, date_of_birth, gender, nationality,
      print_date, photo_path,
      occupation_name, occupation_wp_code, occupation_wp_occ_code, full_label,
      levels: [{level_name, level_description, competence_description,
                modules: [{module_name, wp_description, wp_competence_items}, ...]}, ...],
      es_signature_path, cp_signature_path,
      coat_of_arms_path, uvtab_logo_path,
      employment_history_pages: int (default 4 -> 20 rows at 5/page)
    """
    levels = list(book_data['levels'])
    book_data['levels_label'] = _build_levels_label(levels)
    # Section start pages cannot be pre-computed with dynamic Platypus layout;
    # clear them so the sections list on page 6 omits the "(p. X)" references.
    for lvl in levels:
        lvl['section_start_page'] = ''

    # Part 1: fixed front matter (pages 1–6) — canvas, unchanged
    front_pdf = _build_front_matter_pdf(book_data)

    # Part 2: dynamic section content — Platypus, modules flow freely
    sections_pdf = _build_sections_pdf(book_data)

    # Part 3: grading + employment history — canvas, page numbers continue
    back_start = 6 + _count_pages(sections_pdf) + 1
    back_matter_pdf = _build_back_matter_pdf(book_data, start_page=back_start)

    # Part 4: outer back covers — canvas, unchanged
    covers_pdf = _build_back_covers_pdf(book_data)

    # Merge all parts with saddle-stitch padding before the covers
    return _merge_all(front_pdf, sections_pdf, back_matter_pdf, covers_pdf)
