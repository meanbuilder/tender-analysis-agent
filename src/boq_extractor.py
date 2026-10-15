"""Extract candidate BOQ and technical-item records from tender evidence."""

import re
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict, Field

from src.schemas import EvidenceRecord


class BOQItem(BaseModel):
    """A candidate bill-of-quantities or technical-item record."""

    model_config = ConfigDict(extra="forbid")

    item_number: str | None = None
    description: str = Field(min_length=1)
    quantity: Decimal | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    total_price: Decimal | None = None

    source_filename: str = Field(min_length=1)
    source_page: int = Field(ge=1)

    review_required: bool = True
    review_reason: str | None = None


# Supports common forms such as 1, 10.5, 1,250 and 1,250.75.
NUMBER = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"

QUANTITY_UNIT_PATTERN = re.compile(
    rf"^\s*(?P<quantity>{NUMBER})\s+"
    r"(?P<unit>Nos?|Units?|Sets?|Each|Ea|Kg|Kgs|"
    r"Tonnes?|MT|Meters?|Metres?|Mtr|Mtrs|"
    r"Litres?|Ltrs?|Hours?|Days?|Months?)\b",
    flags=re.IGNORECASE,
)

MONEY_PATTERN = re.compile(
    rf"(?<!\w)(?:INR|Rs\.?|₹)?\s*(?P<amount>{NUMBER})" r"(?!\w)",
    flags=re.IGNORECASE,
)

ITEM_NUMBER_PATTERN = re.compile(
    r"^\s*(?P<number>\d+(?:\.\d+)*(?:[A-Z])?)" r"[\).:-]\s+(?P<description>.+)$",
    flags=re.IGNORECASE,
)


def _parse_decimal(value: str) -> Decimal | None:
    """Convert a formatted numeric string into Decimal."""
    try:
        return Decimal(value.replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        return None


def _normalize_text(text: str) -> str:
    """Normalize whitespace without altering the source evidence."""
    return re.sub(r"\s+", " ", text).strip()


def _extract_quantity_and_unit(
    description: str,
) -> tuple[Decimal | None, str | None, str]:
    """Extract a leading quantity/unit pair when clearly present."""
    match = QUANTITY_UNIT_PATTERN.match(description)

    if not match:
        return None, None, description

    quantity = _parse_decimal(match.group("quantity"))
    unit = match.group("unit")

    remaining = description[match.end() :].strip(" \t-:;,")

    return quantity, unit, remaining or description


def _extract_money_values(text: str) -> list[Decimal]:
    """Extract numeric candidates that may represent monetary values.

    These are candidates only: surrounding labels and table columns are
    required before a number can safely be classified as a price.
    """
    values: list[Decimal] = []

    for match in MONEY_PATTERN.finditer(text):
        value = _parse_decimal(match.group("amount"))

        if value is not None:
            values.append(value)

    return values


def extract_boq_items(
    evidence_records: list[EvidenceRecord],
) -> list[BOQItem]:
    """Extract candidate BOQ rows from page-level text evidence.

    This initial implementation works on individual text lines. It does
    not reconstruct multi-column PDF tables or infer unlabeled prices.
    """
    items: list[BOQItem] = []
    seen: set[tuple[str, int, str]] = set()

    for record in evidence_records:
        for raw_line in record.quoted_text.splitlines():
            line = _normalize_text(raw_line)

            if not line or len(line) < 5:
                continue

            item_number: str | None = None
            description = line

            number_match = ITEM_NUMBER_PATTERN.match(line)

            if number_match:
                item_number = number_match.group("number")
                description = number_match.group("description").strip()

            quantity, unit, cleaned_description = _extract_quantity_and_unit(
                description
            )

            # Require a plausible description and either a leading item
            # number or a recognized quantity/unit pair.
            if not item_number and quantity is None:
                continue

            if len(cleaned_description) < 3:
                continue

            identity = (
                record.filename,
                record.page_number,
                line.casefold(),
            )

            if identity in seen:
                continue

            seen.add(identity)

            # Do not assign unlabeled numbers as prices. Numeric values
            # in item descriptions may be dimensions, capacities, or codes.
            money_candidates = _extract_money_values(cleaned_description)

            review_reason = (
                "Candidate row extracted from PDF text. Verify against the "
                "original BOQ table; prices and column alignment are not "
                "automatically confirmed."
            )

            if quantity is None:
                review_reason += " Quantity and unit were not identified."

            if money_candidates:
                review_reason += (
                    " Numeric values were detected, but no price field was "
                    "assigned because the table column could not be verified."
                )

            items.append(
                BOQItem(
                    item_number=item_number,
                    description=cleaned_description,
                    quantity=quantity,
                    unit=unit,
                    unit_price=None,
                    total_price=None,
                    source_filename=record.filename,
                    source_page=record.page_number,
                    review_required=True,
                    review_reason=review_reason,
                )
            )

    return items
