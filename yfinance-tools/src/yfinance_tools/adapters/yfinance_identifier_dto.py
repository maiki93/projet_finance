"""
DTO class to validate static data from fetching from yahoo finance

Validation:
- for enumeration equivalence => asset_type : "CURRENCY" to "FOREX"
- unavailable ISIN is markerd as '-' fro mthe API
- then normal validation of AssetType and ISIN are applied
"""

import logging
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from yfinance_tools.domain import ISIN, AssetType

logger = logging.getLogger("__name__")


class YFinanceIdentifierDto(BaseModel):
    # forbid, certainly too strong
    model_config = ConfigDict(extra="forbid", strict=True)

    # optional
    asset_type: AssetType = Field(default=AssetType.UNDEFINED, strict=False)
    currency: str | None = Field(default=None)
    isin: ISIN | None = Field(default=None)

    # key are values returned by fast_info.quoteTpye
    equivalence: ClassVar[dict[str, str]] = {
        "CURRENCY": "FOREX",
        "CRYPTOCURRENCY": "DIGITAL_ASSET",
        "MUTUALFUND": "MUTUAL_FUND",
    }

    @classmethod
    def from_fast_info(cls, asset_type: str | None, currency: str | None, isin: str | None) -> YFinanceIdentifierDto:
        # possible ?
        # ffinfo = getattr(ticker, "fast_info", None)
        # return cls.model_validate({
        #     "asset_type": getattr(ffinfo, "quote_type", None),
        #     "currency": getattr(ffinfo, "currency", None),
        #     "isin": getattr(ticker, "isin", None)
        # })
        return cls.model_validate({"asset_type": asset_type, "currency": currency, "isin": isin})

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
    def parse_isin(cls, input: ISIN | str | None) -> ISIN | None:
        """
        User defined type ISIN, we must make the conversion explicitly
        """
        if input is None:
            return None

        if isinstance(input, ISIN):
            return input

        # specific to yahoo api to mark not available isin
        # avoid polluting too much the logs
        if input == "-":
            return None

        try:
            isin = ISIN(input)
        except ValueError as ex:
            err_msg = f"Error in fetching data with ISIN validation string:'{input}' ValueError: {str(ex)}"
            print("DTO: err_msg")
            logger.warning(err_msg)
            isin = None

        return isin
