"""
Asset identifier are static data necessary to perform functionalities:
- tickers for web fetching (provider dependent)
- market / timezone for is_open asset

They are retrieved / stroed from an external registry (file, DB, ...)
"""

from dataclasses import dataclass, field

from yfinance_tools.domain.exceptions import IdentifierError
from yfinance_tools.domain.financial_models import ISIN, AssetType


@dataclass(frozen=True)
class FinancialIdentifierEntry:
    """
    Static data identifier of the asset:
    - a symbole name (must be unique) #TODO to enforce
    - type: EQUITY, FOREX
    - ISIN (optional, ot all assets have an ISIN)
    - yahoo ticker (optional, but raise error if call yfinance)

    TODO to extend ?: seems indefinite if start to add too much "details"
    - market / timezone : usefull to know quickly if open/close ?
    - sector / industry : ? optional ? it is always true for EQUITY, but possible for Fund,ETF,...
    It is may be not the best place IN FINALE, but can be quickly implemented if needed
    """

    name: str
    type: AssetType
    yfTicker: str | None
    # Optional[ISIN] = None
    isin: ISIN | None

    def __post_init__(self) -> None:
        if not self.name or len(self.name) > 50:
            raise ValueError(f"A name must be provided for {self.name} (max length 50)")


# Alias possible for a container, may want more domain logic
# FinancialIdentifiers = dict[str, FinancialIdentifierEntry]


@dataclass
class FinancialIdentifiers:
    """
    Container of asset identifier entry.

    - allow filtering by name / isin, asset type,
    - open-close state with market
    - tickers to fetch live data from website (yahoo, boursorama, ...)
    """

    # with init=False: not present in constructor
    _entries: dict[str, FinancialIdentifierEntry] = field(
        init=False, default_factory=dict[str, FinancialIdentifierEntry]
    )

    def add_entry(self, entry: FinancialIdentifierEntry) -> None:
        # name is key + present in entry
        entry_name = entry.name
        self._entries[entry_name] = entry

    def get_entries(self) -> list[str]:
        return list(self._entries.keys())

    def find(self, name: str) -> FinancialIdentifierEntry | IdentifierError:
        if name not in self._entries:
            raise IdentifierError(f"Asset name not found: {name}")

        return self._entries[name]

    def __len__(self) -> int:
        return len(self._entries)
