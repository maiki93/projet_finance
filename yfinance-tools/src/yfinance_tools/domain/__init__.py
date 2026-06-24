"""
Core package, defines:
    Tickers
"""

from . import exceptions  # Import the module, not the classes
from .assets import Asset, AssetType
from .financial_identifier import FinancialIdentifier

# from .exceptions import IdentifierRegistryError, YFinanceToolsError

# act as a facade, define the exposed classes as public API
# usage: from yfinance_tools.core import AssetsData
# or : from yfinance_tools.domain.exceptions import IdentifierRegistryError

# use exceptions rather that publish all "important"  errors
__all__ = ["Asset", "AssetType", "FinancialIdentifier", "exceptions"]
