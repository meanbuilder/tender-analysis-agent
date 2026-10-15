"""Central catalog of the 27 standard tender-analysis parameters."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TenderParameter:
    """Definition of one standard tender-analysis parameter."""

    number: int
    key: str
    name: str
    description: str
    costing_impact: str


PARAMETERS: tuple[TenderParameter, ...] = (
    TenderParameter(
        1, "price_terms", "Price Terms", "Price basis and price conditions.", "High"
    ),
    TenderParameter(
        2,
        "gst_taxes",
        "GST Taxes",
        "GST rate, applicability, and tax treatment.",
        "High",
    ),
    TenderParameter(
        3,
        "insurance_charges",
        "Insurance Charges",
        "Insurance responsibility and cost.",
        "Medium",
    ),
    TenderParameter(
        4,
        "packing_forwarding",
        "Packing & Forwarding Charges",
        "Packing, forwarding, and related charges.",
        "Medium",
    ),
    TenderParameter(
        5,
        "delivery_period",
        "Delivery Period",
        "Required delivery timeline and its starting point.",
        "High",
    ),
    TenderParameter(
        6,
        "payment_terms",
        "Payment Terms",
        "Payment milestones, timelines, and conditions.",
        "High",
    ),
    TenderParameter(
        7,
        "emd_details",
        "EMD Details",
        "Earnest Money Deposit amount, form, and submission requirements.",
        "High",
    ),
    TenderParameter(
        8,
        "emd_exemption",
        "NSIC/MSME/SSI EMD Exemption",
        "Eligibility and conditions for EMD exemption.",
        "High",
    ),
    TenderParameter(
        9,
        "bank_guarantee",
        "Bank Guarantee Details",
        "Bank guarantee amount, validity, format, and submission.",
        "High",
    ),
    TenderParameter(
        10,
        "pbg_epbg",
        "PBG/ePBG Details",
        "Performance bank guarantee requirements.",
        "High",
    ),
    TenderParameter(
        11,
        "freight_charges",
        "Freight Charges",
        "Freight responsibility and transport charges.",
        "High",
    ),
    TenderParameter(
        12,
        "penalty_late_delivery",
        "Penalty/Late Delivery/Price Reduction",
        "Liquidated damages, penalties, and price-reduction clauses.",
        "High",
    ),
    TenderParameter(
        13,
        "warranty_guarantee",
        "Guarantee/Warranty Period",
        "Warranty duration, commencement, and coverage.",
        "High",
    ),
    TenderParameter(
        14,
        "security_deposit",
        "Security Deposit",
        "Security deposit amount, form, and release conditions.",
        "High",
    ),
    TenderParameter(
        15,
        "part_order",
        "Part Order",
        "Whether partial ordering or splitting is permitted.",
        "Medium",
    ),
    TenderParameter(
        16,
        "reverse_auction",
        "Reverse Auction",
        "Reverse-auction applicability and process conditions.",
        "Medium",
    ),
    TenderParameter(
        17,
        "pqr_eligibility",
        "PQR/Eligibility",
        "Pre-qualification requirements and bidder eligibility.",
        "High",
    ),
    TenderParameter(
        18,
        "technical_specification",
        "Technical Specification",
        "Technical requirements, standards, and deviations.",
        "High",
    ),
    TenderParameter(
        19,
        "commercial_terms",
        "Commercial Terms",
        "Other commercial conditions affecting the offer.",
        "High",
    ),
    TenderParameter(
        20,
        "loading_unloading",
        "Loading/Unloading",
        "Responsibility and cost of loading and unloading.",
        "Medium",
    ),
    TenderParameter(
        21,
        "tpi_inspection",
        "TPI Inspection",
        "Third-party inspection requirements and charges.",
        "Medium",
    ),
    TenderParameter(
        22,
        "offer_validity",
        "Offer Validity",
        "Required validity period of the submitted offer.",
        "Medium",
    ),
    TenderParameter(
        23,
        "bank_details",
        "Bank Details",
        "Required bank details and banking documentation.",
        "Medium",
    ),
    TenderParameter(
        24,
        "ibr_nonibr_asme",
        "IBR/Non-IBR/ASME",
        "Applicable boiler regulations, codes, and certifications.",
        "High",
    ),
    TenderParameter(
        25,
        "testing_requirements",
        "Hydro/PMI/UT/RT",
        "Hydro testing and specified material or non-destructive tests.",
        "High",
    ),
    TenderParameter(
        26,
        "heat_treatment",
        "Heat Treatment",
        "Heat-treatment processes, procedures, and records.",
        "Medium",
    ),
    TenderParameter(
        27,
        "items_specification_quantity",
        "Items/Product Specification/Quantity",
        "BOQ items, descriptions, specifications, and quantities.",
        "High",
    ),
)

PARAMETER_COUNT = 27


def get_all_parameters() -> tuple[TenderParameter, ...]:
    """Return all parameters in their defined order."""
    return PARAMETERS


def get_parameter_by_key(key: str) -> TenderParameter | None:
    """Return a parameter by its stable key, or None if not found."""
    normalized_key = key.strip().lower()
    return next(
        (parameter for parameter in PARAMETERS if parameter.key == normalized_key),
        None,
    )


def validate_parameter_catalog() -> None:
    """Raise ValueError if the catalog contains invalid or duplicate entries."""
    if len(PARAMETERS) != PARAMETER_COUNT:
        raise ValueError(
            f"Expected {PARAMETER_COUNT} parameters, found {len(PARAMETERS)}."
        )

    numbers = [parameter.number for parameter in PARAMETERS]
    keys = [parameter.key for parameter in PARAMETERS]
    names = [parameter.name for parameter in PARAMETERS]

    if numbers != list(range(1, PARAMETER_COUNT + 1)):
        raise ValueError(
            "Parameter numbers must be unique and sequential from 1 to 27."
        )

    if len(keys) != len(set(keys)):
        raise ValueError("Parameter keys must be unique.")

    if len(names) != len(set(names)):
        raise ValueError("Parameter names must be unique.")


validate_parameter_catalog()
