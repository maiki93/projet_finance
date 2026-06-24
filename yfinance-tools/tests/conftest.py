"""
Common fixtures
"""

from pytest import fixture

from yfinance_tools.services import AssetService

from .fakes import FakeIdentifierRegistry

#
# this template input proposes an asset of each type
#
# number of items in the template_registry_data fixture
NB_ITEMS_TEMPLATE_REGISTRY_DATA = 5


# TODO Need to return a copy or immutable dict ? not yet (read-only)
@fixture
def template_registry_data() -> dict:
    return {
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


@fixture(name="asset_service_factory")
def _asset_service_factory():
    """Return a AssetService configured with a FakeIdentifierRegistry accepting static_data"""

    def _build_service(static_identifiers):
        registry_identifier = FakeIdentifierRegistry(static_identifiers)
        return AssetService(registry_identifier, None)

    return _build_service
