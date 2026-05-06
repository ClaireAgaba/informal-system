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
    """Saddle-stitch booklet imposition on A4 portrait, 2 booklets per sheet.

    Each A4 sheet is divided into 4 quadrants (2x2 grid). The top row holds
    Candidate A's pages, the bottom row holds Candidate B's. Within each
    row, the LEFT slot holds the back page and the RIGHT slot holds the
    front page (matching standard saddle-stitch booklet layout).

    Layout per A4 sheet (sheet index i, 0 = outermost):
        FRONT of paper:
          [ C1 page N-2i  | C1 page 1+2i  ]   <- top row
          [ C2 page N-2i  | C2 page 1+2i  ]   <- bottom row
        BACK of paper (mirrored for long-edge duplex flip):
          [ C1 page N-1-2i | C1 page 2+2i ]
          [ C2 page N-1-2i | C2 page 2+2i ]

    Workflow:
        1. Print A4 portrait, duplex, FLIP ON LONG EDGE.
        2. Cut horizontally between top and bottom rows -> 2 A5-landscape strips.
        3. Stack each candidate's strips in order (sheet 0 outside, last inside).
        4. Fold each stack vertically along the centre and staple in the fold.

    The resulting booklet is A6 portrait (105x148mm). Each A4 sheet carries
    4 pages of each booklet (2 on the front, 2 on the back). Booklets whose
    page count is not a multiple of 4 are padded with blank A5 pages.
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

    # Read sources and pad to a multiple of 4 (saddle-stitch requirement).
    reader_a = PdfReader(BytesIO(pdf_a_bytes))
    pages_a = list(reader_a.pages)
    pages_b = list(PdfReader(BytesIO(pdf_b_bytes)).pages) if pdf_b_bytes else []

    n = max(len(pages_a), len(pages_b))
    n = ((n + 3) // 4) * 4  # round up to multiple of 4
    while len(pages_a) < n:
        pages_a.append(_a5_blank())
    while len(pages_b) < n:
        pages_b.append(_a5_blank())

    n_sheets = n // 4
    writer = PdfWriter()

    def _place(target, src_page, q_x, q_y):
        """Place src_page into the quadrant whose lower-left is (q_x, q_y)."""
        # Centre within the quadrant in case scaled dims differ slightly.
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

    for i in range(n_sheets):
        # Saddle-stitch indices (0-indexed) for sheet i (0 = outermost):
        #   FRONT side: physical-left = page (n-1-2i), physical-right = page (2i)
        #   BACK  side: physical-left = page (1+2i),   physical-right = page (n-2-2i)
        # Long-edge duplex flip mirrors LEFT<->RIGHT on the back, so PDF placement
        # on the back side is the MIRROR of the desired physical layout.
        front_left  = n - 1 - 2 * i  # back-cover-side (page N-2i in 1-indexed)
        front_right = 2 * i          # front-cover-side (page 1+2i in 1-indexed)
        back_left_pdf  = n - 2 - 2 * i  # mirrors physical-right of back -> page N-1-2i
        back_right_pdf = 1 + 2 * i      # mirrors physical-left of back -> page 2+2i

        # FRONT of paper
        writer.add_blank_page(width=a4_w, height=a4_h)
        page_front = writer.pages[-1]
        # Top row = Candidate A
        _place(page_front, pages_a[front_left],  0,   q_h)  # top-left
        _place(page_front, pages_a[front_right], q_w, q_h)  # top-right
        # Bottom row = Candidate B
        _place(page_front, pages_b[front_left],  0,   0)    # bottom-left
        _place(page_front, pages_b[front_right], q_w, 0)    # bottom-right

        # BACK of paper (mirrored for long-edge duplex flip)
        writer.add_blank_page(width=a4_w, height=a4_h)
        page_back = writer.pages[-1]
        _place(page_back, pages_a[back_left_pdf],  0,   q_h)
        _place(page_back, pages_a[back_right_pdf], q_w, q_h)
        _place(page_back, pages_b[back_left_pdf],  0,   0)
        _place(page_back, pages_b[back_right_pdf], q_w, 0)

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
