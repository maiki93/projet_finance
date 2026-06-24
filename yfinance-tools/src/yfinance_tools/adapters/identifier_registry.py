"""
Implementation of FinancialIdentifier (outbound port)
"""

import json
import logging
import pathlib

from yfinance_tools.domain.exceptions import IdentifierRegistryError, IdentifierRegistryFileNotExistingError
from yfinance_tools.services.outbound_ports import IdentifierRegistryPort

logger = logging.getLogger(__name__)


class InFileIdentifierRegistry(IdentifierRegistryPort):
    """
    Storage of financial identifiers in JSON file.
    """

    # TODO pathlib.Path ?
    def __init__(self, file_path: str):
        self._file_path = file_path

    def load(self) -> dict:

        logger.info("Load static data from JSON " + self._file_path)

        if not pathlib.Path(self._file_path).exists():
            raise IdentifierRegistryFileNotExistingError("file not existing: " + self._file_path)

        with open(self._file_path, "r") as f:
            try:
                data = json.load(f)
            except json.decoder.JSONDecodeError:
                raise IdentifierRegistryError("Invalid JSON format")

        return data
