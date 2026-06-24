"""
Fake Identifier Registry
"""

from yfinance_tools.services import IdentifierRegistryPort


class FakeIdentifierRegistry(IdentifierRegistryPort):
    """
    Fake implementation, return the dictionary provided in constructor
    """

    def __init__(self, static_identifiers: dict):
        self._static_identifiers = static_identifiers

    def load(self) -> dict:
        return self._static_identifiers

    # def get_identifiers(self, names: list[str] | None = None) -> dict:
    #    return self._static_identifiers
