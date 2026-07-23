"""
Service to orchestrate retrieval and update of FinancialIdentifier and Asset models

External dependencies on
- IdentifierRegistry as source of Financial Identifers storage (static data)
- YfService / YfLibrary to retrieve data from Yahoo Finance (dynamic data)
"""

import logging

from yfinance_tools.domain import Asset, FinancialIdentifiers, PendingIdentifierEntryUpdate
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
        # lazy-loaded on demand
        self._fin_id: FinancialIdentifiers | None = None

    @property
    def financial_identifiers(self) -> FinancialIdentifiers:
        """Lazy load on first access."""
        if self._fin_id is None:
            try:
                self._fin_id = self._identifier_registry.load()
            except YFinanceToolsError as ex:
                logger.error(ex)
                raise ex

        return self._fin_id

    def list_assets(self) -> list[Asset]:
        """
        Return the list of all Assets present in the identifier registry.
        """

        # create assets
        assets = [
            Asset.from_entry(name, entry)
            for name in self.financial_identifiers.get_entries()
            if not isinstance(entry := self.financial_identifiers.find(name), IdentifierError)
        ]

        return assets

    def get_static_data_pending_update(self, force_all: bool) -> list[PendingIdentifierEntryUpdate]:
        """
        Fetch web to get the most recent static data
        1st step of 2 stage commit

        force_all: do not check previous missing data, force all assets
        """

        # optimal, filtering MAY be done in getting the data (post filter for file, efficiency for DB, TUI apply after)
        fin_id = self.financial_identifiers

        # can reuse by  _get_yfianace_adapter()-> YFinancePort
        if self._yfinance is None:
            raise RuntimeError("YFinancePort adapter is not initialized")

        # get yf_ticker() more specific (may need Type definition)
        incoming_static_update = self._yfinance.fetch_static_identifiers(
            self.financial_identifiers.candidates_for_update(force_all)
        )

        # compute diff with previous data in memory
        pending_static_update = fin_id.evaluate_pending_update(incoming_static_update)

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
            self.financial_identifiers.update_entry(pending.name, pending.merged)

        # apply update to the registry
        updated_resource, backup_resource = self._identifier_registry.update_registry(pending_update)

        # need python-json-logger to easily add extra fields
        # logger.info(f"registry updated: {updated_resource}", extra={"backup_resource": backup_resource})
        logger.info(f"registry updated: {updated_resource}")
        if backup_resource:
            logger.info(f"backup resource: {backup_resource}")

        # potential asset update (TUI application)
        # CLI print the data with last values
        list_updated = [pending.name for pending in pending_update]
        # create assets
        assets = [
            Asset.from_entry(name, entry)
            for name in list_updated
            if not isinstance(entry := self.financial_identifiers.find(name), IdentifierError)
        ]

        # updated is a notification
        return str(updated_resource), assets
