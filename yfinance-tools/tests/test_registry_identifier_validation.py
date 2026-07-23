"""
Adpater layer

Validation of static data imported/exported used by File IdentifierRegistry

RegistryFileDto and RegistryFileEntryDto
"""

import pytest
from pydantic import ValidationError

from tests.conftest import NB_ITEMS_TEMPLATE_REGISTRY_DATA
from yfinance_tools.adapters.file_identifier_dto import RegistryFileDto, RegistryFileEntryDto
from yfinance_tools.domain import ISIN, AssetType

#
# Test RegistryFileEntryDto
#


def test_entry_file_dto_python() -> None:

    data_entry = {"yfTicker": "AAPL", "assetType": "EQUITY", "currency": "USD", "isin": "US0378331005"}

    entry_dto = RegistryFileEntryDto.model_validate(data_entry)

    assert entry_dto.yfTicker == "AAPL"
    assert entry_dto.assetType == AssetType.EQUITY
    # StrEnum equal
    assert entry_dto.assetType == "EQUITY"
    assert entry_dto.currency == "USD"
    assert entry_dto.isin == ISIN("US0378331005")
    # Equal method overwritten
    assert entry_dto.isin == "US0378331005"

    data_entry_default = {"yfTicker": "AAPL"}
    entry_dto = RegistryFileEntryDto.model_validate(data_entry_default)
    assert entry_dto.yfTicker == "AAPL"
    assert entry_dto.assetType == AssetType.UNDEFINED
    assert entry_dto.assetType == "UNDEFINED"
    assert entry_dto.currency is None
    assert entry_dto.isin is None


def test_invlaid_entry_file_dto_python() -> None:

    # wrong isin format will invalid the entry
    data_entry = {"yfTicker": "AAPL", "assetType": "EQUITY", "currency": "USD", "isin": "120378331005"}

    with pytest.raises(ValidationError, match="Invalid ISIN"):
        RegistryFileEntryDto.model_validate(data_entry)

    # wrong AssetType and ISIN, both reported
    data_entry = {"yfTicker": "AAPL", "assetType": "WRONG", "isin": "120378331005"}

    with pytest.raises(ValidationError, match="Invalid ISIN"):
        RegistryFileEntryDto.model_validate(data_entry)
    with pytest.raises(ValidationError, match="Invalid AssetType"):
        RegistryFileEntryDto.model_validate(data_entry)


def test_entry_file_dto_case_insensitive() -> None:

    data = {"yfTicker": "APPL", "assetType": "equity", "isin": "us0378331005"}
    entry = RegistryFileEntryDto.model_validate(data)

    assert entry.isin == "US0378331005"
    assert entry.assetType == AssetType.EQUITY


#
# Test RegistryFileDto
#


def test_read_all_attributes() -> None:

    data = {"apple": {"yfTicker": "AAPL", "assetType": "EQUITY", "currency": "USD", "isin": "US0378331005"}}

    static_dto = RegistryFileDto.validate_python(data)

    name = "apple"
    assert static_dto[name].yfTicker == "AAPL"
    assert static_dto[name].assetType == AssetType.EQUITY
    assert static_dto[name].currency == "USD"
    assert static_dto[name].isin == ISIN("US0378331005")

    # from a json string
    str_json: str = '{"apple":{"yfTicker": "AAPL", "assetType": "EQUITY", "currency": "USD", "isin": "US0378331005"}}'
    static_dto2 = RegistryFileDto.validate_json(str_json)
    assert static_dto2[name].yfTicker == "AAPL"
    assert static_dto2[name].assetType == AssetType.EQUITY
    assert static_dto2[name].currency == "USD"
    assert static_dto2[name].isin == "US0378331005"


