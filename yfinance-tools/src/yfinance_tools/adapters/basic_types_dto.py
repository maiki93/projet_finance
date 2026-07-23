"""
Custom types for validation

Use of 'basic' DTO types allows to compose functionnal TypeAdapter or BaseModel validators

Validation:
- on length for DB storage constraints (AssetName)
- domain model types (ISIN, AssetType) are validated

Used only by adapter layer's modules
"""

import logging
from typing import Annotated

from pydantic import BeforeValidator, Field, PlainSerializer

from yfinance_tools.domain import ISIN, AssetType

logger = logging.getLogger(__name__)

#
# Asset Name
#

"""The asset name has length and valid characters requirements"""
AssetNameDto = Annotated[
    str,
    Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-z0-9_\-]+$",
    ),
]

#
# Asset Type
#


def parse_asset_type(input: AssetType | str | None) -> AssetType:
    """
    Create an AssetType from the input or raise ValueError, catchable as ValidationError with pydantic
    Input is case insensisitive
    """
    if isinstance(input, AssetType):
        return input

    if isinstance(input, str):
        cleaned = input.strip().upper()

        try:
            return AssetType[cleaned]
        except KeyError:
            # pydantic will wraps ValueError into a ValidationError
            err_msg = f"Invalid AssetType key: '{cleaned}'. Allowed values: {[e.name for e in AssetType]}"
            raise ValueError(err_msg)

    return AssetType.UNDEFINED


"""
Absence of the input creates an AssetType.UNDEFINED value
Raise a ValidationError if an invalid string input is provided - not in AssetType Enum
"""
AssetTypeDto = Annotated[AssetType, BeforeValidator(parse_asset_type)]

#
# ISIN
#


def parse_isin(input: ISIN | str | None) -> ISIN | None:
    """
    User defined type ISIN, make the conversion explicitly.
    ISIN constructor throws a ValueError if the input is not valid
    """
    if input is None:
        return None

    if isinstance(input, ISIN):
        return input

    if isinstance(input, str):
        # raise ValueError, wrapped to ValidationError
        isin = ISIN(input.upper())

    return isin


"""
If present must respect ISIN format (ISO 6166) or will raise a ValidationError
"""
IsinDto = Annotated[
    ISIN | None,
    BeforeValidator(parse_isin),
    PlainSerializer(str, return_type=str, when_used="unless-none"),
]


# """More specific IsinDto, ValidationError is throw if the format is invalid"""
# StrictIsinDto = Annotated[IsinDto, AfterValidator(reject_invalid_isin)]
# StrictIsinDto = Annotated[
#     ISIN | None,  # <--- IDEs / Pylance / Mypy now see ONLY `ISIN | None`!
#     BeforeValidator(parse_isin),
#     AfterValidator(reject_invalid_isin),
#     PlainSerializer(str, return_type=str, when_used="unless-none"),
# ]
