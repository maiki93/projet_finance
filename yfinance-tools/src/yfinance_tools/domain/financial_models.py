"""
Pure values objects for the core domain
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import override


class AssetType(StrEnum):
    """Different types of Assets"""

    UNDEFINED = "UNDEFINED"  # During creation the type may be undefined ?
    EQUITY = "EQUITY"  # Action # auto() => generates lower case string
    INDEX = "INDEX"  # Indices
    FOREX = "FOREX"  # Devise
    DIGITAL_ASSET = "DIGITAL_ASSET"  # all kinds crypto(BTC, ETH), NFT, Stablecoins...
    MUTUAL_FUND = "MUTUAL_FUND"  # OPCVM, content available by FundsData
    COMMODITY = "COMMODITY"  # Matières premières
    # Not sure all those distinctions are important for Yahoo Finance retrieval data
    FUTURE = "FUTURE"  #
    DERIVATIVES = "DERIVATIVES"  # OPTION, WARRANT, CFD
    ETF = "ETF"  # ETF on various assets
    RATES = "RATES"  # Taux institutionnels (non accessible aux particuliers)
    BOND = "BOND"  # (Obligation) PRIVATE_BOND and GOVERNMENT_BOND
    MONEY_MARKET = "MONEY_MARKET"  # Taux à court termes


@dataclass(frozen=True)
class ISIN:
    """
    ISIN (International Securities Identification Number)

    Its format is defined by ISO 6166 and consists of a 12-character alphanumeric code
    """

    value: str

    def __post_init__(self) -> None:
        if not self._is_valid_isin(self.value):
            raise ValueError(f"Invalid ISIN format: {self.value}")

    @staticmethod
    def _is_valid_isin(isin: str) -> bool:
        """Validation for ISIN format (2 capital letters + 9 alphanumeric characters + 1 check digit)"""
        return len(isin) == 12 and isin[:2].isupper() and isin[2:11].isalnum() and isin[11].isdigit()

    # keep __repr__ for debug  / logs
    def __str__(self) -> str:
        return self.value

    @override
    def __eq__(self, other: object | None) -> bool:
        """Allow comparison between FinancialIdentierEntries (object) and its serialization"""
        if other is None:
            return False
        if isinstance(other, ISIN):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other

        raise TypeError(f"{str(other)}")
