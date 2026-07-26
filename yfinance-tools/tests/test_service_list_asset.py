"""
Asset Service under Test

- outbound port IdentifierRegistryPort : FakeIdentifierRegistry (in memory only)
able to simulate errors (raise exception) or return a static dictionary of identifiers

Use case: list-asset
"""

import pytest

from tests.conftest import NB_ITEMS_TEMPLATE_REGISTRY_DATA
from yfinance_tools.domain import Asset
from yfinance_tools.domain.exceptions import YFinanceToolsError
from yfinance_tools.domain.filter_asset import FilterAsset, FilterAssetBuilder


def test_get_list_of_all_assets(asset_service_factory_fake_registry, template_registry_data) -> None:

    assets: list[Asset] = asset_service_factory_fake_registry(template_registry_data).list_assets(
        selector=FilterAsset()
    )

    assert len(assets) == NB_ITEMS_TEMPLATE_REGISTRY_DATA


def test_get_list_type_equity(asset_service_factory_fake_registry, template_registry_data) -> None:

    filter = FilterAssetBuilder().with_type("EQUITY").build()
    assets: list[Asset] = asset_service_factory_fake_registry(template_registry_data).list_assets(selector=filter)

    assert len(assets) == 1


def test_get_list_name(asset_service_factory_fake_registry, template_registry_data) -> None:

    filter = FilterAssetBuilder().with_name("cac40").build()
    assets: list[Asset] = asset_service_factory_fake_registry(template_registry_data).list_assets(selector=filter)

    assert len(assets) == 1


def test_identifier_registry_error(asset_service_factory_fake_registry) -> None:

    asset_service = asset_service_factory_fake_registry({}, error_registry=YFinanceToolsError("RegistryError"))
    with pytest.raises(YFinanceToolsError, match="RegistryError"):
        asset_service.list_assets(selector=FilterAsset())
