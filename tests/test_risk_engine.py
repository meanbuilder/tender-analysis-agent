from src.risk_engine import assess_finding_risk, assess_risks
from src.schemas import (
    EvidenceRecord,
    FindingStatus,
    ParameterFinding,
    RiskLevel,
)


def make_finding(
    key: str,
    number: int,
    text: str | None = None,
    status: FindingStatus = FindingStatus.FOUND,
) -> ParameterFinding:
    evidence = []

    if text:
        evidence.append(
            EvidenceRecord(
                filename="Tender.pdf",
                page_number=3,
                quoted_text=text,
            )
        )

    return ParameterFinding(
        parameter_number=number,
        parameter_key=key,
        parameter_name=key.replace("_", " ").title(),
        status=status,
        evidence=evidence,
    )


def test_high_impact_parameter_requires_review():
    finding = make_finding(
        "payment_terms",
        6,
        "Payment will be made after inspection.",
    )

    assessed = assess_finding_risk(finding)

    assert assessed.risk_level == RiskLevel.MEDIUM
    assert assessed.review_required is True


def test_liquidated_damages_are_flagged_for_high_review():
    finding = make_finding(
        "penalty_late_delivery",
        12,
        "Liquidated damages may apply for delayed delivery.",
    )

    assessed = assess_finding_risk(finding)

    assert assessed.risk_level == RiskLevel.HIGH
    assert "commercial wording" in assessed.review_reason


def test_unlimited_liability_is_flagged_critical():
    finding = make_finding(
        "commercial_terms",
        19,
        "The supplier accepts unlimited liability.",
    )

    assessed = assess_finding_risk(finding)

    assert assessed.risk_level == RiskLevel.CRITICAL
    assert assessed.review_required is True


def test_missing_high_impact_parameter_is_high_priority():
    finding = make_finding(
        "emd_details",
        7,
        status=FindingStatus.NOT_FOUND,
    )

    assessed = assess_finding_risk(finding)

    assert assessed.risk_level == RiskLevel.HIGH
    assert "original documents" in assessed.review_reason


def test_conflicting_evidence_is_high_priority():
    finding = make_finding(
        "delivery_period",
        5,
        status=FindingStatus.CONFLICTING,
    )

    assessed = assess_finding_risk(finding)

    assert assessed.risk_level == RiskLevel.HIGH
    assert assessed.review_required is True


def test_risk_assessment_does_not_modify_original_finding():
    finding = make_finding(
        "payment_terms",
        6,
        "Payment will be made after inspection.",
    )

    assessed = assess_finding_risk(finding)

    assert finding.risk_level == RiskLevel.NOT_ASSESSED
    assert assessed.risk_level != RiskLevel.NOT_ASSESSED


def test_assess_risks_handles_multiple_findings():
    findings = [
        make_finding("payment_terms", 6, "Payment after inspection."),
        make_finding(
            "emd_details",
            7,
            status=FindingStatus.NOT_FOUND,
        ),
    ]

    assessed = assess_risks(findings)

    assert len(assessed) == 2
    assert assessed[0].risk_level == RiskLevel.MEDIUM
    assert assessed[1].risk_level == RiskLevel.HIGH


def test_low_impact_parameter_without_risk_phrase():
    finding = make_finding(
        "part_order",
        15,
        "The buyer may place orders in accordance with the tender.",
    )

    assessed = assess_finding_risk(finding)

    assert assessed.risk_level == RiskLevel.LOW
    assert assessed.review_required is True