def test_required_attributes() -> None:

    data = {"apple": {"yfTicker": "APPL"}}

    entry = RegistryFileDto.validate_python(data)

    name = "apple"
    assert entry[name].yfTicker == "APPL"
    assert entry[name].assetType == AssetType.UNDEFINED
    assert entry[name].currency is None
    assert entry[name].isin is None

    str_json = '{"apple" : {"yfTicker": "APPL"}}'
    entry2 = RegistryFileDto.validate_json(str_json)

    assert entry2[name].yfTicker == "APPL"
    assert entry2[name].assetType == AssetType.UNDEFINED
    assert entry2[name].currency is None
    assert entry2[name].isin is None


def test_missing_attribute() -> None:

    miss_ticker = {"apple": {"assetType": "EQUITY"}}
    with pytest.raises(ValidationError, match="yfTicker"):
        RegistryFileDto.validate_python(miss_ticker)


def test_entry_python_and_json() -> None:

    data = {
        "apple": {"yfTicker": "AAPL", "assetType": "EQUITY", "currency": "USD", "isin": "US0378331005"},
        "cac40": {"yfTicker": "^FCHI", "assetType": "INDEX", "currency": "EUR", "isin": "FR0003500008"},
    }

    registry_dto = RegistryFileDto.validate_python(data)

    assert registry_dto["apple"].currency == "USD"
    assert registry_dto["cac40"].assetType == "INDEX"

    data_json = (
        ""
        "{"
        '"apple": {"yfTicker": "AAPL", "assetType": "EQUITY", "currency": "USD", "isin": "US0378331005"},'
        '"cac40": {"yfTicker": "^FCHI", "assetType": "INDEX", "currency": "EUR", "isin": "FR0003500008"}'
        "}"
    )

    registry_dto = RegistryFileDto.validate_json(data_json)

    assert registry_dto["apple"].currency == "USD"
    assert registry_dto["cac40"].assetType == "INDEX"


def test_dump_json() -> None:

    data = {
        "apple": {"yfTicker": "AAPL", "assetType": "EQUITY", "currency": "USD", "isin": "US0378331005"},
        "cac40": {"yfTicker": "^FCHI"},
    }

    registry_dto = RegistryFileDto.validate_python(data)

    json_bytes = RegistryFileDto.dump_json(registry_dto, indent=2, exclude_none=True)
    json_string = json_bytes.decode("utf-8")

    assert (
        json_string
        == """{
  "apple": {
    "yfTicker": "AAPL",
    "assetType": "EQUITY",
    "currency": "USD",
    "isin": "US0378331005"
  },
  "cac40": {
    "yfTicker": "^FCHI",
    "assetType": "UNDEFINED"
  }
}"""
    )


def test_one_wrong_entry_invalid_all() -> None:

    data = {
        "apple": {"yfTicker": "AAPL", "assetType": "EQUITY", "currency": "USD", "isin": "US0378331005"},
        "cac40": {"yfTicker": "^FCHI", "assetType": "WRONG"},
    }

    with pytest.raises(ValidationError, match="Invalid AssetType"):
        RegistryFileDto.validate_python(data)


# maybe needed later to ignore, but safer with file (manual error)
# def test_ignore_extra_key() -> None:
#     data = {
#         "extra_key": "extra_value",
#         "name": "apple",
#         "asset_type": "equity",
#         "yfTicker": "AAPL",
#         "isin": "US0378331005",
#     }

#     entry_dto = RegistryFileDto.validate_python(data)
#     assert "extra_key" not in entry_dto.model_fields_set


def test_forbid_extra_key() -> None:
    data = {"apple": {"extra_key": "extra_value", "assetType": "equity", "yfTicker": "AAPL", "isin": "US0378331005"}}

    with pytest.raises(ValidationError, match="extra_key"):
        RegistryFileDto.validate_python(data)


def test_valid_template_dictionary_entries(template_registry_data) -> None:

    entries = RegistryFileDto.validate_python(template_registry_data)

    assert len(entries) == NB_ITEMS_TEMPLATE_REGISTRY_DATA
