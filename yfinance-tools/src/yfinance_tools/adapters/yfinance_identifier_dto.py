"""
DTO class to validate static data fetched by yahoo finance

Validation:
- for enumeration equivalence => asset_type : "CURRENCY" to "FOREX"
- unavailable ISIN is markerd as '-' fro mthe API
- then normal validation of AssetType and ISIN are applied
"""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, field_validator

from yfinance_tools.domain import AssetType

from .basic_types_dto import AssetTypeDto, IsinDto


class YFinanceIdentifierDto(BaseModel):
    # forbid, certainly too strong
    model_config = ConfigDict(extra="forbid", strict=True)

    # optional AssetType could be None here
    asset_type: AssetTypeDto = AssetType.UNDEFINED
    currency: str | None = None
    isin: IsinDto | None = None

    # keys are values returned by fast_info.quoteTpye
    equivalence: ClassVar[dict[str, str]] = {
        "CURRENCY": "FOREX",
        "CRYPTOCURRENCY": "DIGITAL_ASSET",
        "MUTUALFUND": "MUTUAL_FUND",
    }

    @field_validator("asset_type", mode="before")
    def _upper_and_equivalence(cls: YFinanceIdentifierDto, input: AssetType | str | None) -> AssetType | str | None:
        """
        Match for asset type, apply correspondances betwen yahoo and domain

        AssetType(EnumStr): pydantic knows how to make the conversion from string
        """

        if input and isinstance(input, str):
            normalized = input.upper()
            return cls.equivalence.get(normalized, normalized)

        return input

    @field_validator("isin", mode="before")
    def parse_isin_yf(cls, input: str | None) -> str | None:

        if input is None:
            return None

        if input == "-":
            return None

        return input
