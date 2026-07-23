"""
Validation of static data fecthed with yahoo finance is done with YFinanceIdentifierDto
"""

import pytest

from yfinance_tools.adapters.yfinance_identifier_dto import YFinanceIdentifierDto
from yfinance_tools.domain import ISIN, AssetType


def test_read_all_attributes() -> None:

    data = {"asset_type": "EQUITY", "currency": "USD", "isin": "US0378331005"}
    yf_dto = YFinanceIdentifierDto.model_validate(data)

    assert yf_dto.asset_type == AssetType.EQUITY
    assert yf_dto.currency == "USD"
    assert yf_dto.isin == ISIN("US0378331005")
    assert yf_dto.isin == "US0378331005"


# certainly too strong
def test_forbid_extra_attributes() -> None:

    data = {"name": "apple", "yfTicker": "AAPL", "asset_type": "EQUITY", "currency": "USD", "isin": "US0378331005"}

    with pytest.raises(ValueError):
        YFinanceIdentifierDto.model_validate(data)


def test_empty_entries_are_defaulted() -> None:

    yf_dto = YFinanceIdentifierDto.model_validate({})

    assert yf_dto.asset_type == AssetType.UNDEFINED
    assert yf_dto.currency is None
    assert yf_dto.isin is None


def test_asset_type_equivalence() -> None:
    data_eurusd = {"asset_type": "CURRENCY"}
    yf_dto = YFinanceIdentifierDto.model_validate(data_eurusd)
    assert yf_dto.asset_type == AssetType.FOREX

    data_bitcoin = {"asset_type": "CRYPTOCURRENCY"}
    yf_dto = YFinanceIdentifierDto.model_validate(data_bitcoin)
    assert yf_dto.asset_type == AssetType.DIGITAL_ASSET

    data_fund = {"asset_type": "MUTUALFUND"}
    yf_dto = YFinanceIdentifierDto.model_validate(data_fund)
    assert yf_dto.asset_type == AssetType.MUTUAL_FUND


def test_unavailable_isin() -> None:
    isin_unavailable = {"isin": "-"}
    yf_dto = YFinanceIdentifierDto.model_validate(isin_unavailable)
    assert yf_dto.isin is None
