"""
Test FinancialIdentifier
"""

from yfinance_tools.domain import FinancialIdentifier


def test_get_names(template_registry_data):
    fin_id = FinancialIdentifier(template_registry_data)

    all_asset_name = fin_id.get_entries()

    assert len(all_asset_name) == len(template_registry_data)
    assert "eurusd" in all_asset_name


def test_find_by_name(template_registry_data):
    fin_id = FinancialIdentifier(template_registry_data)

    data_eurusd = fin_id.find("eurusd")
    assert data_eurusd["yfTicker"] == "EURUSD=X"
