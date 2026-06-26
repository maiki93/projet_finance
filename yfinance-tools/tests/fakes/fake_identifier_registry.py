"""
Fake Identifier Registry

For testing the service layer
- implements a in-memory version of the IdentifierRegistryPort
- can simulate Exception in load() method
- no additional validation of input data with Dto
"""

from yfinance_tools.domain import ISIN, AssetType, FinancialIdentifierEntry, FinancialIdentifiers
from yfinance_tools.services import IdentifierRegistryPort


class FakeIdentifierRegistry(IdentifierRegistryPort):
    """
    Fake implementation, simply return the dictionary provided in the constructor.

    Optional: set an exception raised by load()
    """

    def __init__(self, static_identifiers: dict):
        self._static_identifiers = static_identifiers
        self._exception = None

    def load(self) -> FinancialIdentifiers:

        if self._exception:
            raise self._exception

        fin_id = FinancialIdentifiers()

        for name, items in self._static_identifiers.items():
            entry = FinancialIdentifierEntry(
                name,
                AssetType(items["asset_type"]) if items.get("asset_type") is not None else AssetType.UNDEFINED,
                items["yfTicker"] if items.get("yfTicker") is not None else None,
                ISIN(value=items["isin"]) if items.get("isin") else None,
            )
            fin_id.add_entry(entry)

        return fin_id

    def set_exception(self, error: Exception):
        """To simulate an error in load() method"""
        self._exception = error
