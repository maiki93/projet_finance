"""
Service to orchestrate retrieval and update of FinancialIdentifier and Asset models

External dependencies on
- IdentifierRegistry as source of Financial Identifers storage (static data)
- YfService / YfLibrary to retrieve data from Yahoo Finance (dynamic data)
"""

import logging

from yfinance_tools.domain import Asset, FinancialIdentifiers, PendingIdentifierEntryUpdate, SelectorAsset
from yfinance_tools.domain.exceptions import IdentifierError, YFinanceToolsError

from .outbound_ports import ConfirmationCallback, IdentifierRegistryPort, YFinancePort

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

    def load_financial_identifier_from_registry(self, selector: SelectorAsset) -> FinancialIdentifiers:
        """
        Load financial identifier from the registry.
        It is NOT stored in AssetService, respect stateless property of a Service
        """
        try:
            fin_id = self._identifier_registry.load(selector=selector)
        except YFinanceToolsError as ex:
            logger.error(ex)
            raise ex

        return fin_id

    def list_assets(self, selector: SelectorAsset) -> list[Asset]:
        """
        Return the list of all Assets present in the identifier registry.
        """

        fin_id = self.load_financial_identifier_from_registry(selector)

        # create assets
        assets = [
            Asset.from_entry(name, entry)
            for name in fin_id.get_entries()
            if not isinstance(entry := fin_id.find(name), IdentifierError)
        ]

        return assets

    def update_static_data(
        self, selector: SelectorAsset, force_all: bool, ui_confirm_cb: ConfirmationCallback
    ) -> tuple[str, list[Asset]]:
        """
        Fetch web to get the most recent static data

        Follow a 2 stage commit:
        - Check asset candidates for updates, and fetch web data
            - optional, ask user confirmation (provided as callback)
        - Apply confirmed updates to FinancialIdentifiers
        - Update registry with confirmed updates

        Arguments:
        force_all: do not check previous missing data, force all assets
        """

        # to maintain stateless, fin_id loaded here
        fin_id = self.load_financial_identifier_from_registry(selector)

        pending_static_update = self._get_pending_static_update(fin_id, force_all)

        # call UI confirmation, already configured with always_yes
        pending_update = ui_confirm_cb(pending_static_update)

        # continue on registry update
        if len(pending_update) == 0:
            return "", []

        logger.info(f"assets to be updated in registry: {' '.join([p.name for p in pending_update])}")

        # to make update of fin_id HERE !
        # apply update to model - in memory storage
        for pending in pending_update:
            fin_id.update_entry(pending.name, pending.merged)

        # apply update to the registry
        updated_resource, backup_resource = self._update_registry(pending_update)
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
            if not isinstance(entry := fin_id.find(name), IdentifierError)
        ]

        return str(updated_resource), assets

    def _get_pending_static_update(
        self, fin_id: FinancialIdentifiers, force_all: bool
    ) -> list[PendingIdentifierEntryUpdate]:
        """
        Determine candidates for update (missing in original content)
        and fetch data from Yahoo Finance

        force_all: to force all assets to be candidates for update
        """
        # filter potential candidates for update of static data
        candidates = fin_id.candidates_for_update(force_all)

        if self._yfinance is None:
            raise RuntimeError("YFinancePort adapter is not initialized")

        # fetch data and compute diff with previous data in memory
        incoming_static_update = self._yfinance.fetch_static_identifiers(candidates)
        pending_static_update = fin_id.evaluate_pending_update(incoming_static_update)

        return pending_static_update

    def _update_registry(self, confirmed_pendings: list[PendingIdentifierEntryUpdate]) -> tuple[str | None, str | None]:
        """
        Update registry with confirmed pending update

        Return:
        updated_ressource: registry descriptor updated
        backup_ressource: if available with the implementation
        """
        # defensive
        if len(confirmed_pendings) == 0:
            return "", ""

        # apply update to the registry
        updated_resource, backup_resource = self._identifier_registry.update_registry(confirmed_pendings)

        return updated_resource, backup_resource
