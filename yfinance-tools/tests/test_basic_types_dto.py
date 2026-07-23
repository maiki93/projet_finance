"""
Test of basic DTO types
"""

import pytest
from pydantic import TypeAdapter, ValidationError

from yfinance_tools.adapters.basic_types_dto import AssetNameDto, AssetTypeDto, IsinDto
from yfinance_tools.domain import ISIN, AssetType


@pytest.mark.parametrize("invalid_isin", ["not-an-isin", "120123456789", "USXXX"])
def test_invalid_isin(invalid_isin: str):

    ta = TypeAdapter(IsinDto)

    data = invalid_isin

    with pytest.raises(ValidationError, match="Invalid ISIN"):
        ta.validate_python(data)


def test_isin_case_insensitive() -> None:
    ta = TypeAdapter(IsinDto)

    dto = ta.validate_python("fr0123456789")

    assert dto == ISIN("FR0123456789")
    # ISIN equals method
    assert dto == "FR0123456789"


def test_asset_type_case_insensitive() -> None:

    data = "equity"
    ta = TypeAdapter(AssetTypeDto)
    type_dto = ta.validate_python(data)

    assert isinstance(type_dto, AssetType)
    assert type_dto == AssetType.EQUITY

    # wrong entry
    with pytest.raises(ValidationError, match="Invalid AssetType"):
        ta.validate_python("WRONG")

    # empty entry
    type_dto = ta.validate_python(None)

    assert isinstance(type_dto, AssetType)
    assert type_dto == AssetType.UNDEFINED


def test_asset_name_validation() -> None:
    data = "gold"
    ta = TypeAdapter(AssetNameDto)

    name_dto = ta.validate_python(data)

    assert name_dto == "gold"
    # too short
    with pytest.raises(ValidationError, match="at least 3 characters"):
        ta.validate_python("az")
    # valid string
    with pytest.raises(ValidationError, match="Input should be a valid string"):
        ta.validate_python(None)
    # too long
    with pytest.raises(ValidationError, match="string_too_long"):
        ta.validate_python("a" * 52)
