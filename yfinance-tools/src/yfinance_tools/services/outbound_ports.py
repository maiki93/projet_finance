"""
Define interfaces to external dependencies (ports in hexagonal architecture)
"""

from typing import Callable, Protocol, Sequence

from yfinance_tools.domain import (
    FinancialIdentifierEntry,
    FinancialIdentifiers,
    PendingIdentifierEntryUpdate,
    SelectorAsset,
)

# alias for callback <=> implementation (adapter) in yf_cli.py
ConfirmationCallback = Callable[[Sequence[PendingIdentifierEntryUpdate]], list[PendingIdentifierEntryUpdate]]


class IdentifierRegistryPort(Protocol):
    """
    Provider of static data assets (identified by assets (name, ISIN, tickers))
    """

    def load(self, selector: SelectorAsset) -> FinancialIdentifiers:
        """
        Create a FinancialIdentifiers instance with the full content of the registry
        """
        ...

    def update_registry(self, pendings: list[PendingIdentifierEntryUpdate]) -> tuple[str | None, str | None]:
        """
        Update the registry with merged attribute of the provided entries

        Return a tuple of (updated, backup) ressource (file_path, URI,..)
        """
        ...


class YFinancePort(Protocol):
    """
    Access to yfinance external library
    """

    def fetch_static_identifiers(self, ids: dict[str, FinancialIdentifierEntry]) -> dict[str, FinancialIdentifierEntry]:
        """
        ISIN, currency,...
        """
        ...
