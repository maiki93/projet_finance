"""
Common fixtures et template for unit tests

Provides a valid template of the registry data (one asset of each type)
A factory of AssetService with fakes adapters
"""

from pytest import fixture

from yfinance_tools.domain import FinancialIdentifiers
from yfinance_tools.services import AssetService, IdentifierRegistryPort, YFinancePort

from .fakes.fake_identifier_registry import FakeIdentifierRegistry
from .utils import fid_entry_from_dict

"""Number of items in the template_registry_data fixture"""
NB_ITEMS_TEMPLATE_REGISTRY_DATA = 6


# If modified (add an invalid entry) for tests MUST copy this template (easy to forget), or take out scope
@fixture(scope="session")
def template_registry_data() -> dict:
    return {
        "quantum": {
            "yfTicker": "QNT",
            "isin": "US7479066000",
            "assetType": "EQUITY",
        },
        "cac40": {
            "yfTicker": "^FCHI",
            "assetType": "INDEX",
            "currency": "EUR",
            "isin": "FR0003500008",
        },
        "eurusd": {"yfTicker": "EURUSD=X", "assetType": "FOREX", "isin": None},
        "bitcoin": {"yfTicker": "BTC-USD", "assetType": "DIGITAL_ASSET"},
        "natixis_horizon_40_44": {
            "yfTicker": "0P00014IGT.F",
            "assetType": "MUTUAL_FUND",
            "currency": "EUR",
            "isin": "FR0011461276",
        },
        "apple": {"yfTicker": "APPL"},
    }


@fixture(name="asset_service_factory_fake_registry")
def _asset_service_factory_fake_registry():
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


@fixture(name="asset_service_factory")
def _asset_service_factory():
    """
    Return a AssetService fully configurable

    Optional set exceptions thrown by adapters
    """

    def _build_service(
        registry_adapter: IdentifierRegistryPort,
        yfinance_adapter: YFinancePort,
    ) -> AssetService:

        return AssetService(registry_adapter, yfinance_adapter)

    return _build_service


@fixture(name="financial_identifier_factory")
def _financial_identifiers_factory():
    def _build_idientifiers(static_identifiers) -> FinancialIdentifiers:

        fin_id = FinancialIdentifiers()

        for name, items in static_identifiers.items():
            entry = fid_entry_from_dict(items)
            # fin_id.add_entry(name, entry)
            fin_id[name] = entry

        return fin_id

    return _build_idientifiers
