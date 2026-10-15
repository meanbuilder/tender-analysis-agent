import fitz
import pytest

from src.pdf_extractor import (
    PDFExtractionError,
    extract_pdf,
    extract_pdf_bytes,
)


def create_test_pdf(*pages: str) -> bytes:
    """Create a small PDF in memory for testing."""
    document = fitz.open()

    for text in pages:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text)

    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def test_extract_pdf_preserves_filename_and_page_numbers(tmp_path):
    pdf_path = tmp_path / "tender.pdf"
    pdf_path.write_bytes(
        create_test_pdf("Delivery within 20 weeks", "Payment after inspection")
    )

    metadata, evidence = extract_pdf(pdf_path)

    assert metadata.filename == "tender.pdf"
    assert metadata.total_pages == 2
    assert metadata.extraction_status == "Text extracted"
    assert [item.page_number for item in evidence] == [1, 2]
    assert "20 weeks" in evidence[0].quoted_text


def test_extract_pdf_uses_display_filename(tmp_path):
    pdf_path = tmp_path / "temporary.pdf"
    pdf_path.write_bytes(create_test_pdf("Warranty: 24 months"))

    metadata, evidence = extract_pdf(
        pdf_path,
        display_filename="Technical_Specification.pdf",
    )

    assert metadata.filename == "Technical_Specification.pdf"
    assert evidence[0].filename == "Technical_Specification.pdf"


def test_extract_pdf_bytes():
    pdf_bytes = create_test_pdf("EMD: INR 100000")

    metadata, evidence = extract_pdf_bytes(
        pdf_bytes,
        display_filename="GeM_Bid.pdf",
    )

    assert metadata.filename == "GeM_Bid.pdf"
    assert metadata.total_pages == 1
    assert "EMD" in evidence[0].quoted_text


def test_missing_file_raises_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        extract_pdf(tmp_path / "missing.pdf")


def test_empty_bytes_raise_error():
    with pytest.raises(PDFExtractionError):
        extract_pdf_bytes(b"", display_filename="empty.pdf")


def test_invalid_pdf_bytes_raise_error():
    with pytest.raises(PDFExtractionError):
        extract_pdf_bytes(
            b"This is not a PDF",
            display_filename="invalid.pdf",
        )


def test_image_only_page_is_flagged_for_ocr():
    pdf_bytes = create_test_pdf("")

    metadata, evidence = extract_pdf_bytes(
        pdf_bytes,
        display_filename="scanned_tender.pdf",
    )

    assert evidence == []
    assert "OCR may be required" in metadata.extraction_status
