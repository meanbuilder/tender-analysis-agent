from src.schemas import EvidenceRecord, FindingStatus, RiskLevel
from src.tender_analyzer import analyze_tender_evidence


def test_analyzer_returns_all_27_parameters():
    findings = analyze_tender_evidence([])

    assert len(findings) == 27
    assert [finding.parameter_number for finding in findings] == list(range(1, 28))


def test_payment_terms_are_detected():
    evidence = [
        EvidenceRecord(
            filename="ATC.pdf",
            page_number=8,
            quoted_text="Payment shall be made within 30 days of receipt.",
        )
    ]

    findings = analyze_tender_evidence(evidence)
    payment = next(item for item in findings if item.parameter_key == "payment_terms")

    assert payment.status == FindingStatus.FOUND
    assert payment.evidence[0].filename == "ATC.pdf"
    assert payment.evidence[0].page_number == 8


def test_delivery_period_is_detected():
    evidence = [
        EvidenceRecord(
            filename="Bid.pdf",
            page_number=4,
            quoted_text="The delivery period shall be 24 weeks from the order date.",
        )
    ]

    findings = analyze_tender_evidence(evidence)
    delivery = next(
        item for item in findings if item.parameter_key == "delivery_period"
    )

    assert delivery.status == FindingStatus.FOUND


def test_unmatched_parameter_is_not_claimed_as_absent():
    findings = analyze_tender_evidence([])
    emd = next(item for item in findings if item.parameter_key == "emd_details")

    assert emd.status == FindingStatus.NOT_FOUND
    assert emd.review_required is True
    assert "does not prove" in emd.review_reason


def test_candidate_matches_require_human_review():
    evidence = [
        EvidenceRecord(
            filename="ATC.pdf",
            page_number=2,
            quoted_text="A performance bank guarantee is required.",
        )
    ]

    findings = analyze_tender_evidence(evidence)
    pbg = next(item for item in findings if item.parameter_key == "pbg_epbg")

    assert pbg.status == FindingStatus.FOUND
    assert pbg.review_required is True
    assert pbg.risk_level == RiskLevel.NOT_ASSESSED


def test_source_evidence_is_preserved():
    evidence = [
        EvidenceRecord(
            filename="Technical_Specification_01.pdf",
            page_number=17,
            quoted_text="Hydrostatic testing shall be performed.",
        )
    ]

    findings = analyze_tender_evidence(evidence)
    testing = next(
        item for item in findings if item.parameter_key == "testing_requirements"
    )

    assert len(testing.evidence) == 1
    assert testing.evidence[0] == evidence[0]
