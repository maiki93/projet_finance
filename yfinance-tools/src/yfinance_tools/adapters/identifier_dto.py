"""
Use DTO object to validate static data from external registries

Used only by adapter layer's module
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from yfinance_tools.domain import AssetType


class IdentifierEntryDto(BaseModel):
    """
    Validated data for one identifier entry
    - allow coersion only for asset_type (to match enum AssetType)
    - ISIN always 12 characters
    - capitalize asset_type and ISIN before validation
    - forbid extra parameter (too strict ?)
    """

    # 'forbid'/'allow' ensures if there is no extra key in input
    # strict avoids coersion, default False
    model_config = ConfigDict(extra="forbid", strict=True)

    # name and and asset_type required
    name: str = Field(..., max_length=50)
    asset_type: AssetType = Field(..., strict=False)
    # ticker and isin optional
    yfTicker: str | None = None
    # ISIN validation done also in domain layer, length in case of DB
    isin: str | None = Field(default=None, max_length=12, min_length=12)

    @field_validator("asset_type", "isin", mode="before")
    def capitalize(cls: IdentifierEntryDto, value: Any) -> str | None:
        """Asset type (string) and ISIN are made case incensitive by capitalization"""
        if value and isinstance(value, str):
            return value.upper()
        return None
