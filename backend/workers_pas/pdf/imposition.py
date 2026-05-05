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
    """Duplex A4 2-up: consecutive pages on opposite sides of same sheet."""
    a4_w, a4_h = A4
    a5_w, a5_h = A5
    scale = (a4_h / 2) / a5_h
    x_offset = (a4_w - a5_w * scale) / 2

    reader_a = PdfReader(BytesIO(pdf_a_bytes))
    reader_b = PdfReader(BytesIO(pdf_b_bytes)) if pdf_b_bytes else None

    pages_a = list(reader_a.pages)
    pages_b = list(reader_b.pages) if reader_b else []
    n = max(len(pages_a), len(pages_b))
    # pad shorter booklet with blanks so both have same page count
    while len(pages_a) < n:
        pages_a.append(_a5_blank())
    while len(pages_b) < n:
        pages_b.append(_a5_blank())

    # number of physical A4 sheets = ceil(n / 2)
    n_sheets = (n + 1) // 2

    writer = PdfWriter()

    def _tx(y_base):
        return Transformation().scale(scale, scale).translate(x_offset, y_base)

    def _prepare(src, y_base):
        src.add_transformation(_tx(y_base))
        src.mediabox = RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(a4_w), FloatObject(a4_h))
        )
        src.cropbox = RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(a4_w), FloatObject(a4_h))
        )
        src.trimbox = RectangleObject(
            (FloatObject(0), FloatObject(0), FloatObject(a4_w), FloatObject(a4_h))
        )

    for s in range(n_sheets):
        # Side A (odd PDF page): pages 2*s  (front, then p2, p4...)
        a_side_a = pages_a[2 * s] if 2 * s < n else _a5_blank()
        b_side_a = pages_b[2 * s] if 2 * s < n else _a5_blank()

        writer.add_blank_page(width=a4_w, height=a4_h)
        page_a = writer.pages[-1]
        _prepare(a_side_a, a4_h / 2)
        page_a.merge_page(a_side_a)
        _prepare(b_side_a, 0)
        page_a.merge_page(b_side_a)

        # Side B (even PDF page): pages 2*s+1  (p2, p3, p5...)
        a_side_b = pages_a[2 * s + 1] if 2 * s + 1 < n else _a5_blank()
        b_side_b = pages_b[2 * s + 1] if 2 * s + 1 < n else _a5_blank()

        writer.add_blank_page(width=a4_w, height=a4_h)
        page_b = writer.pages[-1]
        _prepare(a_side_b, a4_h / 2)
        page_b.merge_page(a_side_b)
        _prepare(b_side_b, 0)
        page_b.merge_page(b_side_b)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()
