"""
Core domain model unit testing, no external dependencies:
- input data provided by a common template (fixture), or specific to each test
- fixture factory to factorize the initialization of the model

Most of data validation is done in adpater (from IdentifierDto)
"""

import pytest

from tests.conftest import NB_ITEMS_TEMPLATE_REGISTRY_DATA
from yfinance_tools.domain import ISIN, AssetType, FinancialIdentifierEntry, FinancialIdentifiers, IdentifierEntryDict
from yfinance_tools.domain.exceptions import IdentifierError


def test_get_all_names(financial_identifier_factory, template_registry_data) -> None:

    fin_id = financial_identifier_factory(template_registry_data)

    all_asset_name = fin_id.get_entries()

    assert len(all_asset_name) == NB_ITEMS_TEMPLATE_REGISTRY_DATA
    assert "eurusd" in all_asset_name
    assert "bitcoin" in all_asset_name


def test_find_by_name(financial_identifier_factory, template_registry_data) -> None:
    fin_id = financial_identifier_factory(template_registry_data)

    quantum: FinancialIdentifierEntry = fin_id.find("quantum")

    assert quantum is not None
    assert quantum.asset_type == "EQUITY"
    assert quantum.yf_ticker == "QNT"


def test_name_not_found_raise_error(financial_identifier_factory, template_registry_data) -> None:
    fin_id = financial_identifier_factory(template_registry_data)

    with pytest.raises(IdentifierError, match="Asset name not found: toto"):
        fin_id.find("toto")


def test_candidate_for_update(financial_identifier_factory, template_registry_data) -> None:

    fin_id = financial_identifier_factory(template_registry_data)

    entries_to_check_update = fin_id.candidates_for_update(force_all=False)

    # cac40 and natixis are complete
    assert len(entries_to_check_update) == NB_ITEMS_TEMPLATE_REGISTRY_DATA - 2

    # copy of original (deepcopy performed)
    assert "natixis_horizon_40_44" not in entries_to_check_update
    assert "cac40" not in entries_to_check_update


def test_candidates_for_update_are_copy_forced_all(financial_identifier_factory, template_registry_data) -> None:

    fin_id = financial_identifier_factory(template_registry_data)

    entries_to_check_update = fin_id.candidates_for_update(force_all=True)

    assert len(entries_to_check_update) == NB_ITEMS_TEMPLATE_REGISTRY_DATA
    assert fin_id._entries["apple"] == entries_to_check_update["apple"]
    assert fin_id._entries["apple"] is not entries_to_check_update["apple"]
    assert fin_id._entries["cac40"] == entries_to_check_update["cac40"]
    assert fin_id._entries["cac40"] is not entries_to_check_update["cac40"]


def test_pending_update_with_new_data(financial_identifier_factory) -> None:
    data = {"apple": {"yfTicker": "APPL"}}
    fin_id: FinancialIdentifiers = financial_identifier_factory(data)

    new_entry = FinancialIdentifierEntry("APPL", AssetType.EQUITY, currency="USD", isin=ISIN("US0378331005"))
    new_data: IdentifierEntryDict = {"apple": new_entry}

    pending_update = fin_id.evaluate_pending_update(new_data)

    assert type(pending_update) is list
    assert len(pending_update) == 1
    assert pending_update[0].name == "apple"
    assert pending_update[0].original == fin_id.find("apple")
    assert pending_update[0].incoming == new_entry
    assert pending_update[0].merged.yf_ticker == "APPL"
    assert pending_update[0].merged.asset_type == AssetType.EQUITY
    assert pending_update[0].merged.currency == "USD"
    assert pending_update[0].merged.asset_type == AssetType.EQUITY
    assert pending_update[0].merged.isin == new_entry.isin


def test_pending_update_with_same_data(financial_identifier_factory) -> None:
    data = {"apple": {"yfTicker": "APPL", "asset_type": "EQUITY"}}
    fin_id: FinancialIdentifiers = financial_identifier_factory(data)

    # exactly same data
    new_entry = FinancialIdentifierEntry("APPL", AssetType.EQUITY)
    new_data: IdentifierEntryDict = {"apple": new_entry}

    pending_update = fin_id.evaluate_pending_update(new_data)

    assert len(pending_update) == 0


def test_pending_update_with_new_asset(financial_identifier_factory) -> None:
    fin_id: FinancialIdentifiers = financial_identifier_factory({})

    new_entry = FinancialIdentifierEntry("APPL", AssetType.EQUITY)
    new_data: IdentifierEntryDict = {"apple": new_entry}

    pending_update = fin_id.evaluate_pending_update(new_data)

    assert len(pending_update) == 1
    assert pending_update[0].merged.asset_type == AssetType.EQUITY


def test_pending_rejected_because_less_data(financial_identifier_factory) -> None:

    data = {"apple": {"yfTicker": "APPL", "currency": "USD"}}
    fin_id = financial_identifier_factory(data)

    new_data: IdentifierEntryDict = {"apple": FinancialIdentifierEntry("APPL")}

    pending_update = fin_id.evaluate_pending_update(new_data)

    assert len(pending_update) == 0


def test_pending_rejected_because_lost_asset_type(financial_identifier_factory) -> None:

    data = {"apple": {"yfTicker": "APPL", "asset_type": "EQUITY"}}
    fin_id = financial_identifier_factory(data)

    new_data: IdentifierEntryDict = {"apple": FinancialIdentifierEntry("APPL")}

    pending_update = fin_id.evaluate_pending_update(new_data)

    assert len(pending_update) == 0


def test_pending_merged_with_original_type(financial_identifier_factory) -> None:

    data = {"apple": {"yfTicker": "APPL", "asset_type": "EQUITY"}}
    fin_id = financial_identifier_factory(data)

    # original asset_type was present in original
    new_data: IdentifierEntryDict = {"apple": FinancialIdentifierEntry("APPL", currency="USD")}

    pending_update = fin_id.evaluate_pending_update(new_data)

    assert len(pending_update) == 1
    assert pending_update[0].merged.asset_type == AssetType.EQUITY
    assert pending_update[0].merged.currency == "USD"
