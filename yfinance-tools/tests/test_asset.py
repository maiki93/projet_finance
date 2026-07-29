"""
Domain core layer

- pure business logic, no depenendencies (mock if more complex behavior)
"""

import pytest

from tests.utils import fid_entry_from_dict_or_none
from yfinance_tools.domain import ISIN, Asset, AssetType, FinancialIdentifierEntry, SelectorAssetBuilder


def test_asset_yfticker_only_required() -> None:

    fin_id = FinancialIdentifierEntry("TOTO")
    asset1 = Asset.from_entry("toto", fin_id)

    assert asset1.name == "toto"
    assert asset1.yf_ticker == "TOTO"
    assert asset1.type == AssetType.UNDEFINED
    assert asset1.isin is None


def test_asset_construction_all_parameters() -> None:

    fin_id = FinancialIdentifierEntry("TOTO", asset_type=AssetType["EQUITY"], currency="EUR", isin=ISIN("FT0123456789"))
    asset = Asset("toto", fin_id)
    assert asset.name == "toto"
    assert asset.yf_ticker == "TOTO"
    assert asset.type == AssetType.EQUITY
    assert asset.currency == "EUR"
    assert asset.isin == ISIN("FT0123456789")


# TODO test internal implementation, not best
def test_store_copy_of_entry() -> None:

    fin_id = FinancialIdentifierEntry("TEST")
    asset = Asset.from_entry("test", fin_id)
    assert asset._static_identifiers == fin_id
    assert asset._static_identifiers is not fin_id


def test_invalid_name() -> None:
    with pytest.raises(ValueError, match="Invalid name format"):
        Asset.from_entry("a" * 52, FinancialIdentifierEntry("TEST"))

    with pytest.raises(ValueError, match="Invalid name format"):
        Asset.from_entry("", FinancialIdentifierEntry("TEST"))


def test_to_json() -> None:
    # only required
    fin_id = FinancialIdentifierEntry("EURUSD=X")
    asset = Asset.from_entry("eurusd", fin_id)

    expected_json_str = (
        '{"name": "eurusd", "yf_ticker": "EURUSD=X", "type": "UNDEFINED", "currency": null, "isin": null}'
    )

    str_json = asset.to_json()
    assert str_json == expected_json_str

    # all entries
    fin_id2 = FinancialIdentifierEntry("QNT", asset_type=AssetType["EQUITY"], currency="USD", isin=ISIN("US7479066000"))
    expected_json_str2 = (
        '{"name": "quantum", "yf_ticker": "QNT", "type": "EQUITY", "currency": "USD", "isin": "US7479066000"}'
    )

    asset2 = Asset.from_entry("quantum", fin_id2)
    str_json2 = asset2.to_json()

    assert str_json2 == expected_json_str2


@pytest.mark.parametrize(
    "name, type, expected", [(None, "EQUITY", 1), ("eurusd", None, 1), (None, None, 6), ("bitcoin", "EQUITY", 2)]
)
def test_selector_asset(financial_identifier_factory, template_registry_data, name, type, expected) -> None:

    fin_id = financial_identifier_factory(template_registry_data)

    selector = SelectorAssetBuilder().with_name(name).with_type(type).build()

    fin_id = {
        name: fid_entry
        for name, entry in template_registry_data.items()
        if (fid_entry := selector.as_filter(name, fid_entry_from_dict_or_none(entry))) is True
    }

    assert len(fin_id) == expected
    if name:
        assert name in fin_id
