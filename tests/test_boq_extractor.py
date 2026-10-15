from decimal import Decimal

from src.boq_extractor import (
    BOQItem,
    _extract_quantity_and_unit,
    _parse_decimal,
    extract_boq_items,
)
from src.schemas import EvidenceRecord


def test_parse_decimal_with_commas():
    assert _parse_decimal("1,250.75") == Decimal("1250.75")


def test_parse_invalid_decimal():
    assert _parse_decimal("not-a-number") is None


def test_extract_leading_quantity_and_unit():
    quantity, unit, description = _extract_quantity_and_unit(
        "10 Nos Boiler Feed Water Pumps"
    )

    assert quantity == Decimal("10")
    assert unit == "Nos"
    assert description == "Boiler Feed Water Pumps"


def test_extract_boq_candidate_and_source_reference():
    evidence = [
        EvidenceRecord(
            filename="BOQ.pdf",
            page_number=5,
            quoted_text=("1. Boiler Feed Water Pump\n" "2. 10 Nos Industrial Valves"),
        )
    ]

    items = extract_boq_items(evidence)

    assert len(items) == 2
    assert items[0].item_number == "1"
    assert items[0].description == "Boiler Feed Water Pump"
    assert items[0].source_filename == "BOQ.pdf"
    assert items[0].source_page == 5

    assert items[1].quantity == Decimal("10")
    assert items[1].unit == "Nos"
    assert items[1].description == "Industrial Valves"


def test_numeric_description_is_not_assigned_as_price():
    evidence = [
        EvidenceRecord(
            filename="BOQ.pdf",
            page_number=3,
            quoted_text="1. 10 Nos Boiler Tube 50 mm",
        )
    ]

    items = extract_boq_items(evidence)

    assert len(items) == 1
    assert items[0].unit_price is None
    assert items[0].total_price is None
    assert items[0].review_required is True


def test_duplicate_candidate_lines_are_removed_within_page():
    evidence = [
        EvidenceRecord(
            filename="BOQ.pdf",
            page_number=2,
            quoted_text=("1. 5 Nos Safety Valves\n" "1. 5 Nos Safety Valves"),
        )
    ]

    items = extract_boq_items(evidence)

    assert len(items) == 1


def test_empty_evidence_returns_no_items():
    assert extract_boq_items([]) == []


def test_boq_item_rejects_invalid_source_page():
    try:
        BOQItem(
            description="Industrial Valve",
            source_filename="BOQ.pdf",
            source_page=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid source page should be rejected")
