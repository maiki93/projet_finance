"""
Financial Asset

Store all relevant information about a financial asset:
- static data: stored in an external registry
- last values:
"""

import json

from .financial_identifier import FinancialIdentifierEntry
from .financial_models import ISIN, AssetType


class Asset:
    """Represent a financial asset.

    Attributes:
        name: The asset name.
        type: The asset type.
        isin: The ISIN identifier, if available.
        yf_ticker: The Yahoo Finance ticker, if available.
    """

    def __init__(
        self,
        asset_name: str,
        asset_type: AssetType,
        isin: ISIN | None = None,
        yf_ticker: str | None = None,
    ):
        """
        Initialize a financial asset.

        Args:
            asset_name: Name of the asset.
            asset_type: Type of the asset.
            isin: ISIN of the asset, if provided.
            yf_ticker: Yahoo Finance ticker of the asset, if provided.
        """
        self._name = asset_name
        self._asset_type = asset_type
        self._yf_ticker = yf_ticker
        self._isin = isin

    @classmethod
    def asset_from_entry(cls, entry: "FinancialIdentifierEntry") -> "Asset":
        """
        Create an Asset instance from a FinancialIdentifierEntry.

        Args:
            entry: A FinancialIdentifierEntry object.
        """
        return cls(asset_name=entry.name, asset_type=entry.type, isin=entry.isin, yf_ticker=entry.yfTicker)

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> AssetType:
        return self._asset_type

    @property
    def isin(self) -> ISIN | None:
        return self._isin

    @property
    def yf_ticker(self) -> str | None:
        return self._yf_ticker

    def to_json(self) -> str:
        """All fields are serialized, maybe with null value"""
        return json.dumps(
            {
                "name": self.name,
                "type": self.type.name,
                "isin": str(self.isin) if self.isin else None,
                "yf_ticker": self.yf_ticker,
            }
        )
