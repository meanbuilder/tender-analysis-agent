import pytest
from pydantic import ValidationError

from src.schemas import (
    DocumentMetadata,
    EvidenceRecord,
    FindingStatus,
    ParameterFinding,
    RiskLevel,
    TenderAnalysisResult,
)


def test_document_metadata_creation():
    document = DocumentMetadata(
        filename="GeM_Bid.pdf",
        total_pages=25,
        file_size_bytes=500000,
    )

    assert document.filename == "GeM_Bid.pdf"
    assert document.total_pages == 25
    assert document.extraction_status == "Pending"


def test_evidence_preserves_source_page():
    evidence = EvidenceRecord(
        filename="Technical_Specification.pdf",
        page_number=12,
        quoted_text="Delivery shall be completed within 24 weeks.",
        clause_reference="Clause 5.2",
    )

    assert evidence.filename == "Technical_Specification.pdf"
    assert evidence.page_number == 12
    assert evidence.clause_reference == "Clause 5.2"


def test_finding_defaults_to_not_found():
    finding = ParameterFinding(
        parameter_number=5,
        parameter_key="delivery_period",
        parameter_name="Delivery Period",
    )

    assert finding.status == FindingStatus.NOT_FOUND
    assert finding.evidence == []
    assert finding.review_required is False


def test_finding_can_record_conflicting_evidence():
    finding = ParameterFinding(
        parameter_number=5,
        parameter_key="delivery_period",
        parameter_name="Delivery Period",
        status=FindingStatus.CONFLICTING,
        review_required=True,
        review_reason="Different delivery periods appear in two documents.",
    )

    assert finding.status == FindingStatus.CONFLICTING
    assert finding.review_required is True


def test_tender_result_defaults_to_empty_lists():
    result = TenderAnalysisResult()

    assert result.documents == []
    assert result.findings == []
    assert result.warnings == []


def test_invalid_page_number_is_rejected():
    with pytest.raises(ValidationError):
        EvidenceRecord(
            filename="Bid.pdf",
            page_number=0,
            quoted_text="Sample clause",
        )


def test_invalid_parameter_number_is_rejected():
    with pytest.raises(ValidationError):
        ParameterFinding(
            parameter_number=28,
            parameter_key="invalid",
            parameter_name="Invalid Parameter",
        )


def test_risk_level_enum():
    finding = ParameterFinding(
        parameter_number=6,
        parameter_key="payment_terms",
        parameter_name="Payment Terms",
        risk_level=RiskLevel.HIGH,
    )

    assert finding.risk_level == RiskLevel.HIGH
