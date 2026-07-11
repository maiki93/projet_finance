"""
DTO objects to validate static data from external registries

Validation:
- on length for DB storage constraints
- model types (ISIN, AssetType) are validated

Used only by adapter layer's modules
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from yfinance_tools.domain import ISIN, AssetType


class IdentifierEntryDto(BaseModel):
    """
    Validate data for one identifier entry
    - name (key) and yfTicker required
    - allow coersion for isin (create ISIN) and asset_type (to match AssetType enum)
    - capitalize asset_type and isin before validation
    - 'ignore' extra parameters (to allow extension of registry entries with other data)
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    name: str = Field(..., max_length=50, min_length=1)
    yfTicker: str = Field(..., max_length=20)
    # optional
    asset_type: AssetType = Field(default=AssetType.UNDEFINED, strict=False)
    currency: str | None = Field(default=None)
    isin: ISIN | None = Field(default=None)

    @field_validator("asset_type", mode="before")
    def capitalize(cls: IdentifierEntryDto, value: Any) -> str | None:
        """Asset type (string)"""
        if value and isinstance(value, str):
            return value.upper()
        return None

    @field_validator("isin", mode="before")
    def parse_isin(cls, v: str | ISIN) -> ISIN:
        if isinstance(v, str):
            return ISIN(v.upper())
        return v

    # must ensure it is string for file ouput
    # equivalent to dump_model_json() ?? option ??
    def to_registry_file(self) -> dict[str, str | None]:
        return {
            "yfTicker": self.yfTicker,
            "asset_type": self.asset_type.value,
            "currency": self.currency,
            "isin": str(self.isin),
        }
