"""
Financial Asset

Aggregate all relevant information about a financial asset:
- static_identifers: static data stored in an external registry
- last values: updated by yfinance
"""

import json
from dataclasses import replace

from .financial_identifier_entry import FinancialIdentifierEntry
from .financial_models import ISIN, AssetType


class Asset:
    """Represent a financial asset.

    Attributes:
        name: The asset name, the asset unique identifier. length <= 50
        static_identifier: static data (yf_ticker, asset_type, ISIN)
    """

    def __init__(self, name: str, static_identifiers: FinancialIdentifierEntry):
        """
        Initialize a financial asset.

        A copy of static_identifiers is stored
        """

        if not name or len(name) > 50:
            raise ValueError(f"Invalid name format for'{name}' (max length 50)")

        self._name = name
        self._static_identifiers = replace(static_identifiers)

    @classmethod
    def from_entry(cls, name: str, entry: FinancialIdentifierEntry) -> Asset:
        """
        Create an Asset instance from a FinancialIdentifierEntry.

        A copy of the original entry is stored

        Args:
            entry: A FinancialIdentifierEntry object.
        """
        return cls(name=name, static_identifiers=entry)

    @property
    def name(self) -> str:
        return self._name

    @property
    def yf_ticker(self) -> str:
        return self._static_identifiers.yf_ticker

    @property
    def type(self) -> AssetType:
        return self._static_identifiers.asset_type

    @property
    def currency(self) -> str | None:
        return self._static_identifiers.currency

    @property
    def isin(self) -> ISIN | None:
        return self._static_identifiers.isin

    def to_json(self) -> str:
        """All fields are serialized, possibly with null value"""
        return json.dumps(
            {
                "name": self.name,
                "yf_ticker": self.yf_ticker,
                "type": self.type.name,
                "currency": self.currency,
                "isin": str(self.isin) if self.isin else None,
            }
        )
