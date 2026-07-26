""" """

import pytest

from yfinance_tools.domain import AssetType, FilterAsset, FilterAssetBuilder


def test_default_inactive():

    filter = FilterAssetBuilder().build()
    assert filter.is_active is False

    filter = FilterAsset()
    assert filter.is_active is False

    # construct in CLI
    filter = FilterAssetBuilder().with_name(None).with_type(None).build()
    assert filter.is_active is False


def test_valid_asset_type() -> None:

    filter: FilterAsset = FilterAssetBuilder().with_type("EQUITY").build()

    assert filter.type == AssetType.EQUITY
    assert filter.name is None
    assert filter.is_active is True

    filter: FilterAsset = FilterAssetBuilder().with_type("forex").build()

    assert filter.type == AssetType.FOREX
    assert filter.name is None
    assert filter.is_active is True

    #  depends on AssetType(..) or AssetType[...]
    with pytest.raises(ValueError, match="INVALID"):
        # with pytest.raises(KeyError, match="INVALID"):
        FilterAssetBuilder().with_type("INVALID").build()


def test_filter_name():

    filter: FilterAsset = FilterAssetBuilder().with_name("toto").build()

    assert filter.name == "toto"
    assert filter.type is None
    assert filter.is_active is True


def test_cli_usage():

    filter: FilterAsset = FilterAssetBuilder().with_name("toto").with_type(None).build()

    assert filter.name == "toto"
    assert filter.type is None
    assert filter.is_active is True
