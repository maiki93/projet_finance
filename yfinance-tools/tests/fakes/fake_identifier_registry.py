"""
Fake Identifier Registry

For testing the service layer
- implements a in-memory version of the IdentifierRegistryPort
- can simulate Exception in load() method
- no additional validation of input data with Dto
"""

import logging

from yfinance_tools.adapters.file_identifier_dto import IdentifierEntryDto
from yfinance_tools.domain import (
    AssetType,
    FinancialIdentifierEntry,
    FinancialIdentifiers,
    PendingIdentifierEntryUpdate,
)
from yfinance_tools.services import IdentifierRegistryPort

logger = logging.getLogger("__name__")


class FakeIdentifierRegistry(IdentifierRegistryPort):
    """
    Fake implementation, in-memory, dictionary provided in the constructor

    Optional: set an exception raised by load() for testing errors
    """

    def __init__(self, static_identifiers: dict):
        self._static_identifiers = static_identifiers
        self._exception: Exception | None = None

    def load(self) -> FinancialIdentifiers:

        if self._exception:
            raise self._exception

        fin_id = FinancialIdentifiers()

        for name, items in self._static_identifiers.items():
            entry = FinancialIdentifierEntry(
                items.get("yfTicker"),
                asset_type=items.get("asset_type", AssetType.UNDEFINED),
                currency=items.get("currency", None),
                isin=items.get("isin", None),
            )
            fin_id.add_entry(name, entry)

        return fin_id

    def update_registry(self, pending_update: list[PendingIdentifierEntryUpdate]) -> tuple[str | None, str | None]:
        """Only replace in memory for the fake, return static strings"""

        for pending_entry in pending_update:
            dict_values = self._entry_to_dict(pending_entry.merged)
            self._static_identifiers[pending_entry.name] = dict_values

        return "/tmp_dir/in_memory_static_assets.json", "/tmp_dir/in_memory_static_assets2.json)"

    def _entry_to_dict(self, entry: FinancialIdentifierEntry) -> dict[str, str | None]:
        """Serialize for Registry file storage"""
        ## discard "name"
        dto = IdentifierEntryDto(
            name="toto", yfTicker=entry.yf_ticker, asset_type=entry.asset_type, currency=entry.currency, isin=entry.isin
        )
        # can exclude with dump
        # return dto.model_dump(exclude=name) # return a dictionnary
        return dto.to_registry_file()

    def set_exception(self, error: Exception) -> None:
        """To simulate an error in load() method"""
        self._exception = error
