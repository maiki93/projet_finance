"""
Adpater layer

Validation of static data imported by IdentifierRegistry implementations

Encapsulated in IdentifierEntryDto
"""

import pytest
from pydantic import ValidationError

from tests.conftest import NB_ITEMS_TEMPLATE_REGISTRY_DATA
from yfinance_tools.adapters import IdentifierEntryDto
from yfinance_tools.domain import AssetType


def test_read_all_attributes_present() -> None:

    data = {"name": "apple", "asset_type": "EQUITY", "yfTicker": "AAPL", "isin": "US0378331005"}

    entry = IdentifierEntryDto.model_validate(data)

    assert entry.name == "apple"
    assert entry.asset_type == AssetType.EQUITY
    assert entry.yfTicker == "AAPL"
    assert entry.isin == "US0378331005"

    #
    str_json: str = '{"name": "apple", "asset_type": "EQUITY", "yfTicker": "AAPL", "isin": "US0378331005"}'
    entry2 = IdentifierEntryDto.model_validate_json(str_json)
    assert entry2.name == "apple"
    assert entry2.asset_type == AssetType.EQUITY
    assert entry2.yfTicker == "AAPL"
    assert entry2.isin == "US0378331005"


def test_required_attributes_in_entry() -> None:

    data = {"name": "apple", "asset_type": "equity"}

    entry = IdentifierEntryDto.model_validate(data)

    assert entry.name == "apple"
    assert entry.asset_type == AssetType.EQUITY
    assert entry.yfTicker is None
    assert entry.isin is None

    str_json = '{"name": "apple", "asset_type": "equity"}'
    entry2 = IdentifierEntryDto.model_validate_json(str_json)

    assert entry2.name == "apple"
    assert entry2.asset_type == AssetType.EQUITY
    assert entry2.yfTicker is None
    assert entry2.isin is None


# asset type and isin are case incensitive
def test_case_insensitive_case() -> None:

    data = {"name": "apple", "asset_type": "equity", "isin": "us0378331005"}
    entry = IdentifierEntryDto.model_validate(data)

    assert entry.name == "apple"
    assert entry.asset_type == AssetType.EQUITY
    assert entry.yfTicker is None
    assert entry.isin == "US0378331005"


def test_name_too_long() -> None:

    data = {"name": "a" * 52, "asset_type": "EQUITY"}

    with pytest.raises(ValidationError, match="string_too_long"):
        IdentifierEntryDto.model_validate(data)


def test_invalid_asset_type() -> None:
    data = {"name": "apple", "asset_type": "invalid", "yfTicker": "AAPL", "isin": "US0378331005"}

    with pytest.raises(ValidationError, match="asset_type"):
        IdentifierEntryDto.model_validate(data)


def test_invalid_isin_length() -> None:
    data = {"name": "apple", "asset_type": "EQUITY", "isin": "USXXXX"}

    with pytest.raises(ValidationError, match="isin"):
        IdentifierEntryDto.model_validate(data)


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
        IdentifierEntryDto.model_validate({"name": symbol_name, **item})
        for symbol_name, item in template_registry_data.items()
    ]

    assert len(entries) == NB_ITEMS_TEMPLATE_REGISTRY_DATA
