"""
One-shot script: replaces the Platypus double-wide section engine in renderer.py
with a pure-canvas implementation that has zero cropbox bleed.
"""
path = '/Users/fbamwe/Documents/code/informal-system/backend/workers_pas/pdf/renderer.py'
content = open(path, 'r').read()

START = ('# -----------------------------------------------------------------------------\n'
         '# Platypus: achievement stamp flowable\n'
         '# -----------------------------------------------------------------------------')
END_MARKER = 'def _build_back_matter_pdf'

start_idx = content.find(START)
end_idx   = content.find(END_MARKER)

assert start_idx != -1, "START marker not found"
assert end_idx   != -1, "END marker not found"

NEW_SECTION = r'''# -----------------------------------------------------------------------------
# Pure-canvas section renderer (no cropbox tricks — zero bleed)
# -----------------------------------------------------------------------------

# Printable content area constants (Y coords in ReportLab bottom-up units)
_CONTENT_TOP    = HEADER_BOTTOM_Y          # just below the header rule
_CONTENT_BOTTOM = MARGIN_Y                 # above the bottom margin
_CONTENT_H      = _CONTENT_TOP - _CONTENT_BOTTOM
_CONTENT_W      = PAGE_W - 2 * MARGIN_X   # text column width

# Fixed height for one Achievement Stamp block
_STAMP_H   = 37 * mm
_STAMP_GAP = 3 * mm   # vertical gap between consecutive stamps on the same page


def _para_height(html, style, width):
    """Return the rendered height of a Paragraph in points."""
    p = Paragraph(html, style)
    _, h = p.wrap(width, 9999)
    return h


def _draw_para_canvas(c, html, style, x, y_top, width):
    """Draw a Paragraph with its top-left at (x, y_top). Returns height used."""
    p = Paragraph(html, style)
    _, h = p.wrap(width, 9999)
    p.drawOn(c, x, y_top - h)
    return h


def _measure_module_height(module, area_no, width):
    """Return the total canvas height consumed by a Test Area block (points)."""
    s = _styles()
    desc = module.get('wp_description') or (
        f"The Worker has acquired adequate knowledge and skills to perform "
        f"{module['module_name']}.")
    items_text = [
        i.strip()
        for i in (module.get('wp_competence_items') or '').splitlines()
        if i.strip()
    ]
    h  = _para_height(f"<b>Test area {area_no}: {module['module_name']}</b>",
                      s['h1_center'], width)
    h += 5 * mm
    h += _para_height(desc, s['body_justify'], width)
    h += 2 * mm
    for it in items_text:
        h += _para_height(f"&bull;&nbsp;{it}", s['body'], width)
    h += 2 * mm
    return h


def _draw_test_area(c, x, y_top, width, area_no, module):
    """Draw the Test Area block anchored at (x, y_top). Returns height used."""
    s = _styles()
    desc = module.get('wp_description') or (
        f"The Worker has acquired adequate knowledge and skills to perform "
        f"{module['module_name']}.")
    items_text = [
        i.strip()
        for i in (module.get('wp_competence_items') or '').splitlines()
        if i.strip()
    ]
    y = y_top
    h = _draw_para_canvas(
        c, f"<b>Test area {area_no}: {module['module_name']}</b>",
        s['h1_center'], x, y, width)
    y -= h + 5 * mm
    h = _draw_para_canvas(c, desc, s['body_justify'], x, y, width)
    y -= h + 2 * mm
    for it in items_text:
        h = _draw_para_canvas(c, f"&bull;&nbsp;{it}", s['body'], x, y, width)
        y -= h
    y -= 2 * mm
    return y_top - y


def _draw_achievement_stamp(c, x, y_top, width):
    """Draw one Achievement Level / Stamp block anchored at (x, y_top). Returns height used."""
    s = _styles()
    y = y_top

    # Header row
    _draw_para_canvas(c, "<i>ACHIEVEMENT LEVEL</i>", s['h2'], x, y, width - 20 * mm)
    _draw_para_canvas(c, "<i>STAMP</i>", s['h2'], x + width - 20 * mm, y, 20 * mm)
    y -= 10 * mm

    rows = [
        ('Qualified to work independently',  'Assessment Period'),
        ('Qualified to work with assistance', 'Assessment Period'),
    ]
    for line1, line2 in rows:
        _draw_para_canvas(c, line1, s['body'], x, y, width)
        c.setLineWidth(0.4)
        c.line(x + width - 20 * mm, y - 10, x + width, y - 10)
        y -= 5 * mm
        _draw_para_canvas(c, line2, s['body'], x, y, width)
        c.line(x + width - 20 * mm, y - 10, x + width, y - 10)
        y -= 7 * mm

    c.setLineWidth(0.6)
    c.line(x, y, x + width, y)
    y -= 2 * mm
    return y_top - y


def _draw_section_index_page(c, pg, occ_name, level_idx, lvl):
    """Draw the section index (list of all test areas) on the current canvas page."""
    s = _styles()
    _draw_page_header(c, occ_name)
    _draw_page_number(c, pg)

    level_num = _extract_level_number(lvl.get('level_name', '')) or level_idx
    x = MARGIN_X
    y = _CONTENT_TOP

    y -= _draw_para_canvas(c, f"<b>Section {_ordinal(level_idx)}</b>",
                           s['h1_center'], x, y, _CONTENT_W) + 2 * mm
    y -= _draw_para_canvas(c, f"<b>COMPETENCE LEVEL {level_num}</b>",
                           s['h2_center'], x, y, _CONTENT_W) + 6 * mm
    y -= _draw_para_canvas(c, "<b><i>TEST AREAS</i></b>",
                           s['h2'], x, y, _CONTENT_W) + 2 * mm

    for i, m in enumerate(lvl.get('modules', []), start=1):
        h = _draw_para_canvas(
            c, f"&nbsp;&nbsp;{i}.&nbsp;&nbsp;{m['module_name']}",
            s['body'], x, y, _CONTENT_W)
        y -= h + 1 * mm


# -----------------------------------------------------------------------------
# Canvas-based per-part PDF builders
# -----------------------------------------------------------------------------

def _build_front_matter_pdf(book_data):
    """Pages 1-6 via canvas (all existing functions, zero change)."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    c.setTitle(f"Worker's PAS - {book_data.get('candidate_name', '')}")
    _draw_cover(c, book_data);           c.showPage()
    _draw_page2_intro(c, book_data);     c.showPage()
    _draw_page3_biodata(c, book_data);   c.showPage()
    _draw_page4_levels(c, book_data);    c.showPage()
    _draw_page5_certified(c, book_data); c.showPage()
    _draw_page6_sections(c, book_data);  c.showPage()
    c.save()
    return buf.getvalue()


def _build_sections_pdf(book_data):
    """Pure-canvas section renderer - no double-wide pages, no cropbox tricks.

    Layout rules
    ------------
    * Section Index  -> single ODD page (right-hand page when booklet is open).
    * Module spreads -> Left page (EVEN) = Test Area content;
                        Right page (ODD) = Achievement Stamp.
    * Multiple modules share one spread when they fit within _CONTENT_H.
    * Each stamp is drawn at the SAME y_top as its corresponding test area so
      the two columns are perfectly vertically aligned.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    occ_name = book_data['occupation_name']

    # Physical page counter: front matter occupies pages 1-6.
    pg = 7

    for level_idx, lvl in enumerate(book_data['levels'], start=1):
        # --- Section Index page must land on an ODD page (right-hand side) ---
        if pg % 2 == 0:
            # Currently on even page; emit a blank to reach odd.
            c.showPage()
            pg += 1

        _draw_section_index_page(c, pg, occ_name, level_idx, lvl)
        c.showPage()
        pg += 1

        # After the index we must be on an EVEN page for modules (left-hand side).
        if pg % 2 != 0:
            c.showPage()   # blank padding page
            pg += 1

        # --- Module spreads ---------------------------------------------------
        modules = lvl.get('modules', [])
        if not modules:
            continue

        # Group modules into spreads. Each spread = one Left page + one Right page.
        # We greedily pack as many modules as fit within _CONTENT_H.
        spread_groups = []   # list of lists of (area_no, module, measured_h)
        current_group = []
        used_h = 0.0

        for area_no, module in enumerate(modules, start=1):
            mh = _measure_module_height(module, area_no, _CONTENT_W)
            gap = _STAMP_GAP if current_group else 0.0
            if current_group and (used_h + gap + mh > _CONTENT_H):
                spread_groups.append(current_group)
                current_group = []
                used_h = 0.0
                gap = 0.0
            current_group.append((area_no, module, mh))
            used_h += gap + mh

        if current_group:
            spread_groups.append(current_group)

        for group in spread_groups:
            # ---- LEFT page: Test Areas ----
            _draw_page_header(c, occ_name)
            _draw_page_number(c, pg)

            positions = []   # (area_no, module, y_top) for stamp sync
            y = _CONTENT_TOP
            for area_no, module, _ in group:
                positions.append((area_no, module, y))
                drawn_h = _draw_test_area(c, MARGIN_X, y, _CONTENT_W, area_no, module)
                y -= drawn_h + _STAMP_GAP

            c.showPage()
            pg += 1

            # ---- RIGHT page: Achievement Stamps (aligned to left y_tops) ----
            _draw_page_header(c, occ_name)
            _draw_page_number(c, pg)

            for area_no, module, y_top in positions:
                _draw_achievement_stamp(c, MARGIN_X, y_top, _CONTENT_W)

            c.showPage()
            pg += 1

    c.save()
    return buf.getvalue()


'''

result = content[:start_idx] + NEW_SECTION + content[end_idx:]
open(path, 'w').write(result)
print(f"Done. File length: {len(result)} chars")
