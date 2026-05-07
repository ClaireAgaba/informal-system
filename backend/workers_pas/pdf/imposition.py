"""A4 2-up duplex imposition for Worker's PAS booklets.

Given two single-candidate booklet PDFs, produce an A4 portrait PDF
ready for duplex (double-sided) printing (flip on long edge).

Each physical A4 sheet, when printed on both sides and cut along the
dashed guide lines, yields two pocket-sized booklets.
"""
from io import BytesIO

from pypdf import PdfReader, PdfWriter, Transformation, PageObject
from pypdf.generic import FloatObject, RectangleObject
from reportlab.lib.pagesizes import A4, A5, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas

from .constants import BOOKLET_W, BOOKLET_H


def _a5_blank():
    w, h = A5
    p = PageObject.create_blank_page(width=w, height=h)
    for box in ("mediabox", "cropbox", "trimbox"):
        setattr(p, box, RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(w), FloatObject(h))
        ))
    return p


def _booklet_blank():
    """Blank page at the booklet page size (passport-sized)."""
    w, h = BOOKLET_W, BOOKLET_H
    p = PageObject.create_blank_page(width=w, height=h)
    for box in ("mediabox", "cropbox", "trimbox"):
        setattr(p, box, RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(w), FloatObject(h))
        ))
    return p


