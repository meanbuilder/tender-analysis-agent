from src.parameter_catalog import (
    PARAMETER_COUNT,
    PARAMETERS,
    get_all_parameters,
    get_parameter_by_key,
    validate_parameter_catalog,
)


def test_catalog_contains_27_parameters():
    assert len(PARAMETERS) == 27
    assert PARAMETER_COUNT == 27


def test_parameter_numbers_are_sequential():
    assert [parameter.number for parameter in PARAMETERS] == list(range(1, 28))


def test_parameter_names_are_unique():
    names = [parameter.name for parameter in PARAMETERS]
    assert len(names) == len(set(names))


def test_get_all_parameters_preserves_order():
    assert get_all_parameters() == PARAMETERS


def test_lookup_existing_parameter():
    parameter = get_parameter_by_key("payment_terms")

    assert parameter is not None
    assert parameter.number == 6
    assert parameter.name == "Payment Terms"


def test_lookup_is_case_insensitive_and_trims_spaces():
    parameter = get_parameter_by_key("  PAYMENT_TERMS  ")

    assert parameter is not None
    assert parameter.key == "payment_terms"


def test_lookup_unknown_parameter():
    assert get_parameter_by_key("unknown_parameter") is None


def test_catalog_validation_passes():
    validate_parameter_catalog()
