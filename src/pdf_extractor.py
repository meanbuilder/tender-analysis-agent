"""Extract text from PDF files while preserving source-page information."""

from pathlib import Path

import fitz  # PyMuPDF
from pydantic import ValidationError

from src.schemas import DocumentMetadata, EvidenceRecord


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be opened or processed."""


def extract_pdf(
    file_path: str | Path,
    *,
    display_filename: str | None = None,
) -> tuple[DocumentMetadata, list[EvidenceRecord]]:
    """Extract text page by page from a PDF.

    Args:
        file_path: Path to the PDF file.
        display_filename: Optional original filename shown to the user.

    Returns:
        A tuple containing document metadata and page-level evidence records.

    Raises:
        PDFExtractionError: If the PDF cannot be opened or processed.
        FileNotFoundError: If the specified file does not exist.
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")

    filename = display_filename or path.name
    file_size = path.stat().st_size

    if path.suffix.lower() != ".pdf":
        raise PDFExtractionError(f"Expected a PDF file: {filename}")

    evidence: list[EvidenceRecord] = []

    try:
        with fitz.open(path) as pdf:
            if pdf.is_encrypted:
                raise PDFExtractionError(
                    f"Encrypted PDF cannot be processed without a password: {filename}"
                )

            total_pages = len(pdf)
            pages_with_text = 0
            pages_without_text = 0

            for page_index, page in enumerate(pdf):
                page_text = page.get_text("text").strip()

                if not page_text:
                    pages_without_text += 1
                    continue

                pages_with_text += 1

                evidence.append(
                    EvidenceRecord(
                        filename=filename,
                        page_number=page_index + 1,
                        quoted_text=page_text,
                    )
                )

            if total_pages == 0:
                extraction_status = "Empty PDF"
            elif pages_with_text == 0:
                extraction_status = "No extractable text; OCR may be required"
            elif pages_without_text:
                extraction_status = (
                    f"Partial text extraction; {pages_without_text} "
                    "page(s) may require OCR"
                )
            else:
                extraction_status = "Text extracted"

            metadata = DocumentMetadata(
                filename=filename,
                total_pages=total_pages,
                file_size_bytes=file_size,
                extraction_status=extraction_status,
            )

    except PDFExtractionError:
        raise
    except (fitz.FileDataError, RuntimeError, OSError, ValueError) as exc:
        raise PDFExtractionError(f"Could not process PDF '{filename}': {exc}") from exc

    return metadata, evidence


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
            evidence: list[EvidenceRecord] = []
            pages_without_text = 0
            total_pages = len(pdf)

            for page_index, page in enumerate(pdf):
                page_text = page.get_text("text").strip()

                if not page_text:
                    pages_without_text += 1
                    continue

                evidence.append(
                    EvidenceRecord(
                        filename=display_filename,
                        page_number=page_index + 1,
                        quoted_text=page_text,
                    )
                )

            if total_pages == 0:
                status = "Empty PDF"
            elif not evidence:
                status = "No extractable text; OCR may be required"
            elif pages_without_text:
                status = (
                    f"Partial text extraction; {pages_without_text} "
                    "page(s) may require OCR"
                )
            else:
                status = "Text extracted"

            metadata = DocumentMetadata(
                filename=display_filename,
                total_pages=total_pages,
                file_size_bytes=len(pdf_bytes),
                extraction_status=status,
            )

            return metadata, evidence

    except (fitz.FileDataError, RuntimeError, OSError, ValueError) as exc:
        raise PDFExtractionError(
            f"Could not process uploaded PDF '{display_filename}': {exc}"
        ) from exc
