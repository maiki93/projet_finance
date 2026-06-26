"""
Service to orchestrate retrieval and update of FinancialIdentifier and Asset models

Dependencies on
- IdentifierRegistry as source of Financial Identifers (static data)
- YfService / YfLibrary to retrieve data from Yahoo Finance (dynamic data)
"""

import logging

from yfinance_tools.domain import Asset, FinancialIdentifiers
from yfinance_tools.domain.exceptions import IdentifierError, YFinanceToolsError

from .outbound_ports import IdentifierRegistryPort, YFinancePort

logger = logging.getLogger(__name__)


class AssetService:
    """
    Main orchestrator, stateless component
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

        # load static data from the registry
        try:
            identifiers: FinancialIdentifiers = self._identifier_registry.load()
        except YFinanceToolsError as ex:
            logger.error(ex)
            raise ex

        # create assets
        assets = [
            Asset.asset_from_entry(entry)
            for name in identifiers.get_entries()
            if not isinstance(entry := identifiers.find(name), IdentifierError)
        ]

        # more verbose, with assert would crash if entry is not valid (IdentifierError)
        # assets: list[Asset] = []
        # for name in identifiers.get_entries():
        #     entry = identifiers.find(name)
        #     assert isinstance(entry, FinancialIdentifierEntry), f"Unexpected state: {type(entry)}"
        #     assets.append(Asset.asset_from_entry(entry))

        return assets
