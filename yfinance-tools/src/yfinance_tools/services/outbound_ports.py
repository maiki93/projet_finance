"""
Define interfaces to external dependencies (ports in hexagonal architecture)
"""

from typing import Protocol


class IdentifierRegistryPort(Protocol):
    """
    Provider of static data assets (identified by assets (name, ISIN, tickers))
    """

    def load(self) -> dict:
        """
        Load full content of the registry
        """
        ...


class YFinancePort(Protocol):
    """
    Access to yfinance external library
    """

    ...
