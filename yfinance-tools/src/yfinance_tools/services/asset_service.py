"""
Service to orchestrate retrieval and update of FinancialIdentifier and Asset models

External dependencies on
- IdentifierRegistry as source of Financial Identifers storage (static data)
- YfService / YfLibrary to retrieve data from Yahoo Finance (dynamic data)
"""

import logging

from yfinance_tools.domain import Asset, FinancialIdentifiers, PendingIdentifierEntryUpdate
from yfinance_tools.domain.exceptions import IdentifierError, YFinanceToolsError
from yfinance_tools.domain.filter_asset import FilterAsset

from .outbound_ports import IdentifierRegistryPort, YFinancePort

logger = logging.getLogger(__name__)


class AssetService:
    """
    Orchestrator between domain models
    """

    def __init__(
        self,
        identifier_registry: IdentifierRegistryPort,
        yfinance_api: YFinancePort | None,
    ):
        self._identifier_registry = identifier_registry
        self._yfinance = yfinance_api

        # break stateless
        self._financial_identifiers: FinancialIdentifiers | None = None

    def load_financial_identifier_from_registry(self, selector: FilterAsset) -> None:
        """
        Load financial identifier from the registry.
        It is stored in AssetService, accessible by property .fin_id
        """
        try:
            self._financial_identifiers = self._identifier_registry.load(selector=selector)
        except YFinanceToolsError as ex:
            logger.error(ex)
            raise ex

    @property
    def fin_id(self) -> FinancialIdentifiers:
        """Return financial_identifiers, raise Error if not present"""
        assert self._financial_identifiers is not None
        return self._financial_identifiers

    # no reason to have None for filter (always created) => just a filter which accepts everything
    def list_assets(self, selector: FilterAsset) -> list[Asset]:
        """
        Return the list of all Assets present in the identifier registry.
        """

        self.load_financial_identifier_from_registry(selector)

        # create assets
        assets = [
            Asset.from_entry(name, entry)
            for name in self.fin_id.get_entries()
            if not isinstance(entry := self.fin_id.find(name), IdentifierError)
        ]

        return assets

    def get_static_data_pending_update(
        self,
        selector: FilterAsset,
        force_all: bool,
    ) -> list[PendingIdentifierEntryUpdate]:
        """
        Fetch web to get the most recent static data
        1st step of 2 stage commit

        force_all: do not check previous missing data, force all assets
        """

        if self._yfinance is None:
            raise RuntimeError("YFinancePort adapter is not initialized")

        self.load_financial_identifier_from_registry(selector)

        # fetch data for assets which are incomplete or force for all
        candidates = self.fin_id.candidates_for_update(force_all)
        incoming_static_update = self._yfinance.fetch_static_identifiers(candidates)

        # compute diff with previous data in memory
        pending_static_update = self.fin_id.evaluate_pending_update(incoming_static_update)

        return pending_static_update

    # should have more logic here ?? Human validation done before
    def update_registry(self, pending_update: list[PendingIdentifierEntryUpdate]) -> tuple[str, list[Asset]]:
        """
        Update static data after user validation

        Both in memory (FinancialIdentifiers) and storage are updated
        2nd step of 2 stage commit
        """

        if len(pending_update) == 0:
            return "", []

        logger.info(f"assets to be updated in registry: {' '.join([p.name for p in pending_update])}")

        # apply update to model - in memory storage
        for pending in pending_update:
            self.fin_id.update_entry(pending.name, pending.merged)

        # apply update to the registry
        updated_resource, backup_resource = self._identifier_registry.update_registry(pending_update)
        # need python-json-logger to easily add extra fields
        logger.info(f"registry updated: {updated_resource}")
        if backup_resource:
            logger.info(f"backup resource: {backup_resource}")

        # potential asset update (TUI application)
        # return to CLI the data with last values
        list_updated = [pending.name for pending in pending_update]

        # create assets
        assets = [
            Asset.from_entry(name, entry)
            for name in list_updated
            if not isinstance(entry := self.fin_id.find(name), IdentifierError)
        ]

        # updated is a notification
        return str(updated_resource), assets
