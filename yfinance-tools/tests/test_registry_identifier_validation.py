"""
Adpater layer

Validation of static data imported/exported by IdentifierRegistry implementations
"""

import pytest
from pydantic import ValidationError

from tests.conftest import NB_ITEMS_TEMPLATE_REGISTRY_DATA
from yfinance_tools.adapters.file_identifier_dto import IdentifierEntryDto
from yfinance_tools.domain import ISIN, AssetType


def test_read_all_attributes() -> None:

    data = {"name": "apple", "yfTicker": "AAPL", "asset_type": "EQUITY", "currency": "USD", "isin": "US0378331005"}

    static_dto = IdentifierEntryDto.model_validate(data)

    assert static_dto.yfTicker == "AAPL"
    assert static_dto.name == "apple"
    assert static_dto.asset_type == AssetType.EQUITY
    assert static_dto.currency == "USD"
    assert static_dto.isin == ISIN("US0378331005")

    # from a json string
    str_json: str = (
        '{"name": "apple", "yfTicker": "AAPL", "asset_type": "EQUITY", "currency": "USD", "isin": "US0378331005"}'
    )
    static_dto2 = IdentifierEntryDto.model_validate_json(str_json)
    assert static_dto2.yfTicker == "AAPL"
    assert static_dto2.name == "apple"
    assert static_dto2.asset_type == AssetType.EQUITY
    assert static_dto2.currency == "USD"
    assert static_dto2.isin == ISIN("US0378331005")


def test_required_attributes() -> None:

    data = {"name": "apple", "yfTicker": "APPL"}

    entry = IdentifierEntryDto.model_validate(data)

    assert entry.name == "apple"
    assert entry.yfTicker == "APPL"
    assert entry.asset_type == AssetType.UNDEFINED
    assert entry.currency is None
    assert entry.isin is None

    str_json = '{"name": "apple", "yfTicker": "APPL"}'
    entry2 = IdentifierEntryDto.model_validate_json(str_json)

    assert entry2.name == "apple"
    assert entry2.yfTicker == "APPL"
    assert entry2.asset_type == AssetType.UNDEFINED
    assert entry2.currency is None
    assert entry2.isin is None


def test_missing_attribute() -> None:

    miss_name = {"yfTicker": "APPL"}
    with pytest.raises(ValidationError, match="name"):
        IdentifierEntryDto.model_validate(miss_name)

    miss_ticker = {"name": "apple"}
    with pytest.raises(ValidationError, match="yfTicker"):
        IdentifierEntryDto.model_validate(miss_ticker)


#
# those below are more ISIN and AssetType validation
# still test that DTO correcty handle them (check logging WARNING)
# additional contraints on the specific DTO (read and write)
#


# asset type and isin are case insensitive
def test_case_insensitive_case() -> None:

    data = {"name": "apple", "yfTicker": "APPL", "asset_type": "equity", "isin": "us0378331005"}
    entry = IdentifierEntryDto.model_validate(data)

    assert entry.isin == ISIN("US0378331005")
    assert entry.asset_type == AssetType.EQUITY


def test_name_too_long() -> None:

    data = {"name": "a" * 52, "asset_type": "EQUITY"}

    with pytest.raises(ValidationError, match="string_too_long"):
        IdentifierEntryDto.model_validate(data)


def test_invalid_asset_type() -> None:
    data = {"name": "apple", "asset_type": "invalid", "yfTicker": "AAPL", "isin": "US0378331005"}

    with pytest.raises(ValidationError, match="asset_type"):
        IdentifierEntryDto.model_validate(data)


@pytest.mark.parametrize("invalid_isin", ["not-an-isin", "120123456789", "USXXX"])
def test_invalid_isin(invalid_isin: str):

    data = {"name": "apple", "yfTicker": "APPL"}
    data["isin"] = invalid_isin
    with pytest.raises(ValidationError, match="isin"):
        IdentifierEntryDto.model_validate(data)


# maybe needed later to ignore, but safer with file (manual error)
# def test_ignore_extra_key() -> None:
#     data = {
#         "extra_key": "extra_value",
#         "name": "apple",
#         "asset_type": "equity",
#         "yfTicker": "AAPL",
#         "isin": "US0378331005",
#     }

#     entry_dto = IdentifierEntryDto.model_validate(data)
#     assert "extra_key" not in entry_dto.model_fields_set


def test_forbid_extra_key() -> None:
    data = {
        "extra_key": "extra_value",
        "name": "apple",
        "asset_type": "equity",
        "yfTicker": "AAPL",
        "isin": "US0378331005",
    }

    with pytest.raises(ValidationError, match="extra_key"):
        IdentifierEntryDto.model_validate(data)


def test_valid_template_dictionary_entries(template_registry_data) -> None:

    entries = [
        IdentifierEntryDto.model_validate({"name": name, **item}) for name, item in template_registry_data.items()
    ]

    assert len(entries) == NB_ITEMS_TEMPLATE_REGISTRY_DATA
