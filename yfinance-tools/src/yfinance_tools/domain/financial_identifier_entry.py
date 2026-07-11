"""
Asset identifiers are static data, they never(rarely) change:
- yahoo ticker is required for web  with yfinance (partly true, ISIN may work also)
- AssetType : different capabilities from the asset
- currency : currency (or points for index, % for rates ...), maybe too specific
- isin : for some asset_type, not all
To extend with ?!
- market / timezone for is_open asset

Update is done in a 2 - Stage Commit, with PendingIdentifierEntryUpdate

They are retrieved / stored from an external registry (file, DB, ...)
Stored in one unique file/DB
"""

from dataclasses import dataclass, fields, replace
from typing import Any

# from pydantic import fields
from .financial_models import ISIN, AssetType


@dataclass(frozen=True)
class FinancialIdentifierEntry:
    """
    Static data associated to an asset:
    - yahoo ticker (required)
    - asset_type : AssetType( UNDEFINED by default)
    - isin: ISIN | None (optional, not all assets have an ISIN)
    """

    yf_ticker: str
    asset_type: AssetType = AssetType.UNDEFINED
    currency: str | None = None
    isin: ISIN | None = None

    def has_missing_values(self) -> bool:
        """ """
        if len(self.get_valid_fields()) != 4:
            return True
        return False

    def merge_with(self, incoming: FinancialIdentifierEntry) -> FinancialIdentifierEntry:
        """
        Merges incoming data with existing. Returns a new instance.

        Invalid data from incoming (None, AssetType.UNDEFINED) are discarded
        TODO: replacement of valid data should be logged / informed to user
        """
        updates = incoming.get_valid_fields()
        return replace(self, **updates)

    def get_valid_fields(self) -> dict[str, Any]:
        """
        Dynamically extracts all attributes that have non-default/valid values.

        None and AssetType.UNDEFINED are considered invalid
        """

        valid_data = {}
        for field in fields(self):
            val = getattr(self, field.name)

            # check if "empty" or default
            is_none = val is None
            is_undefined_enum = val == AssetType.UNDEFINED
            # is_empty_str = isinstance(val,str) and not val

            if not (is_none or is_undefined_enum):
                valid_data[field.name] = val

        return valid_data


@dataclass(frozen=True)
class PendingIdentifierEntryUpdate:
    """
    Value object for the update of FinancialIdentifierEntry

    Produced at step 1 of the 2 stage commit:
    - incoming: data proposed as an update
    - merged: full entry which will be saved to registry
    - original: if available, actual entry in registry
    """

    name: str
    incoming: FinancialIdentifierEntry
    merged: FinancialIdentifierEntry
    # optional: None if it is a new asset
    original: FinancialIdentifierEntry | None = None

    def is_new(self) -> bool:
        return self.original is None
