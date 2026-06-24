"""
Asset Service under Test

Build service with implementation of FinancialIdentifier(in memory) and YfinanceGw(mock)
"""

from pytest import fixture

from tests.fakes import FakeIdentifierRegistry
from yfinance_tools.services import AssetService

# @fixture(name="identifier_factory")
# def _identifier_factory():
#     """Returns a factory of FinancialIdentifierInMemory accepting static_data"""

#     def _build_service(dictionary_data):
#         identifier = FinancialIdentifierInMemory(dictionary_data)
#         return AssetService(identifier, None)

#     return _build_service


@fixture(name="fake_identifier_registry")
def _identifier_registry():
    """Set up an Asset Service with predefined in-memory FinancialIdentifier"""

    dummy_data = {
        "quantum": {
            "yfTicker": "QNT",
            "yfIsin": "US7479066000",
            "type": "EQUITY",
        },
        "cac40": {
            "yfTicker": "^FCHI",
            "yfIsin": "FR0003500008",
            "type": "INDEX",
        },
        "eurusd": {"yfTicker": "EURUSD=X", "yfIsin": "", "type": "FOREX"},
        "bitcoin": {"yfTicker": "BTC-USD", "yfIsin": "", "type": "DIGITAL_ASSET"},
        "natixis_horizon_40_44": {
            "yfTicker": "0P00014IGT.F",
            "yfIsin": "FR0011461276",
            "type": "MUTUAL_FUND",
        },
    }

    # identifier = InMemoryIdentifierRegistry(dummy_data)
    identifier_registry = FakeIdentifierRegistry(dummy_data)

    service = AssetService(identifier_registry, None)
    return service


def test_get_list_of_all_assets(asset_service_factory, template_registry_data):
    assets = asset_service_factory(template_registry_data).list_assets()

    assert len(assets) == 5


# def test_minimal_asset_field(in_memory_service_factory):
#     dummy = {"eurusd": {"type": "FOREX", "yfTicker": "EURUSD=X", "yfIsin": "12345"}}
#     service = in_memory_service_factory(dummy)

#     assets = service.list_assets()
#     assert len(assets) == 1
#     assert assets[0].type == AssetType.FOREX
