"""
A4 2-up imposition for Worker's PAS booklets.

Given two single-candidate A5 booklet PDFs (with the same number of pages),
produce an A4 portrait PDF where each page contains:
  - top half: candidate A's page N
  - bottom half: candidate B's page N

After printing, the A4 sheets are guillotine-cut horizontally to yield two
separate A5 booklet stacks ready to be stapled.
"""
from io import BytesIO

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import FloatObject, RectangleObject
from reportlab.lib.pagesizes import A4, A5


def impose_2up_a4(pdf_a_bytes, pdf_b_bytes=None):
    """
    Combine two A5 PDFs onto A4 pages (top + bottom).

    If ``pdf_b_bytes`` is None the bottom half is left blank, which is useful
    when an odd number of candidates are batched together.

    Returns the imposed PDF as bytes.
    """
    a4_w, a4_h = A4  # 595.276, 841.890 points
    a5_w, a5_h = A5  # 419.528, 595.276 points

    # Scale each A5 page uniformly so its height equals half of A4 (keeping
    # aspect ratio). This preserves the upright portrait orientation — the
    # cut strips each contain a readable, non-rotated booklet page.
    # scale = (a4_h / 2) / a5_h  == 1 / sqrt(2)  ≈ 0.7071 (the A-series ratio)
    scale = (a4_h / 2) / a5_h
    scaled_w = a5_w * scale  # width of the scaled A5 page
    scaled_h = a5_h * scale  # == a4_h / 2

    # Centre horizontally on A4 (scaled A5 is narrower than A4).
    x_offset = (a4_w - scaled_w) / 2

    reader_a = PdfReader(BytesIO(pdf_a_bytes))
    reader_b = PdfReader(BytesIO(pdf_b_bytes)) if pdf_b_bytes else None
    writer = PdfWriter()

    n_pages = len(reader_a.pages)
    if reader_b is not None:
        n_pages = max(n_pages, len(reader_b.pages))

    def _scaled_transform(y_base):
        """Scale by ``scale`` about the origin then translate so the page's
        bottom-left corner lands at ``(x_offset, y_base)`` on the A4 sheet."""
        return (Transformation()
                .scale(scale, scale)
                .translate(x_offset, y_base))

    def _prepare(src_page, y_base):
        """Scale + translate the source page's content, and expand its box
        so pypdf.merge_page doesn't clip it to the original A5 region."""
        src_page.add_transformation(_scaled_transform(y_base))
        # Expand all page boxes so merge_page's internal clip rectangle
        # (built from trimbox) covers the whole A4 sheet.
        src_page.mediabox = RectangleObject(
            (FloatObject(0), FloatObject(0),
             FloatObject(a4_w), FloatObject(a4_h))
        )
        src_page.cropbox = RectangleObject(
            (FloatObject(0), FloatObject(0),
             FloatObject(a4_w), FloatObject(a4_h))
        )
        src_page.trimbox = RectangleObject(
            (FloatObject(0), FloatObject(0),
             FloatObject(a4_w), FloatObject(a4_h))
        )

    for i in range(n_pages):
        writer.add_blank_page(width=a4_w, height=a4_h)
        # IMPORTANT: the PageObject returned by add_blank_page is *not* the
        # one stored in writer.pages (the library clones it internally).
        # Mutations on the returned object are silently dropped, leading to
        # blank output. Grab the real page from writer.pages.
        page = writer.pages[-1]

        # Top half: candidate A (y range [a4_h/2, a4_h])
        if i < len(reader_a.pages):
            top = reader_a.pages[i]
            _prepare(top, a4_h / 2)
            page.merge_page(top)

        # Bottom half: candidate B (y range [0, a4_h/2])
        if reader_b is not None and i < len(reader_b.pages):
            bot = reader_b.pages[i]
            _prepare(bot, 0)
            page.merge_page(bot)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()
