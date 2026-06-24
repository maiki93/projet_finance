"""
Service to orchestrate retrieval and update of FinancialIdentifier and Asset models

Use of YfService and FinancialIdentifierSource Protcol
"""

import logging

from yfinance_tools.domain import Asset, AssetType, FinancialIdentifier
from yfinance_tools.domain.exceptions import YFinanceToolsError

from .outbound_ports import IdentifierRegistryPort, YFinancePort

logger = logging.getLogger(__name__)


class AssetService:
    """
    Main orchestrator.

    Stateless component
    """

    def __init__(
        self,
        identifier_registry: IdentifierRegistryPort,
        yfinance_api: YFinancePort | None,
    ):
        self._identifier_registry = identifier_registry
        self._yfinance = yfinance_api

    def list_assets(self) -> list[Asset]:
        """
        Return the list of all Assets present in the identifier registry.
        available in FinancialIdentifier Source
        """

        asset_static_ids = {}

        # a better usage ?
        # assets = AssetFactory.byAssetType(asset_type)
        #                      .byMarket(market)

        # load static data from the registry to build domain models
        try:
            asset_static_ids = self._identifier_registry.load()
        except YFinanceToolsError as ex:
            logger.error(ex)
            raise ex

        identifier = FinancialIdentifier(asset_static_ids)
        assets: list[Asset] = []
        # for name, data in asset_static_ids.items():
        for name in identifier.get_entries():
            data = identifier.find(name)
            asset = Asset(name, AssetType[data["type"]], data["yfIsin"], data["yfTicker"])
            assets.append(asset)
        return assets
