"""Deterministic screening rules for tender risks.

Risk levels indicate review priority, not a legal conclusion or a
confirmed contractual liability.
"""

import re

from src.schemas import (
    FindingStatus,
    ParameterFinding,
    RiskLevel,
)

# Parameters that can materially affect pricing, eligibility, or execution.
HIGH_IMPACT_PARAMETERS = {
    "price_terms",
    "gst_taxes",
    "delivery_period",
    "payment_terms",
    "emd_details",
    "emd_exemption",
    "bank_guarantee",
    "pbg_epbg",
    "freight_charges",
    "penalty_late_delivery",
    "warranty_guarantee",
    "security_deposit",
    "pqr_eligibility",
    "technical_specification",
    "ibr_nonibr_asme",
    "testing_requirements",
    "items_specification_quantity",
}

# Phrases that warrant closer commercial review when found in evidence.
HIGH_REVIEW_PATTERNS = (
    r"\bliquidated damages\b",
    r"\bdelay penalty\b",
    r"\bforfeit(?:ure)?\b",
    r"\bnon[- ]refundable\b",
    r"\bprice reduction\b",
    r"\bset[- ]off\b",
    r"\bdeduct(?:ion|ed)?\b",
    r"\btermination without compensation\b",
    r"\bunlimited liability\b",
    r"\bperformance security may be invoked\b",
)

CRITICAL_REVIEW_PATTERNS = (
    r"\bunlimited liability\b",
    r"\bunlimited damages\b",
)


def _evidence_text(finding: ParameterFinding) -> str:
    """Combine source excerpts for screening only."""
    return "\n".join(record.quoted_text for record in finding.evidence).lower()


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    """Check whether any risk-screening pattern appears in the evidence."""
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def assess_finding_risk(finding: ParameterFinding) -> ParameterFinding:
    """Return a copy of one finding with a screening risk level.

    This function does not decide whether a clause is legally enforceable,
    applicable, or acceptable to the bidder.
    """
    text = _evidence_text(finding)

    # Conflicts and extraction failures need priority human attention.
    if finding.status in {
        FindingStatus.CONFLICTING,
        FindingStatus.EXTRACTION_FAILED,
    }:
        level = RiskLevel.HIGH
        reason = (
            "Conflicting evidence or extraction failure requires manual "
            "verification against the original tender documents."
        )

    # Not found means no matching evidence was extracted, not that the
    # requirement is absent from the tender.
    elif finding.status == FindingStatus.NOT_FOUND:
        if finding.parameter_key in HIGH_IMPACT_PARAMETERS:
            level = RiskLevel.HIGH
            reason = (
                "High-impact parameter was not identified in the extracted "
                "evidence. Review the original documents and OCR coverage."
            )
        else:
            level = RiskLevel.MEDIUM
            reason = (
                "Parameter was not identified in the extracted evidence. "
                "Confirm whether it is addressed elsewhere in the tender."
            )

    elif _matches_any(text, CRITICAL_REVIEW_PATTERNS):
        level = RiskLevel.CRITICAL
        reason = (
            "Potentially significant liability wording was detected. "
            "Confirm the exact clause, scope, exceptions, and applicability."
        )

    elif _matches_any(text, HIGH_REVIEW_PATTERNS):
        level = RiskLevel.HIGH
        reason = (
            "Potentially significant commercial wording was detected. "
            "Verify the clause and quantify its impact before bidding."
        )

    elif finding.parameter_key in HIGH_IMPACT_PARAMETERS:
        level = RiskLevel.MEDIUM
        reason = (
            "High-impact parameter identified. Verify the complete clause "
            "and calculate the commercial or execution impact."
        )

    else:
        level = RiskLevel.LOW
        reason = (
            "No configured high-priority risk phrase was detected. "
            "This is not proof that the clause is risk-free."
        )

    existing_reason = finding.review_reason
    combined_reason = (
        f"{existing_reason} {reason}".strip() if existing_reason else reason
    )

    return finding.model_copy(
        update={
            "risk_level": level,
            "review_required": True,
            "review_reason": combined_reason,
        }
    )


def assess_risks(
    findings: list[ParameterFinding],
) -> list[ParameterFinding]:
    """Apply risk-screening rules to all parameter findings."""
    return [assess_finding_risk(finding) for finding in findings]
