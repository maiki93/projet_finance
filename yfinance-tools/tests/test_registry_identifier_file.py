"""
Adapter layer tests

test implementation of InFileIdentifierRegistry:
- load valid / invalid JSON file : create file in temporary directory
    - raise specific YFinanceToolsError
- validation of data (common) using DTO
    more on data validation in test_registry_identifier_validation.py
"""

from pathlib import Path

import pytest

import tests.utils as utils
from tests.conftest import NB_ITEMS_TEMPLATE_REGISTRY_DATA
from yfinance_tools.adapters import InFileIdentifierRegistry
from yfinance_tools.domain import FinancialIdentifiers
from yfinance_tools.domain.exceptions import IdentifierRegistryError, IdentifierRegistryFileNotExistingError


def test_load_identifier_from_file(tmp_path: Path, template_registry_data: dict):

    # create a valid temporary json file with the template data
    json_file = utils.create_file_with_content(tmp_path, "static_ids.json", template_registry_data)

    # initialize registry, no check
    registry = InFileIdentifierRegistry(str(json_file))

    # create domain object from file
    fin_id: FinancialIdentifiers = registry.load()

    assert len(fin_id) == NB_ITEMS_TEMPLATE_REGISTRY_DATA


def test_load_invalid_json_file(tmp_path: Path):

    json_file = utils.create_file_with_content(tmp_path, "invalid.json", "{]}")

    registry = InFileIdentifierRegistry(str(json_file))

    with pytest.raises(IdentifierRegistryError, match="invalid JSON format"):
        registry.load()


def test_load_file_do_not_exist(tmp_path: Path):

    # do not create file
    registry = InFileIdentifierRegistry(str(tmp_path / "static_ids.json"))

    # excinfo, alternative to match
    with pytest.raises(IdentifierRegistryFileNotExistingError) as excinfo:
        registry.load()
    # file path is reported in error message
    assert "static_ids.json" in str(excinfo)


def test_load_invalid_registry_extra_field(tmp_path: Path):

    # unexpected key
    data = {"eurusd": {"unexpected": "value", "yfTicker": "EURUSD=X", "isin": "", "asset_type": "forex"}}
    json_file = utils.create_file_with_content(tmp_path, "invalid_payload.json", data)

    registry = InFileIdentifierRegistry(str(json_file))

    with pytest.raises(IdentifierRegistryError, match="Extra inputs are not permitted"):
        registry.load()

    # fin_id: FinancialIdentifiers = registry.load()
    # assert len(fin_id) == 0
