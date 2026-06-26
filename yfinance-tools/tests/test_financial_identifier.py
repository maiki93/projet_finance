"""
Core domain model unit testing, no external dependencies:
- input data provided by a common template (fixture), or specific to each test
- fixture factory to factorize the initialization of the model

Most of data validation is done in adpater (from IdentifierDto)
"""

import pytest

from tests.conftest import NB_ITEMS_TEMPLATE_REGISTRY_DATA
from yfinance_tools.domain import FinancialIdentifierEntry
from yfinance_tools.domain.exceptions import IdentifierError
from yfinance_tools.domain.financial_identifier import FinancialIdentifiers
from yfinance_tools.domain.financial_models import AssetType


def test_get_all_names(financial_identifier_factory, template_registry_data):

    fin_id = financial_identifier_factory(template_registry_data)

    all_asset_name = fin_id.get_entries()

    assert len(all_asset_name) == NB_ITEMS_TEMPLATE_REGISTRY_DATA
    assert "eurusd" in all_asset_name
    assert "bitcoin" in all_asset_name


def test_find_by_name(financial_identifier_factory, template_registry_data):
    fin_id = financial_identifier_factory(template_registry_data)

    quantum: FinancialIdentifierEntry = fin_id.find("quantum")
    print(quantum)
    assert quantum is not None
    assert quantum.name == "quantum"
    assert quantum.type == "EQUITY"
    assert quantum.yfTicker == "QNT"


def test_name_not_found_raise_error(financial_identifier_factory, template_registry_data):
    fin_id = financial_identifier_factory(template_registry_data)

    with pytest.raises(IdentifierError, match="Asset name not found: toto"):
        fin_id.find("toto")


# keep to check for Optional argument later
def test_required_attributes():
    # no provided dataclasses functionalities to have option in constructor ?
    # yes typing.Option or use classmethod => easier use in Dto
    entry = FinancialIdentifierEntry("test", AssetType.EQUITY, None, None)
    fin_id = FinancialIdentifiers()
    fin_id.add_entry(entry)

    assert len(fin_id) == 1
