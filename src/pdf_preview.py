
"""Render original tender PDF pages with verified text highlights."""

from __future__ import annotations

import fitz


def render_highlighted_pdf_page(
    pdf_bytes: bytes,
    page_number: int,
    quoted_text: str,
) -> tuple[bytes | None, bool, str]:
    """Render a one-based PDF page and highlight matching quoted text.

    Returns:
        PNG bytes, whether the quotation was highlighted, and a status message.
    """
    document = None

    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")

        if not 1 <= page_number <= len(document):
            return None, False, "The cited page number is outside the PDF."

        page = document[page_number - 1]
        highlighted = False

        if quoted_text and quoted_text.strip():
            matches = page.search_for(quoted_text.strip(), quads=True)

            if matches:
                page.add_highlight_annot(matches)
                highlighted = True

        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(1.5, 1.5),
            alpha=False,
            annots=True,
        )
        png_bytes = pixmap.tobytes("png")

        if highlighted:
            message = "The cited quotation was located and highlighted."
        else:
            message = (
                "The original page is displayed, but the complete quotation "
                "could not be matched. No highlight was added."
            )

        return png_bytes, highlighted, message

    except Exception:
        return None, False, (
            "The PDF page could not be rendered. Check the original PDF."
        )

    finally:
        if document is not None:
            document.close()
