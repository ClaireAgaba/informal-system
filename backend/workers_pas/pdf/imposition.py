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

from PyPDF2 import PdfReader, PdfWriter, Transformation
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

    # Center each A5 page horizontally on A4 (a4_w > a5_w by ~176pt)
    x_offset = (a4_w - a5_w) / 2

    reader_a = PdfReader(BytesIO(pdf_a_bytes))
    reader_b = PdfReader(BytesIO(pdf_b_bytes)) if pdf_b_bytes else None
    writer = PdfWriter()

    n_pages = len(reader_a.pages)
    if reader_b is not None:
        n_pages = max(n_pages, len(reader_b.pages))

    for i in range(n_pages):
        page = writer.add_blank_page(width=a4_w, height=a4_h)

        # Top half: candidate A (translate up by half A4 height)
        if i < len(reader_a.pages):
            top = reader_a.pages[i]
            top.add_transformation(Transformation().translate(x_offset, a4_h / 2))
            page.merge_page(top)

        # Bottom half: candidate B
        if reader_b is not None and i < len(reader_b.pages):
            bot = reader_b.pages[i]
            bot.add_transformation(Transformation().translate(x_offset, 0))
            page.merge_page(bot)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()
