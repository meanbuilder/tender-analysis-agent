"""Integration tests for the tender-analysis pipeline."""

import pytest

import src.tender_pipeline as pipeline
from src.schemas import DocumentMetadata, EvidenceRecord, FindingStatus


def test_pipeline_processes_evidence_and_creates_workbook(monkeypatch):
    """Successful extraction should produce findings and an Excel file."""

    def fake_extract(pdf_bytes, *, display_filename):
        metadata = DocumentMetadata(
            filename=display_filename,
            document_type="PDF",
            total_pages=1,
            file_size_bytes=len(pdf_bytes),
            extraction_status="success",
        )

        evidence = [
            EvidenceRecord(
                filename=display_filename,
                page_number=1,
                quoted_text=(
                    "Delivery period shall be 12 weeks from "
                    "the date of purchase order."
                ),
                section_heading="Delivery Terms",
                clause_reference="Clause 5",
            )
        ]

        return metadata, evidence

    monkeypatch.setattr(pipeline, "extract_pdf_bytes", fake_extract)

    output = pipeline.run_tender_pipeline(
        [("sample_tender.pdf", b"%PDF-test-content")],
        tender_reference="TEST-BID-001",
    )

    assert output.result.tender_reference == "TEST-BID-001"
    assert len(output.result.documents) == 1
    assert len(output.result.findings) == 27
    assert output.workbook_bytes[:2] == b"PK"
    assert isinstance(output.boq_items, list)

    delivery_finding = next(
        finding
        for finding in output.result.findings
        if finding.parameter_key == "delivery_period"
    )

    assert delivery_finding.evidence
    assert delivery_finding.review_required is True


def test_pipeline_marks_all_findings_when_all_documents_fail(
    monkeypatch,
):
    """Total extraction failure must not look like absent clauses."""

    def fake_extract(pdf_bytes, *, display_filename):
        raise ValueError("Simulated invalid PDF")

    monkeypatch.setattr(pipeline, "extract_pdf_bytes", fake_extract)

    output = pipeline.run_tender_pipeline([("broken.pdf", b"not-a-valid-pdf")])

    assert len(output.result.findings) == 27
    assert output.result.documents[0].extraction_status == "failed"
    assert "failed" in output.result.overall_status.lower()
    assert output.result.warnings

    assert all(
        finding.status == FindingStatus.EXTRACTION_FAILED
        for finding in output.result.findings
    )

    assert output.workbook_bytes[:2] == b"PK"


def test_pipeline_rejects_empty_upload_list():
    """The pipeline should require at least one uploaded document."""

    with pytest.raises(ValueError, match="at least one PDF"):
        pipeline.run_tender_pipeline([])
