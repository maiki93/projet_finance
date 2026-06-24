"""
Common fixtures
"""

from pytest import fixture

from yfinance_tools.services import AssetService

from .fakes import FakeIdentifierRegistry


# this standard input proposes an asset of each type
# more flexible to use as fixture
# TODO return copy or immutable dict ?
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
    """Return a AssetService configured with a FinancialIdentifierInMemory accepting static_data"""

    def _build_service(static_identifiers):
        # identifier = InMemoryIdentifierRegistry(dictionary_data)
        registry_identifier = FakeIdentifierRegistry(static_identifiers)
        return AssetService(registry_identifier, None)

    return _build_service


# not needed of this implementation
# @fixture(name="in_memory_identifier_factory")
# def _in_memory_identifier_factory():
#     """Returns a factory of FinancialIdentifierInMemory accepting static_data"""

#     def _build_instance(dictionary_data):
#         identifier = InMemoryIdentifierRegistry(dictionary_data)
#         return identifier

#     return _build_instance
