"""
Fake Identifier Registry

For testing the service layer
- implements a in-memory version of the IdentifierRegistryPort
- can simulate Exception in load() method
- no additional validation of input data with Dto
"""

import logging
from typing import Any

# no use of RegistryFileDto ?? more close of the real implementation, to see with extension DB
from yfinance_tools.adapters.file_identifier_dto import RegistryFileEntryDto
from yfinance_tools.domain import (
    AssetType,
    FinancialIdentifierEntry,
    FinancialIdentifiers,
    PendingIdentifierEntryUpdate,
)
from yfinance_tools.services import IdentifierRegistryPort

logger = logging.getLogger(__name__)


class FakeIdentifierRegistry(IdentifierRegistryPort):
    """
    Fake implementation, in-memory, dictionary provided in the constructor

    For testing assertion access to content by keys (eg: reg._satic_identifiers["apple"]["assetType"])
    access to the the fileds by Dto keys (assetType)

    Optional: set an exception raised by load() for testing errors
    """

    def __init__(self, static_identifiers: dict[str, dict[str, Any]]):
        self._static_identifiers = static_identifiers
        self._exception: Exception | None = None

    @property
    def fake_static_identifiers(self) -> dict[str, dict[str, Any]]:
        return self._static_identifiers

    def load(self) -> FinancialIdentifiers:

        if self._exception:
            raise self._exception

        fin_id = FinancialIdentifiers()

        for name, items in self._static_identifiers.items():
            entry = FinancialIdentifierEntry(
                items.get("yfTicker", "-"),  # not possible
                asset_type=items.get("assetType", AssetType.UNDEFINED),
                currency=items.get("currency", None),
                isin=items.get("isin", None),
            )
            fin_id.add_entry(name, entry)

        return fin_id

    def update_registry(self, pendings: list[PendingIdentifierEntryUpdate]) -> tuple[str | None, str | None]:
        """
        Only replace in memory dictionary entries for this fake implementation
        Return static strings
        """
        for pending_entry in pendings:
            dict_values = self._entry_to_dict(pending_entry.merged)
            self._static_identifiers[pending_entry.name] = dict_values

        return "/tmp_dir/in_memory_static_assets.json", "/tmp_dir/in_memory_static_assets2.json)"

    def _entry_to_dict(self, entry: FinancialIdentifierEntry) -> dict[str, str | None]:
        """Serialize for Registry file storage"""

        dto = RegistryFileEntryDto(
            yfTicker=entry.yf_ticker, assetType=entry.asset_type, currency=entry.currency, isin=entry.isin
        )
        # real implemantation json
        return dto.model_dump(exclude_none=True)

    def set_exception(self, error: Exception) -> None:
        """To simulate an error in load() method"""
        self._exception = error
