"""
Define interfaces to external dependencies (ports in hexagonal architecture)
"""

from typing import Protocol

from yfinance_tools.domain import FinancialIdentifierEntry, FinancialIdentifiers
from yfinance_tools.domain.filter_asset import FilterAsset
from yfinance_tools.domain.financial_identifier_entry import PendingIdentifierEntryUpdate


class IdentifierRegistryPort(Protocol):
    """
    Provider of static data assets (identified by assets (name, ISIN, tickers))
    """

    def load(self, selector: FilterAsset) -> FinancialIdentifiers:
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

    # name is not good
    def fetch_static_identifiers(self, ids: dict[str, FinancialIdentifierEntry]) -> dict[str, FinancialIdentifierEntry]:
        """
        ISIN, currency,...
        """
        ...
