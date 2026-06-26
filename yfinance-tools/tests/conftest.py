"""
Common fixtures et template for unit tests

Provides a valid template of the registry data (one asset of each type)
A factory of AssetService with fakes adapters
"""

from pytest import fixture

from yfinance_tools.domain import ISIN, AssetType, FinancialIdentifierEntry, FinancialIdentifiers
from yfinance_tools.services import AssetService

from .fakes import FakeIdentifierRegistry

"""Number of items in the template_registry_data fixture"""
NB_ITEMS_TEMPLATE_REGISTRY_DATA = 5


# TODO Need to return an immutable dict ? not yet (read-only for the moment)
# scope seesion, shared across all tests
@fixture(scope="session")
def template_registry_data() -> dict:
    return {
        "quantum": {
            "yfTicker": "QNT",
            "isin": "US7479066000",
            "asset_type": "EQUITY",
        },
        "cac40": {
            "yfTicker": "^FCHI",
            "isin": "FR0003500008",
            "asset_type": "INDEX",
        },
        "eurusd": {"yfTicker": "EURUSD=X", "asset_type": "FOREX", "isin": None},
        "bitcoin": {"yfTicker": "BTC-USD", "asset_type": "DIGITAL_ASSET"},  # "isin": None},
        "natixis_horizon_40_44": {
            "yfTicker": "0P00014IGT.F",
            "isin": "FR0011461276",
            "asset_type": "MUTUAL_FUND",
        },
    }


@fixture(name="asset_service_factory")
def _asset_service_factory():
    """
    Return a AssetService configured with a FakeIdentifierRegistry.

    Optional set exceptions thrown by adapters
    """

    def _build_service(static_identifiers, error_registry: Exception | None = None) -> AssetService:
        registry_identifier = FakeIdentifierRegistry(static_identifiers)
        if error_registry:
            registry_identifier.set_exception(error_registry)

        return AssetService(registry_identifier, None)

    return _build_service


@fixture(name="financial_identifier_factory")
def _financial_identifiers_factory():
    def _build_idientifiers(static_identifiers):

        ## TODO too verbose
        fin_id = FinancialIdentifiers()

        for name, items in static_identifiers.items():
            # pythonic alternative: self._entries.get(name, _not_found) ??
            entry = FinancialIdentifierEntry(
                name,
                AssetType(items["asset_type"]) if items.get("asset_type") is not None else AssetType.UNDEFINED,
                items["yfTicker"] if items.get("yfTicker") is not None else None,
                ISIN(value=items["isin"]) if items.get("isin") else None,
            )
            fin_id.add_entry(entry)

        return fin_id

    return _build_idientifiers
