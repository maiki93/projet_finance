"""
Domain core layer

- pure business logic, at core, no depenendencies (mock if more complex behavior)
"""

import pytest

from yfinance_tools.domain import ISIN, Asset, AssetType


def test_asset_construction_only_required_parameters():

    asset1 = Asset("toto", AssetType["INDEX"])
    assert asset1.name == "toto"
    assert asset1.type == AssetType.INDEX
    assert asset1.isin is None
    assert asset1.yf_ticker is None


def test_asset_construction_all_parameters():

    asset = Asset("toto", AssetType["INDEX"], ISIN("FT0123456789"), "TOTO")
    assert asset.name == "toto"
    assert asset.type == AssetType.INDEX
    assert asset.isin == ISIN("FT0123456789")
    assert asset.yf_ticker == "TOTO"


@pytest.mark.parametrize("invalid_isin", ["not-an-isin", "120123456789", "fr0123456789"])
def test_invalid_isin(invalid_isin: str):
    with pytest.raises(ValueError, match="Invalid ISIN format"):
        Asset("invalid", AssetType.EQUITY, isin=ISIN(invalid_isin))


def test_to_json():

    asset = Asset("eurusd", AssetType.FOREX, None, None)
    str_json = asset.to_json()
    assert str_json == '{"name": "eurusd", "type": "FOREX", "isin": null, "yf_ticker": null}'

    asset = Asset(
        "eurusd",
        AssetType.FOREX,
        ISIN("FR0123456789"),
        "EURUSD=X",
    )
    str_json = asset.to_json()
    assert str_json == '{"name": "eurusd", "type": "FOREX", "isin": "FR0123456789", "yf_ticker": "EURUSD=X"}'