def impose_2up_a4(pdf_a_bytes, pdf_b_bytes=None):
    """Sequential 2-up duplex imposition with odd/even alignment on A4 portrait.

    Each A4 portrait sheet is split into 2 horizontal rows (top = Candidate A,
    bottom = Candidate B), and each row into 2 columns (left and right A6
    portrait slots). For each booklet page K (1-indexed) we emit ONE imposed
    PDF page that contains page K of BOTH candidates, placed in only one
    column with the other column left blank:
        - K odd  -> content in RIGHT column (right-aligned)
        - K even -> content in LEFT column (left-aligned)

    Combined with duplex printing + long-edge flip, the back of each physical
    sheet has its content mirrored horizontally, so book page (2s) ends up on
    the same PHYSICAL column as book page (2s-1). The print thus produces a
    sheet whose right (or left) half carries content on BOTH sides while the
    other half is fully blank.

    Print/cut workflow:
        1. Print A4 portrait, duplex, FLIP ON LONG EDGE, 100% scale.
        2. Cut horizontally between the top and bottom rows of every sheet.
        3. Cut vertically down the middle of every strip; discard the blank
           half. Each remaining A6 strip is one booklet leaf with content on
           both sides.
        4. Stack each candidate's A6 leaves in printed order. Bind/staple.

    Input expectation: each candidate's booklet PDF is in A5 portrait with
    pages in normal reading order (page 1 = cover, page N = trailing blank).
    """
    a4_w, a4_h = A4
    a5_w, a5_h = A5

    # Quadrant size = half of A4
    q_w = a4_w / 2
    q_h = a4_h / 2

    # Scale A5 to fit a quadrant. Both axes: q/a5 = 0.5/sqrt(0.5) = 1/sqrt(2).
    scale = min(q_w / a5_w, q_h / a5_h)
    scaled_w = a5_w * scale
    scaled_h = a5_h * scale

    def _load_pages(pdf_bytes):
        if not pdf_bytes:
            return []
        return list(PdfReader(BytesIO(pdf_bytes)).pages)

    pages_a = _load_pages(pdf_a_bytes)
    pages_b = _load_pages(pdf_b_bytes) if pdf_b_bytes else []

    # Equalise lengths (Candidate B may be missing or shorter).
    n = max(len(pages_a), len(pages_b))
    while len(pages_a) < n:
        pages_a.append(_a5_blank())
    while len(pages_b) < n:
        pages_b.append(_a5_blank())

    writer = PdfWriter()

    def _place(target, src_page, q_x, q_y):
        """Place src_page into the quadrant whose lower-left is (q_x, q_y)."""
        ox = q_x + (q_w - scaled_w) / 2
        oy = q_y + (q_h - scaled_h) / 2
        src_page.add_transformation(
            Transformation().scale(scale, scale).translate(ox, oy)
        )
        src_page.mediabox = RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(a4_w), FloatObject(a4_h))
        )
        src_page.cropbox = RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(a4_w), FloatObject(a4_h))
        )
        src_page.trimbox = RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(a4_w), FloatObject(a4_h))
        )
        target.merge_page(src_page)

    # One imposed PDF page per booklet page. PDF page (k+1) is odd when k is
    # even (k starts at 0), so the right column is used; otherwise left column.
    for k in range(n):
        is_odd_pdf_page = (k % 2 == 0)
        col_x = q_w if is_odd_pdf_page else 0  # right slot for odd, left for even

        writer.add_blank_page(width=a4_w, height=a4_h)
        page = writer.pages[-1]
        # Top row = Candidate A, bottom row = Candidate B
        _place(page, pages_a[k], col_x, q_h)
        _place(page, pages_b[k], col_x, 0)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def _cut_line_overlay():
    """Return PDF bytes (A4 portrait) with dashed grey trim guide lines.

    Lines drawn:
      1. Horizontal at midpoint + 3 cm  — bottom-trim guide for top candidate
      2. Horizontal at midpoint − 3 cm  — bottom-trim guide for bottom candidate
      3. Vertical at 0.5 cm from each edge — side-trim guides (narrow each strip)

    Labels sit in the 6 cm waste strip between the two trim lines so they
    never overlap booklet content.  No separate "cut here" line — the two
    trim cuts already separate and size both candidates in one operation each.

    Returns bytes so callers can create a fresh PageObject each time via
    PdfReader — avoids the dict.copy() / 'get_contents' error in PyPDF.
    """
    buf = BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    a4_w, a4_h = A4
    mid_y = a4_h / 2
    top_trim = mid_y + 3 * cm   # bottom edge of top booklet
    bot_trim = mid_y - 3 * cm   # top edge of bottom booklet

    c.setStrokeColorRGB(0.55, 0.55, 0.55)
    c.setLineWidth(0.6)
    c.setFillColorRGB(0.55, 0.55, 0.55)

    # 1. Trim line for top candidate — label in waste strip below the line
    c.setDash(3, 4)
    c.line(8, top_trim, a4_w - 8, top_trim)
    c.setDash()
    c.setFont('Helvetica', 5)
    c.drawCentredString(a4_w / 2, top_trim - 7, 'trim')

    # 2. Trim line for bottom candidate — label in waste strip above the line
    c.setDash(3, 4)
    c.line(8, bot_trim, a4_w - 8, bot_trim)
    c.setDash()
    c.drawCentredString(a4_w / 2, bot_trim + 2, 'trim')

    # 3. Side-trim verticals — 0.5 cm from each edge
    for x_trim in (0.5 * cm, a4_w - 0.5 * cm):
        c.setDash(3, 4)
        c.line(x_trim, 8, x_trim, a4_h - 8)
        c.setDash()

    c.save()
    return buf.getvalue()


