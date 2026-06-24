"""
Data container holding identifiers to assets:
- allow filtering by name / isin, asset type, open-close state with market
- tickers fetch live data from website (yahoo, boursorama, ...)

TODO to extend ?: seems indefinite if start to add too much "details"
- market / timezone : usefull to know quickly if open/close ?
- sector / industry : ? optional ? it is always true for EQUITY, but possible for Fund,ETF,...
It is may be not the best place IN FINALE, but can be quickly implemented if needed

Data can be stored in file or DB : responsability of IdentifierRegistry (port & adapters)
"""


class FinancialIdentifier:
    """
    Identifiers and tickers of financial assets.

    Static data identifier of the asset:
    - ISIN
    - yahoo ticker
    - type: EQUITY, FOREX
    - ? timzezone, market : open/close can be guessed ?
    """

    def __init__(self, identifiers: dict):
        self._static_identifier = identifiers

    def get_entries(self) -> list[str]:
        return list(self._static_identifier.keys())

    def find(self, name: str):
        return self._static_identifier[name]
