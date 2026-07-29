"""
Store user criteria for the selection of assets from the registry
"""

from dataclasses import dataclass, field

from .financial_identifier_entry import FinancialIdentifierEntry
from .financial_models import AssetType


@dataclass(frozen=True, kw_only=True, init=True)
class SelectorAsset:
    """
    Allow filtering of assets

    OR logic is used
    """

    name: str | None = None
    type: AssetType | None = None
    # market: Market | Open | Closed

    is_active: bool = field(default=True, init=False)

    def __post_init__(self):
        if self.name is None and self.type is None:
            # Bypass the frozen lock
            object.__setattr__(self, "is_active", False)

    def as_filter(self, name: str, entry: FinancialIdentifierEntry | None) -> bool:
        """Act as a filter, returning boolean value if match"""
        if entry is None:
            return False

        if not self.is_active:
            return True

        if (self.name and self.name == name) or (self.type and self.type == entry.asset_type):
            return True

        return False

    def __str__(self) -> str:
        "Pretty output"
        msg = f"FilterAsset {'active' if self.is_active else 'inactive'}"
        if self.is_active:
            msg += f": {self.name if self.name else ''} {self.type if self.type else ''}"
        return msg


class SelectorAssetBuilder:
    """Buider API to construct FilterAsset"""

    def __init__(self):
        self.name: str | None = None
        self.type: str | None = None

    def with_type(self, type: str | None) -> SelectorAssetBuilder:
        if type is not None:
            self.type = type.upper()
        return self

    def with_name(self, name: str | None) -> SelectorAssetBuilder:
        if name is not None:
            self.name = name
        return self

    def build(self) -> SelectorAsset:
        """
        Build and return the FilterAsset instance

        Raise ValueError if invalid AssetType
        """
        if self.type:
            asset_type = AssetType(self.type)
        else:
            asset_type = None

        return SelectorAsset(name=self.name, type=asset_type)
