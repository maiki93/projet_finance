""" """

import pytest

from yfinance_tools.domain import AssetType, SelectorAsset, SelectorAssetBuilder


def test_default_inactive():

    filter = SelectorAssetBuilder().build()
    assert filter.is_active is False

    filter = SelectorAsset()
    assert filter.is_active is False

    # construct in CLI
    filter = SelectorAssetBuilder().with_name(None).with_type(None).build()
    assert filter.is_active is False


def test_valid_asset_type() -> None:

    filter: SelectorAsset = SelectorAssetBuilder().with_type("EQUITY").build()

    assert filter.type == AssetType.EQUITY
    assert filter.name is None
    assert filter.is_active is True

    filter: SelectorAsset = SelectorAssetBuilder().with_type("forex").build()

    assert filter.type == AssetType.FOREX
    assert filter.name is None
    assert filter.is_active is True

    #  depends on AssetType(..) or AssetType[...]
    with pytest.raises(ValueError, match="INVALID"):
        # with pytest.raises(KeyError, match="INVALID"):
        SelectorAssetBuilder().with_type("INVALID").build()


def test_filter_name():

    filter: SelectorAsset = SelectorAssetBuilder().with_name("toto").build()

    assert filter.name == "toto"
    assert filter.type is None
    assert filter.is_active is True


def test_cli_usage():

    filter: SelectorAsset = SelectorAssetBuilder().with_name("toto").with_type(None).build()

    assert filter.name == "toto"
    assert filter.type is None
    assert filter.is_active is True
