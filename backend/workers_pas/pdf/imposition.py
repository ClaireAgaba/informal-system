"""A4 2-up duplex imposition for Worker's PAS booklets.

Given two single-candidate A5 booklet PDFs, produce an A4 portrait PDF
ready for duplex (double-sided) printing (flip on long edge).

Each physical A4 sheet, when printed on both sides and cut horizontally,
yields two A5 half-sheets with consecutive pages back-to-back.
"""
from io import BytesIO

from pypdf import PdfReader, PdfWriter, Transformation, PageObject
from pypdf.generic import FloatObject, RectangleObject
from reportlab.lib.pagesizes import A4, A5, landscape


def _a5_blank():
    w, h = A5
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
