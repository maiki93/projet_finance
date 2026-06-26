"""
Define interfaces to external dependencies (ports in hexagonal architecture)
"""

from typing import Protocol

from yfinance_tools.domain import FinancialIdentifiers


class IdentifierRegistryPort(Protocol):
    """
    Provider of static data assets (identified by assets (name, ISIN, tickers))
    """

    def load(self) -> FinancialIdentifiers:
        """
        Create a FinancialIdentifiers instance with the full content of the registry
        """
        ...


class YFinancePort(Protocol):
    """
    Access to yfinance external library
    """

    ...
