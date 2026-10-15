"""Rule-based matching of extracted tender evidence to standard parameters."""

import re

from src.parameter_catalog import PARAMETERS, TenderParameter
from src.schemas import (
    EvidenceRecord,
    FindingStatus,
    ParameterFinding,
    RiskLevel,
)

# Initial keyword patterns. These locate candidate evidence; they do not
# independently prove that a clause is contractually applicable.
KEYWORDS: dict[str, tuple[str, ...]] = {
    "price_terms": (
        r"\bprice basis\b",
        r"\bfirm price\b",
        r"\bprice terms\b",
        r"\bex[- ]works\b",
        r"\bfob\b",
        r"\bcif\b",
        r"\bfor\b",
    ),
    "gst_taxes": (
        r"\bgst\b",
        r"\bgoods and services tax\b",
        r"\btax(?:es)?\b",
    ),
    "insurance_charges": (r"\binsurance\b",),
    "packing_forwarding": (
        r"\bpacking\b",
        r"\bforwarding\b",
        r"\bpacking and forwarding\b",
    ),
    "delivery_period": (
        r"\bdelivery period\b",
        r"\bdelivery schedule\b",
        r"\bweeks? from\b",
        r"\bmonths? from\b",
        r"\bwithin \d+ days\b",
    ),
    "payment_terms": (
        r"\bpayment terms?\b",
        r"\bterms of payment\b",
        r"\bpayment shall\b",
        r"\bpayment will\b",
        r"\bwithin \d+ days of\b",
    ),
    "emd_details": (
        r"\bearnest money deposit\b",
        r"\bEMD\b",
        r"\bbid security\b",
    ),
    "emd_exemption": (
        r"\bEMD exemption\b",
        r"\bexemption from EMD\b",
        r"\bMSME\b",
        r"\bNSIC\b",
        r"\bsmall scale industries\b",
    ),
    "bank_guarantee": (
        r"\bbank guarantee\b",
        r"\bBG validity\b",
    ),
    "pbg_epbg": (
        r"\bperformance bank guarantee\b",
        r"\bPBG\b",
        r"\bePBG\b",
        r"\bperformance security\b",
    ),
    "freight_charges": (
        r"\bfreight\b",
        r"\btransportation charges\b",
        r"\bcarriage charges\b",
    ),
    "penalty_late_delivery": (
        r"\bliquidated damages\b",
        r"\bLD\b",
        r"\blate delivery\b",
        r"\bdelay penalty\b",
        r"\bprice reduction\b",
    ),
    "warranty_guarantee": (
        r"\bwarranty\b",
        r"\bguarantee period\b",
        r"\bdefect liability\b",
    ),
    "security_deposit": (
        r"\bsecurity deposit\b",
        r"\bretention money\b",
    ),
    "part_order": (
        r"\bpart order\b",
        r"\bpartial order\b",
        r"\bsplit order\b",
        r"\bquantity splitting\b",
    ),
    "reverse_auction": (
        r"\breverse auction\b",
        r"\bRA\b",
        r"\be-reverse auction\b",
    ),
    "pqr_eligibility": (
        r"\bpre[- ]qualification\b",
        r"\bqualification criteria\b",
        r"\beligibility criteria\b",
        r"\bprior experience\b",
        r"\bannual turnover\b",
    ),
    "technical_specification": (
        r"\btechnical specification\b",
        r"\btechnical requirements\b",
        r"\btechnical parameters\b",
    ),
    "commercial_terms": (
        r"\bcommercial terms\b",
        r"\bcommercial conditions\b",
        r"\bgeneral conditions of contract\b",
    ),
    "loading_unloading": (
        r"\bloading\b",
        r"\bunloading\b",
        r"\bunloading charges\b",
    ),
    "tpi_inspection": (
        r"\bthird[- ]party inspection\b",
        r"\bTPI\b",
        r"\binspection agency\b",
    ),
    "offer_validity": (
        r"\boffer validity\b",
        r"\bbid validity\b",
        r"\bvalidity of offer\b",
    ),
    "bank_details": (
        r"\bbank details\b",
        r"\bbeneficiary bank\b",
        r"\baccount number\b",
        r"\bIFSC\b",
    ),
    "ibr_nonibr_asme": (
        r"\bIBR\b",
        r"\bnon[- ]IBR\b",
        r"\bASME\b",
        r"\bIndian Boiler Regulations\b",
    ),
    "testing_requirements": (
        r"\bhydro(?:static)? test(?:ing)?\b",
        r"\bPMI\b",
        r"\bUT\b",
        r"\bRT\b",
        r"\bradiographic test(?:ing)?\b",
        r"\bultrasonic test(?:ing)?\b",
    ),
    "heat_treatment": (
        r"\bheat treatment\b",
        r"\bpost[- ]weld heat treatment\b",
        r"\bPWHT\b",
    ),
    "items_specification_quantity": (
        r"\bBOQ\b",
        r"\bbill of quantities\b",
        r"\bquantity\b",
        r"\bitem description\b",
        r"\bproduct specification\b",
    ),
}


def _matches_parameter(text: str, parameter_key: str) -> bool:
    """Return whether any keyword pattern matches the supplied text."""
    patterns = KEYWORDS.get(parameter_key, ())
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _build_summary(evidence: list[EvidenceRecord]) -> str:
    """Build a short excerpt for review without changing source evidence."""
    excerpts: list[str] = []

    for record in evidence[:3]:
        normalized = re.sub(r"\s+", " ", record.quoted_text).strip()
        if len(normalized) > 350:
            normalized = normalized[:347].rstrip() + "..."
        excerpts.append(normalized)

    return " | ".join(excerpts)


def analyze_tender_evidence(
    evidence_records: list[EvidenceRecord],
) -> list[ParameterFinding]:
    """Create one finding per standard parameter.

    A keyword match means only that relevant-looking text was found.
    It is not a legal interpretation or confirmation of compliance.
    """
    findings: list[ParameterFinding] = []

    for parameter in PARAMETERS:
        matching_evidence = [
            record
            for record in evidence_records
            if _matches_parameter(record.quoted_text, parameter.key)
        ]

        if matching_evidence:
            finding = ParameterFinding(
                parameter_number=parameter.number,
                parameter_key=parameter.key,
                parameter_name=parameter.name,
                status=FindingStatus.FOUND,
                requirement_summary=_build_summary(matching_evidence),
                costing_impact=parameter.costing_impact,
                risk_level=RiskLevel.NOT_ASSESSED,
                evidence=matching_evidence,
                review_required=True,
                review_reason=(
                    "Keyword-based candidate detected. Verify the complete "
                    "clause, applicability, exceptions, and any conflicting terms."
                ),
            )
        else:
            finding = ParameterFinding(
                parameter_number=parameter.number,
                parameter_key=parameter.key,
                parameter_name=parameter.name,
                status=FindingStatus.NOT_FOUND,
                costing_impact=parameter.costing_impact,
                risk_level=RiskLevel.NOT_ASSESSED,
                review_required=True,
                review_reason=(
                    "No matching keyword was found in the text extracted so far. "
                    "This does not prove that the tender requirement is absent."
                ),
            )

        findings.append(finding)

    return findings
