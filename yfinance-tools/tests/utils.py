"""
Helper methods and template data for tests.

Keep separate from conftest.py, specifc for fixtures
"""

import json
from pathlib import Path

from yfinance_tools.domain import ISIN, AssetType, FinancialIdentifierEntry


def create_file_with_content(tmp_path: Path, filename: str, content: str | dict | None = None) -> Path:

    tmp_file = tmp_path / filename
    with open(tmp_file, "w") as f:
        if content and isinstance(content, str):
            f.write(content)

        elif content and isinstance(content, dict):
            json.dump(content, f)

    return tmp_file


def fid_entry_from_dict(data: dict[str, str]) -> FinancialIdentifierEntry:
    """
    Convenient helper to create instance FinancialIdentifierEntry for tests.

    Skip normal validation by DTO, so need to keep up to date.
    """
    # copy_data = dict() to not change the original
    # if dict[str, str|None] more steps to perform (maybe usefull anyway)

    assert "yfTicker" in data

    yf_ticker = data.get("yfTicker")
    if not yf_ticker:
        raise ValueError("Cannot create FinancialIdentifierEntry: 'yfTicker' is missing or empty")

    return FinancialIdentifierEntry(
        yf_ticker=yf_ticker,
        asset_type=AssetType[data.get("assetType", "UNDEFINED")],
        currency=data.get("currency", None),
        isin=ISIN(data["isin"].upper()) if data.get("isin") else None,
    )