def impose_2up_a6_booklet_a4(pdf_c1_bytes, pdf_c2_bytes=None):
    """2-up passport-size saddle-stitch booklet imposition on A4 portrait.

    Two candidates are imposed on a single A4 portrait sheet — Candidate 1 on
    the top half, Candidate 2 on the bottom half (head-to-toe, rotated 180°).
    Booklet pages (BOOKLET_W × BOOKLET_H) are placed at 1:1 scale, centred
    within each A6 cell (A4/2).  Dashed cut-guide lines on the overlay show
    the operator where to trim for a passport-sized finished booklet.

    Print/cut/fold workflow:
        1. Print A4 portrait, duplex, FLIP ON LONG EDGE.
        2. Cut at the main horizontal dashed line — separates the two candidates.
        3. Cut each strip at the two vertical dashed lines (0.5 cm each side).
        4. Cut at the bottom-trim dashed line — shortens the strip by 3 cm.
        5. Rotate the lower strip 180°.
        6. Fold each strip vertically at the centre (x = 105 mm).
        7. Saddle-stitch (staple).
    Result: two independent ~100 × 118.5 mm portrait booklets per A4 sheet.

    If pdf_c2_bytes is None the bottom half of every page is left blank.
    """
    a4_w, a4_h = A4

    a6_w = a4_w / 2   # cell width  (≈ 105 mm)
    a6_h = a4_h / 2   # cell height (≈ 148.5 mm)

    # Booklet pages are placed at 1:1 — centred within the A6 cell.
    # Margins: (a6_w - BOOKLET_W)/2 ≈ 2.5 mm each side horizontally,
    #          (a6_h - BOOKLET_H)/2 ≈ 15 mm each side vertically.
    src_w, src_h = BOOKLET_W, BOOKLET_H
    scale = 1.0
    scaled_w = src_w
    scaled_h = src_h

    def _load(pdf_bytes):
        return list(PdfReader(BytesIO(pdf_bytes)).pages)

    pages_c1 = _load(pdf_c1_bytes)
    pages_c2 = _load(pdf_c2_bytes) if pdf_c2_bytes else []

    # Pad both to the same multiple of 4
    n = max(len(pages_c1), len(pages_c2), 1)
    while n % 4:
        n += 1
    while len(pages_c1) < n:
        pages_c1.append(_booklet_blank())
    while len(pages_c2) < n:
        pages_c2.append(_booklet_blank())

    n_sheets = n // 4
    writer = PdfWriter()

    def _set_a4_boxes(p):
        r = RectangleObject((FloatObject(0), FloatObject(0),
                              FloatObject(a4_w), FloatObject(a4_h)))
        p.mediabox = r
        p.cropbox = r
        p.trimbox = r

    def _place(target, src, cell_x, cell_y, rotated=False):
        """Place src into the A6 cell, flushed to the outer edge.

        Horizontal: flush to the fold (A4 centre).  Each column's booklet
        aligns with the vertical trim lines at 0.5 cm from each A4 edge.
        Vertical: flush away from mid_y.  Top-half pages sit against the top
        of the A4; bottom-half (rotated) pages sit against the bottom.  This
        makes the horizontal trim lines land exactly at the booklet edges.
        """
        h_gap = a6_w - scaled_w   # ≈ 5 mm (= 0.5 cm trim on outer edge)
        v_gap = a6_h - scaled_h   # ≈ 30 mm (= 3 cm trim on inner edge)

        # Horizontal: flush each column toward the fold (centre of A4).
        if cell_x == 0:           # left column — flush right (toward fold)
            ox = h_gap
        else:                      # right column — flush left (toward fold)
            ox = cell_x

        # Vertical: flush away from the main cut (mid_y).
        if rotated:                # bottom half — flush to page bottom
            oy = cell_y
        else:                      # top half — flush to page top
            oy = cell_y + v_gap

        if rotated:
            tf = (Transformation()
                  .scale(scale, scale)
                  .rotate(180)
                  .translate(ox + scaled_w, oy + scaled_h))
        else:
            tf = Transformation().scale(scale, scale).translate(ox, oy)
        src.add_transformation(tf)
        _set_a4_boxes(src)
        target.merge_page(src)

    cut_overlay_pdf = _cut_line_overlay()

    def _cut_page():
        return PdfReader(BytesIO(cut_overlay_pdf)).pages[0]

    for s in range(n_sheets):
        # Saddle-stitch page indices (0-based).
        # C1 front/back use standard formula.
        # C2 back has left/right swapped vs C1 because the 180° operator
        # rotation reverses the effective fold direction after cutting.
        c1_fl = n - 1 - 2 * s   # C1 front-left  (back cover on first sheet)
        c1_fr = 2 * s            # C1 front-right (front cover on first sheet)
        c1_bl = 2 * s + 1        # C1 back-left
        c1_br = n - 2 - 2 * s   # C1 back-right

        c2_fl = 2 * s            # C2 front-left  (printed 180°; becomes cover after cut+rotate)
        c2_fr = n - 1 - 2 * s   # C2 front-right (back cover after cut+rotate)
        c2_bl = n - 2 - 2 * s   # C2 back-left   (swapped vs C1)
        c2_br = 2 * s + 1        # C2 back-right  (swapped vs C1)

        # --- FRONT page ---
        writer.add_blank_page(width=a4_w, height=a4_h)
        front = writer.pages[-1]
        _place(front, pages_c1[c1_fl], 0,     a6_h, rotated=False)
        _place(front, pages_c1[c1_fr], a6_w,  a6_h, rotated=False)
        _place(front, pages_c2[c2_fl], 0,     0,    rotated=True)
        _place(front, pages_c2[c2_fr], a6_w,  0,    rotated=True)
        front.merge_page(_cut_page())

        # --- BACK page (placed in normal PDF coords; printer flip-on-long-edge
        #     will mirror left/right, which is accounted for in the formula) ---
        writer.add_blank_page(width=a4_w, height=a4_h)
        back = writer.pages[-1]
        _place(back, pages_c1[c1_bl], 0,     a6_h, rotated=False)
        _place(back, pages_c1[c1_br], a6_w,  a6_h, rotated=False)
        _place(back, pages_c2[c2_bl], 0,     0,    rotated=True)
        _place(back, pages_c2[c2_br], a6_w,  0,    rotated=True)
        back.merge_page(_cut_page())

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def impose_booklet_a4_landscape(pdf_bytes, rotate_back_side=True):
    """Impose a single A5 booklet PDF into an A4 LANDSCAPE duplex booklet.

    Output is designed for fold + staple (saddle stitch).

    - Input: A5 portrait pages in normal reading order (page 1..N)
    - Output: A4 landscape sheets, two A5 pages side-by-side per side.
    - Pages are re-ordered so that, when duplex-printed and folded, the booklet reads correctly.

    Booklet math requires total pages divisible by 4; we pad with blank A5 pages at the end.

    Printing:
      - Most printers want "flip on short edge" for landscape booklet output.
      - If your environment insists on "flip on long edge", set rotate_back_side=True (default),
        which rotates the back side by 180° to compensate on many drivers.
    """
    a5_w, a5_h = A5
    a4_w, a4_h = landscape(A4)  # (842, 595) points

    reader = PdfReader(BytesIO(pdf_bytes))
    pages = list(reader.pages)

    # Pad to a multiple of 4 pages for saddle-stitch.
    while len(pages) % 4 != 0:
        pages.append(_a5_blank())

    n = len(pages)
    n_sheets = n // 4
    writer = PdfWriter()

    def _set_a4_boxes(p):
        p.mediabox = RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(a4_w), FloatObject(a4_h))
        )
        p.cropbox = RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(a4_w), FloatObject(a4_h))
        )
        p.trimbox = RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(a4_w), FloatObject(a4_h))
        )

    def _place(target_page, src_page, x, y):
        # translate only (A5 fits A4 landscape halves without scaling)
        src_page.add_transformation(Transformation().translate(x, y))
        _set_a4_boxes(src_page)
        target_page.merge_page(src_page)

    for s in range(n_sheets):
        # Indices (0-based) for this sheet in booklet order
        # Front: [last, first]
        front_left = n - 1 - 2 * s
        front_right = 0 + 2 * s
        # Back:  [second, second-last]
        back_left = 1 + 2 * s
        back_right = n - 2 - 2 * s

        # Front side
        writer.add_blank_page(width=a4_w, height=a4_h)
        front = writer.pages[-1]
        _place(front, pages[front_left], 0, 0)
        _place(front, pages[front_right], a5_w, 0)

        # Back side
        writer.add_blank_page(width=a4_w, height=a4_h)
        back = writer.pages[-1]

        left_page = pages[back_left]
        right_page = pages[back_right]

        if rotate_back_side:
            # Rotate each A5 by 180° around its origin; then place it into its half.
            # This often makes "flip on long edge" behave like booklet printing.
            left_page = left_page.copy()
            right_page = right_page.copy()
            left_page.rotate(180)
            right_page.rotate(180)

        _place(back, left_page, 0, 0)
        _place(back, right_page, a5_w, 0)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()
