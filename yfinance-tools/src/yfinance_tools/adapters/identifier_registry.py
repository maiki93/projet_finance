"""
Implementation of FinancialIdentifier for retrieval and storage in file (Outbound Port)
"""

import json
import logging
import pathlib
from typing import Any

from pydantic import ValidationError

from yfinance_tools.adapters import IdentifierEntryDto
from yfinance_tools.domain import ISIN, FinancialIdentifierEntry, FinancialIdentifiers
from yfinance_tools.domain.exceptions import IdentifierRegistryError, IdentifierRegistryFileNotExistingError
from yfinance_tools.services import IdentifierRegistryPort

logger = logging.getLogger(__name__)


class InFileIdentifierRegistry(IdentifierRegistryPort):
    """
    Storage of financial identifiers in JSON file.
    """

    def __init__(self, file_path: str):
        self._file_path = file_path

    def load(self) -> FinancialIdentifiers:
        """
        Initialize FinancailIdentifiers from JSON file.

        Validation of data using IdentifierEntryDto
        """

        logger.info("Load static data from JSON " + self._file_path)

        data_json = self._load_from_file()
        entries_dto = self._validate_data(data_json)
        return self._to_domain(entries_dto)

    def _load_from_file(self) -> dict:

        if not pathlib.Path(self._file_path).exists():
            raise IdentifierRegistryFileNotExistingError("file not existing: " + self._file_path)

        with open(self._file_path, "r") as f:
            try:
                # explicit for mypy type checking
                data_json: dict[str, Any] = json.load(f)
            except json.decoder.JSONDecodeError:
                raise IdentifierRegistryError("invalid JSON format: " + self._file_path)

        return data_json

    def _validate_data(self, data_json: dict) -> list[IdentifierEntryDto]:
        """Validation of every entry from input data"""

        entries_dto = []
        for name, item in data_json.items():
            try:
                entry_dto = IdentifierEntryDto.model_validate({"name": name, **item})
                entries_dto.append(entry_dto)

            except ValidationError as e:
                logger.warning(f"name = {name}, item = {item}")
                logger.warning(f"validation failed for registry data: {str(e)}")
                raise IdentifierRegistryError(f"validation failed for registry data: {str(e)}")

            except Exception as exc:
                logger.error(f"unexpected error occurred: {str(exc)}")
                raise RuntimeError(f"unexpected error occurred: {str(exc)}") from exc

        return entries_dto

    def _to_domain(self, entries_dto: list[IdentifierEntryDto]) -> FinancialIdentifiers:
        """
        Initialize a FinancialIdentiers domain model from validated entries
        """

        fin_id: FinancialIdentifiers = FinancialIdentifiers()

        for entry_dto in entries_dto:
            entry = FinancialIdentifierEntry(
                name=entry_dto.name,
                type=entry_dto.asset_type,
                yfTicker=entry_dto.yfTicker,
                isin=ISIN(entry_dto.isin) if entry_dto.isin else None,
            )
            fin_id.add_entry(entry)

        return fin_id
