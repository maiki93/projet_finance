"""
Asset Service under Test

- outbound port IdentifierRegistryPort : FakeIdentifierRegistry (in memory only)
able to simulate errors (raise exception) or return a static dictionary of identifiers
- YFinancePort: Mock to set return values by test cases

Use case: update of static data, 2 steps
"""

import logging
import re
from typing import cast

import pytest

from tests.fakes.fake_identifier_registry import FakeIdentifierRegistry
from yfinance_tools.domain import (
    ISIN,
    AssetType,
    FinancialIdentifierEntry,
    IdentifierEntryDict,
    PendingIdentifierEntryUpdate,
)
from yfinance_tools.domain.selector_asset import SelectorAsset
from yfinance_tools.services import AssetService, YFinancePort

from .utils import fid_entry_from_dict


def create_initial_and_pending_update_for_get_static_data_update() -> tuple[dict, IdentifierEntryDict]:

    original_data = {
        "apple": {"yfTicker": "APPL"},
        "eurusd": {"yfTicker": "EURUSD=X"},
        "cac40": {"yfTicker": "^FCHI", "assetType": "INDEX", "isin": "FR0003500008"},
    }

    updated_data = {
        # add new data => accepted
        "apple": FinancialIdentifierEntry("APPL", AssetType.EQUITY, currency="USD", isin=ISIN("US0378331005")),
        "eurusd": FinancialIdentifierEntry("EURUSD=X", AssetType.FOREX),
        # missing currency but no more data provided => discarded
        "cac40": FinancialIdentifierEntry("^FCHI", AssetType.INDEX, isin=ISIN("FR0003500008")),
        # asset-type has been suppressed
        # brand new asset ids
        "new": FinancialIdentifierEntry("NEW", AssetType.DIGITAL_ASSET),
    }

    return (original_data, updated_data)


def test_get_pending_update(mocker, asset_service_factory) -> None:

    original_data, return_from_yfinance = create_initial_and_pending_update_for_get_static_data_update()

    # initilization of adapters: in-memory registry and mock of YFinancePort
    registry_identifier = FakeIdentifierRegistry(original_data)

    mock_yfinance_adapter = mocker.create_autospec(YFinancePort, instance=True)
    mock_yfinance_adapter.fetch_static_identifiers.return_value = return_from_yfinance

    service = asset_service_factory(registry_identifier, mock_yfinance_adapter)

    # tested method
    pendings: list[PendingIdentifierEntryUpdate] = service.get_static_data_pending_update(
        selector=SelectorAsset(), force_all=False
    )

    assert len(pendings) == 3
    assert "cac40" not in {pending.name for pending in pendings}
    assert {"eurusd", "apple", "new"} == {pending.name for pending in pendings}

    # it was called exactly 1 time
    mock_yfinance_adapter.fetch_static_identifiers.assert_called_once()
    assert mock_yfinance_adapter.fetch_static_identifiers.call_count == 1
    # mock_yfinance_adapter.fetch_static_identifiers.assert_called_once_with("AAPL")


def test_get_pendings_missing_yfadapter_dependecy(asset_service_factory):
    original_data, return_from_yfinance = create_initial_and_pending_update_for_get_static_data_update()

    # missing YFPort
    registry_identifier = FakeIdentifierRegistry(original_data)
    service = asset_service_factory(registry_identifier, None)

    with pytest.raises(RuntimeError, match="YFinancePort adapter is not initialized"):
        service.get_static_data_pending_update(force_all=False, selector=SelectorAsset())


def create_initial_and_pending_update_for_update_registry() -> tuple[dict, list[PendingIdentifierEntryUpdate]]:
    """Initialize update_registry data"""

    initial_data = {
        "apple": {"yfTicker": "APPL"},
        "cac40": {"yfTicker": "^FCHI", "isin": "FR0003500008", "assetType": "INDEX"},
        "eurusd": {"yfTicker": "EURUSD=X"},
    }

    # cac40 was discarded
    pendings = [
        # complete all fields
        PendingIdentifierEntryUpdate(
            "apple",
            incoming=FinancialIdentifierEntry("APPL", AssetType.EQUITY, currency="USD", isin=ISIN("US0378331005")),
            merged=FinancialIdentifierEntry("APPL", AssetType.EQUITY, currency="USD", isin=ISIN("US0378331005")),
            original=fid_entry_from_dict(initial_data["apple"]),
        ),
        # add asset_type
        PendingIdentifierEntryUpdate(
            "eurusd",
            incoming=FinancialIdentifierEntry("EURUSD=X", AssetType.FOREX),
            merged=FinancialIdentifierEntry("EURUSD=X", AssetType.FOREX),
            original=fid_entry_from_dict(initial_data["eurusd"]),
        ),
        # brand new asset
        PendingIdentifierEntryUpdate(
            "new",
            incoming=FinancialIdentifierEntry("NEW", AssetType.DIGITAL_ASSET),
            merged=FinancialIdentifierEntry("new", AssetType.DIGITAL_ASSET),
            # original = None
        ),
    ]
    return initial_data, pendings


def test_update_registry(asset_service_factory, caplog) -> None:
    caplog.set_level(logging.INFO)

    original_data, pendings_update = create_initial_and_pending_update_for_update_registry()

    registry_identifier = FakeIdentifierRegistry(original_data)
    service: AssetService = asset_service_factory(registry_identifier, None)

    # load done in previous stage of use case
    service.load_financial_identifier_from_registry(SelectorAsset())

    # update fin_id and registry
    filepath, assets = service.update_registry(pendings_update)

    assert "in_memory_static_assets.json" in filepath

    #
    # check FinancialIdentifier update
    #
    fin_id = service.fin_id

    assert fin_id is not None
    assert len(fin_id) == 4
    assert fin_id.find("new") is not None
    assert fin_id.find("apple").asset_type == AssetType.EQUITY

    #
    # check registry update (Fake)
    #
    in_memory_registry = cast(FakeIdentifierRegistry, service._identifier_registry)

    assert len(in_memory_registry.fake_static_identifiers) == 4
    assert "new" in in_memory_registry.fake_static_identifiers
    assert in_memory_registry.fake_static_identifiers["apple"]["assetType"] == "EQUITY"

    #
    # check return assets, only updated entries are returned
    #
    assert len(assets) == 3
    assert {"new", "eurusd", "apple"} == {asset.name for asset in assets}

    #
    # check logs of asset_service
    #
    assert "assets to be updated in registry: apple eurusd new" in caplog.text

    pattern = r"registry updated: .*/in_memory_static_assets\.json"
    assert re.search(pattern, caplog.text), f"Pattern '{pattern}' not found in log: {caplog.text}"

    pattern = r"backup resource: .*/in_memory_static_assets2\.json"
    assert re.search(pattern, caplog.text), f"Pattern '{pattern}' not found in log: {caplog.text}"


def test_update_registry_empty_pendings(asset_service_factory) -> None:
    registry_identifier = FakeIdentifierRegistry({})
    service: AssetService = asset_service_factory(registry_identifier, None)

    # update fin_id and registry
    filepath, assets = service.update_registry([])

    assert filepath == ""
    assert assets == []
