"""
Asset and Asset Factory
"""

from enum import Enum


class AssetType(Enum):
    """
    The different types of Assets
    """

    UNDEFINED = 0
    EQUITY = 1  # Action
    INDEX = 2  # Indices
    FOREX = 3  # Devise
    DIGITAL_ASSET = 4  # all kinds crypto(BTC, ETH), NFT, Stablecoins...
    MUTUAL_FUND = 5  # OPCVM, content available by FundsData
    COMMODITY = 6  # Matières premières
    # Not sure all those distinctions are important for Yahoo Finance retrieval data
    FUTURE = 7  #
    DERIVATIVES = 8  # OPTION, WARRANT, CFD
    ETF = 9  # ETF on various assets
    RATES = 10  # Taux institutionnels (non accessible aux particuliers)
    BOND = 11  # (Obligation) PRIVATE_BOND and GOVERNMENT_BOND
    MONEY_MARKET = 12  # Taux à court termes


class Asset:
    """
    Financial asset
    """

    value: float | None
    last_update: float | None
    # could store the content

    def __init__(
        self,
        asset_name: str,
        asset_type: AssetType,
        isin: str | None = None,
        yf_ticker: str | None = None,
    ):
        self._name = asset_name
        self._asset_type = asset_type
        self._isin = isin
        self._yf_ticker = yf_ticker

    @property
    def name(self):
        return self._name

    @property
    def type(self) -> AssetType:
        return self._asset_type

    @property
    def isin(self) -> str | None:
        return self._isin

    @isin.setter
    def isin(self, isin: str):
        # check format
        self._isin = isin

    @property
    def yf_ticker(self) -> str | None:
        return self._yf_ticker

    # update_value


# factory
# def get_assets(names: list[str] | None = None) -> dict[str, Asset]:

#     if not names:
#         names = FinancialIdentifier().get_list_names()

#     assets: dict[str, Asset] = {}
#     for name in names:
#         ticker = FinancialIdentifier().by_name(name)
#         asset = Asset(
#             name, AssetType[ticker["type"]], ticker["yfIsin"], ticker["yfTicker"]
#         )
#         assets[name] = asset

#     return assets
