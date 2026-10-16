"""Extract PDF text using PyMuPDF with Tesseract OCR as a fallback."""

import subprocess
from io import BytesIO
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from src.schemas import DocumentMetadata, EvidenceRecord

# Use the actual Tesseract installation path on this computer.
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\WOSALES1.TPPBOILERS\AppData\Local\Programs"
    r"\Tesseract-OCR\tesseract.exe"
)


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be opened or processed."""


def _extract_page_text(page) -> tuple[str, str]:
    """Extract selectable text first, then use OCR if necessary.

    Returns:
        (extracted_text, extraction_method)

    Extraction methods:
        "text": selectable PDF text was extracted.
        "ocr": text was recovered using Tesseract.
        "ocr_empty": OCR ran but returned no text.
        "ocr_failed": OCR could not be completed.
    """
    page_text = page.get_text("text").strip()

    if page_text:
        return page_text, "text"

    try:
        # Render the scanned page at a higher resolution for OCR.
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(2, 2),
            colorspace=fitz.csRGB,
            alpha=False,
        )

        with Image.open(BytesIO(pixmap.tobytes("png"))) as image:
            ocr_text = pytesseract.image_to_string(
                image.convert("RGB"),
                lang="eng",
            ).strip()

        if ocr_text:
            return ocr_text, "ocr"

        return "", "ocr_empty"

    except (
        pytesseract.TesseractError,
        pytesseract.TesseractNotFoundError,
        subprocess.SubprocessError,
        OSError,
        RuntimeError,
        ValueError,
    ):
        return "", "ocr_failed"


def _extract_document(
    pdf,
    *,
    filename: str,
    file_size: int,
) -> tuple[DocumentMetadata, list[EvidenceRecord]]:
    """Extract text from a PDF while preserving page-level source references."""
    if pdf.is_encrypted:
        raise PDFExtractionError(
            f"Encrypted PDF cannot be processed without a password: {filename}"
        )

    total_pages = len(pdf)
    evidence: list[EvidenceRecord] = []

    text_pages = 0
    ocr_pages: list[int] = []
    ocr_empty_pages: list[int] = []
    ocr_failed_pages: list[int] = []

    for page_index, page in enumerate(pdf):
        page_number = page_index + 1
        page_text, method = _extract_page_text(page)

        if method == "text":
            text_pages += 1
        elif method == "ocr":
            ocr_pages.append(page_number)
        elif method == "ocr_empty":
            ocr_empty_pages.append(page_number)
        elif method == "ocr_failed":
            ocr_failed_pages.append(page_number)

        if not page_text:
            continue

        evidence.append(
            EvidenceRecord(
                filename=filename,
                page_number=page_number,
                quoted_text=page_text,
            )
        )

    if total_pages == 0:
        status = "Empty PDF"
    elif not evidence:
        status = "No extractable text; OCR may be required"
    elif not ocr_pages and not ocr_empty_pages and not ocr_failed_pages:
        status = "Text extracted"
    else:
        status_parts = []

        if text_pages:
            status_parts.append(f"Selectable text extracted from {text_pages} page(s)")

        if ocr_pages:
            status_parts.append(f"OCR extracted text from {len(ocr_pages)} page(s)")

        if ocr_empty_pages:
            status_parts.append(
                "OCR returned no text on page(s): "
                + ", ".join(map(str, ocr_empty_pages))
            )

        if ocr_failed_pages:
            status_parts.append(
                "OCR failed on page(s): " + ", ".join(map(str, ocr_failed_pages))
            )

        status = "; ".join(status_parts)

    metadata = DocumentMetadata(
        filename=filename,
        total_pages=total_pages,
        file_size_bytes=file_size,
        extraction_status=status,
    )

    return metadata, evidence


def extract_pdf(
    file_path: str | Path,
    *,
    display_filename: str | None = None,
) -> tuple[DocumentMetadata, list[EvidenceRecord]]:
    """Extract text from a PDF file on disk."""
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")

    filename = display_filename or path.name
    file_size = path.stat().st_size

    if path.suffix.lower() != ".pdf":
        raise PDFExtractionError(f"Expected a PDF file: {filename}")

    try:
        with fitz.open(path) as pdf:
            return _extract_document(
                pdf,
                filename=filename,
                file_size=file_size,
            )

    except PDFExtractionError:
        raise
    except (fitz.FileDataError, RuntimeError, OSError, ValueError) as exc:
        raise PDFExtractionError(f"Could not process PDF '{filename}': {exc}") from exc


def extract_pdf_bytes(
    pdf_bytes: bytes,
    *,
    display_filename: str,
) -> tuple[DocumentMetadata, list[EvidenceRecord]]:
    """Extract a PDF supplied as bytes, such as a Streamlit upload."""
    if not pdf_bytes:
        raise PDFExtractionError("The uploaded PDF is empty.")

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
            return _extract_document(
                pdf,
                filename=display_filename,
                file_size=len(pdf_bytes),
            )

    except PDFExtractionError:
        raise
    except (fitz.FileDataError, RuntimeError, OSError, ValueError) as exc:
        raise PDFExtractionError(
            f"Could not process uploaded PDF '{display_filename}': {exc}"
        ) from exc
