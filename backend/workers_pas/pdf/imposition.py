"""A4 2-up duplex imposition for Worker's PAS booklets.

Given two single-candidate A5 booklet PDFs, produce an A4 portrait PDF
ready for duplex (double-sided) printing (flip on long edge).

Each physical A4 sheet, when printed on both sides and cut horizontally,
yields two A5 half-sheets with consecutive pages back-to-back.
"""
from io import BytesIO

from pypdf import PdfReader, PdfWriter, Transformation, PageObject
from pypdf.generic import FloatObject, RectangleObject
from reportlab.lib.pagesizes import A4, A5


def _a5_blank():
    w, h = A5
    p = PageObject.create_blank_page(width=w, height=h)
    for box in ("mediabox", "cropbox", "trimbox"):
        setattr(p, box, RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(w), FloatObject(h))
        ))
    return p


def impose_2up_a4(pdf_a_bytes, pdf_b_bytes=None):
    """Duplex 2-up: A4 landscape with two A5 portraits side-by-side.

    No scaling. Candidate A on the left slot (0, 0), candidate B on the
    right slot (a5_w, 0). A4 landscape height = A5 portrait height, so
    they fit perfectly. Cut the printed A4 landscape vertically down the
    middle to yield two A5 booklets.
    """
    a4_w, a4_h = A4
    a5_w, a5_h = A5
    # A4 landscape: swap width/height
    sheet_w = a4_h  # 841.89 pt (297 mm)
    sheet_h = a4_w  # 595.28 pt (210 mm) = A5 height

    reader_a = PdfReader(BytesIO(pdf_a_bytes))
    reader_b = PdfReader(BytesIO(pdf_b_bytes)) if pdf_b_bytes else None

    pages_a = list(reader_a.pages)
    pages_b = list(reader_b.pages) if reader_b else []
    n = max(len(pages_a), len(pages_b))
    while len(pages_a) < n:
        pages_a.append(_a5_blank())
    while len(pages_b) < n:
        pages_b.append(_a5_blank())

    n_sheets = (n + 1) // 2
    writer = PdfWriter()

    def _tx(x_base):
        # Translate-only, no scaling
        return Transformation().translate(x_base, 0)

    def _prepare(src, x_base):
        src.add_transformation(_tx(x_base))
        src.mediabox = RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(sheet_w), FloatObject(sheet_h))
        )
        src.cropbox = RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(sheet_w), FloatObject(sheet_h))
        )
        src.trimbox = RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(sheet_w), FloatObject(sheet_h))
        )

    for s in range(n_sheets):
        a_side_a = pages_a[2 * s] if 2 * s < n else _a5_blank()
        b_side_a = pages_b[2 * s] if 2 * s < n else _a5_blank()

        writer.add_blank_page(width=sheet_w, height=sheet_h)
        page_a = writer.pages[-1]
        _prepare(a_side_a, 0)       # left slot (candidate A)
        page_a.merge_page(a_side_a)
        _prepare(b_side_a, a5_w)    # right slot (candidate B)
        page_a.merge_page(b_side_a)

        a_side_b = pages_a[2 * s + 1] if 2 * s + 1 < n else _a5_blank()
        b_side_b = pages_b[2 * s + 1] if 2 * s + 1 < n else _a5_blank()

        # Side B: swap left/right so that when the printer flips the paper
        # on the SHORT edge (standard landscape duplex), each A5 strip gets
        # its own back page on the correct physical side.
        writer.add_blank_page(width=sheet_w, height=sheet_h)
        page_b = writer.pages[-1]
        _prepare(b_side_b, 0)       # candidate B on PDF left → physical right after flip
        page_b.merge_page(b_side_b)
        _prepare(a_side_b, a5_w)    # candidate A on PDF right → physical left after flip
        page_b.merge_page(a_side_b)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()
