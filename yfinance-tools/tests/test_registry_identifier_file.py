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
import re
from pathlib import Path

import pytest

import tests.utils as utils
from tests.conftest import NB_ITEMS_TEMPLATE_REGISTRY_DATA
from yfinance_tools.adapters import InFileIdentifierRegistry
from yfinance_tools.domain import ISIN, AssetType, FinancialIdentifierEntry, FinancialIdentifiers
from yfinance_tools.domain.exceptions import IdentifierRegistryError, IdentifierRegistryFileNotExistingError
from yfinance_tools.domain.financial_identifier_entry import PendingIdentifierEntryUpdate


def test_load_identifier_from_file(tmp_path: Path, template_registry_data) -> None:

    # create a valid temporary json file with the template data
    json_file = utils.create_file_with_content(tmp_path, "static_ids.json", template_registry_data)

    # initialize registry, no check
    registry = InFileIdentifierRegistry(str(json_file))

    # create domain object from file
    fin_id: FinancialIdentifiers = registry.load()

    assert len(fin_id) == NB_ITEMS_TEMPLATE_REGISTRY_DATA

    assert fin_id.find("quantum").yf_ticker == "QNT"
    assert fin_id.find("cac40").currency == "EUR"
    assert fin_id.find("eurusd").asset_type == "FOREX"
    assert fin_id.find("natixis_horizon_40_44").isin == "FR0011461276"


def test_load_invalid_json_file(tmp_path: Path) -> None:

    json_file = utils.create_file_with_content(tmp_path, "invalid.json", "{]}")

    registry = InFileIdentifierRegistry(str(json_file))

    with pytest.raises(IdentifierRegistryError, match="Invalid JSON format"):
        registry.load()


def test_load_file_do_not_exist(tmp_path: Path) -> None:

    # do not create file
    registry = InFileIdentifierRegistry(str(tmp_path / "static_ids.json"))

    # excinfo, alternative to match
    with pytest.raises(IdentifierRegistryFileNotExistingError) as excinfo:
        registry.load()
    # file path is reported in error message
    assert "static_ids.json" in str(excinfo)


def test_update_registry(caplog, tmp_path: Path, template_registry_data: dict) -> None:
    caplog.set_level(logging.INFO)

    data_origin = {
        "apple": {"yfTicker": "APPL"},
        "cac40": {"yfTicker": "^FCHI", "isin": "FR0003500008", "asset_type": "INDEX"},
        "eurusd": {"yfTicker": "EURUSD=X"},
    }

    json_file = utils.create_file_with_content(tmp_path, "static_ids.json", data_origin)

    # initialize registry
    registry = InFileIdentifierRegistry(str(json_file))

    fin_id_origin = registry.load()

    assert len(fin_id_origin) == 3

    pendings = [
        PendingIdentifierEntryUpdate(
            "apple",
            incoming=FinancialIdentifierEntry("APPL", AssetType.EQUITY, currency="USD", isin=ISIN("US0378331005")),
            merged=FinancialIdentifierEntry("APPL", AssetType.EQUITY, currency="USD", isin=ISIN("US0378331005")),
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

    assert new_file == os.path.join(tmp_path, "static_ids.json")
    assert backup_file == os.path.join(tmp_path, "static_ids2.json")

    # TODO test content, it is rather a serialization test

    #
    # test log
    #
    pattern = r"file updated: .*/static_ids\.json"
    assert re.search(pattern, caplog.text), f"Pattern '{pattern}' not found in log: {caplog.text}"
    pattern = r"created backup file: .*/static_ids2\.json"
    assert re.search(pattern, caplog.text), f"Pattern '{pattern}' not found in log: {caplog.text}"
