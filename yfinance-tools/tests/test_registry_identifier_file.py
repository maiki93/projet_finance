"""
Adapter layer tests

test implementation of InFileIdentifierRegistry:
- load valid / invalid JSON file : create file in temporary directory
    - raise specific YFinanceToolsError
- validation of data (common) using DTO
    more on data validation in test_registry_identifier_validation.py
"""

import logging
import os
import pathlib
import re
from pathlib import Path

import pytest

import tests.utils as utils
from tests.conftest import NB_ITEMS_TEMPLATE_REGISTRY_DATA
from yfinance_tools.adapters import InFileIdentifierRegistry
from yfinance_tools.domain import (
    ISIN,
    AssetType,
    FinancialIdentifierEntry,
    FinancialIdentifiers,
    PendingIdentifierEntryUpdate,
    SelectorAssetBuilder,
)
from yfinance_tools.domain.exceptions import IdentifierRegistryError, IdentifierRegistryFileNotExistingError
from yfinance_tools.domain.selector_asset import SelectorAsset


def test_load_identifier_from_file(tmp_path: Path, template_registry_data) -> None:

    # create a valid temporary json file with the template data
    json_file = utils.create_file_with_content(tmp_path, "static_ids.json", template_registry_data)

    # initialize registry, no check
    registry = InFileIdentifierRegistry(str(json_file))

    # create domain object from file
    fin_id: FinancialIdentifiers = registry.load(SelectorAsset())

    assert len(fin_id) == NB_ITEMS_TEMPLATE_REGISTRY_DATA

    assert fin_id.find("quantum").yf_ticker == "QNT"
    assert fin_id.find("cac40").currency == "EUR"
    assert fin_id.find("eurusd").asset_type == "FOREX"
    assert fin_id.find("natixis_horizon_40_44").isin == "FR0011461276"


def test_load_partially_valid_file(caplog, tmp_path: Path) -> None:
    caplog.set_level(logging.WARNING)

    # valid JSON, but missing required yfTicker and asset name too short
    data = {
        "apple": {},
        "cac40": {"yfTicker": "^FCHI", "isin": "FR0003500008", "assetType": "INDEX"},
        "e": {"yfTicker": "EURUSD=X"},
    }
    json_file = utils.create_file_with_content(tmp_path, "staticids.json", data)

    registry = InFileIdentifierRegistry(json_file)

    fin_id: FinancialIdentifiers = registry.load(SelectorAsset())

    assert len(fin_id) == 1
    assert ["cac40"] == fin_id.get_entries()

    # test both my code and pydantic log output
    assert "Skip invalid entry 'apple'" in caplog.text
    assert "'yfTicker': Field required" in caplog.text
    assert "Skip invalid entry 'e'" in caplog.text
    assert "String should have at least 3 characters" in caplog.text


@pytest.mark.parametrize(
    "name, type, expected", [(None, "EQUITY", 1), ("eurusd", None, 1), (None, None, 6), ("bitcoin", "EQUITY", 2)]
)
def test_load_with_selector(tmp_path: Path, template_registry_data, name, type, expected) -> None:

    json_file = utils.create_file_with_content(tmp_path, "static_ids.json", template_registry_data)

    # initialize registry, no check
    registry = InFileIdentifierRegistry(str(json_file))

    selector = SelectorAssetBuilder().with_name(name).with_type(type).build()

    # create domain object from file
    fin_id: FinancialIdentifiers = registry.load(selector=selector)

    assert len(fin_id) == expected


def test_load_invalid_json_file(tmp_path: Path) -> None:

    json_file = utils.create_file_with_content(tmp_path, "invalid.json", "{]}")

    registry = InFileIdentifierRegistry(str(json_file))

    with pytest.raises(IdentifierRegistryError, match="Invalid JSON format"):
        registry.load(SelectorAsset())


def test_load_file_do_not_exist(tmp_path: Path) -> None:

    # do not create file
    registry = InFileIdentifierRegistry(str(tmp_path / "static_ids.json"))

    # excinfo, alternative to match
    with pytest.raises(IdentifierRegistryFileNotExistingError) as excinfo:
        registry.load(SelectorAsset())
    # file path is reported in error message
    assert "static_ids.json" in str(excinfo)


# tempalte_registry_data not used
def test_update_registry(caplog, tmp_path: Path, template_registry_data: dict) -> None:
    caplog.set_level(logging.INFO)

    data_origin = {
        "apple": {"yfTicker": "AAPL"},
        "cac40": {"yfTicker": "^FCHI", "assetType": "INDEX", "isin": "FR0003500008"},
        "eurusd": {"yfTicker": "EURUSD=X"},
    }

    json_file = utils.create_file_with_content(tmp_path, "static_ids.json", data_origin)

    # initialize registry
    registry = InFileIdentifierRegistry(str(json_file))

    fin_id_origin = registry.load(SelectorAsset())

    assert len(fin_id_origin) == 3

    pendings = [
        PendingIdentifierEntryUpdate(
            "apple",
            incoming=FinancialIdentifierEntry("AAPL", AssetType.EQUITY, currency="USD", isin=ISIN("US0378331005")),
            merged=FinancialIdentifierEntry("AAPL", AssetType.EQUITY, currency="USD", isin=ISIN("US0378331005")),
            original=fin_id_origin.find("apple"),
        ),
        PendingIdentifierEntryUpdate(
            "eurusd",
            incoming=FinancialIdentifierEntry("EURUSD=X", AssetType.FOREX),
            merged=FinancialIdentifierEntry("EURUSD=X", AssetType.FOREX),
            original=fin_id_origin.find("eurusd"),
        ),
        PendingIdentifierEntryUpdate(
            "new",
            incoming=FinancialIdentifierEntry("NEW", AssetType.DIGITAL_ASSET),
            merged=FinancialIdentifierEntry("NEW", AssetType.DIGITAL_ASSET),
            original=None,
        ),
    ]

    new_file, backup_file = registry.update_registry(pendings)

    assert new_file is not None
    assert new_file == os.path.join(tmp_path, "static_ids.json")
    assert backup_file == os.path.join(tmp_path, "static_ids2.json")

    #
    # file content
    #
    json_string = pathlib.Path(new_file).read_text(encoding="utf-8")
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
    "assetType": "INDEX",
    "isin": "FR0003500008"
  },
  "eurusd": {
    "yfTicker": "EURUSD=X",
    "assetType": "FOREX"
  },
  "new": {
    "yfTicker": "NEW",
    "assetType": "DIGITAL_ASSET"
  }
}"""
    )

    #
    # test log
    #
    pattern = r"file updated: .*/static_ids\.json"
    assert re.search(pattern, caplog.text), f"Pattern '{pattern}' not found in log: {caplog.text}"
    pattern = r"created backup file: .*/static_ids2\.json"
    assert re.search(pattern, caplog.text), f"Pattern '{pattern}' not found in log: {caplog.text}"
