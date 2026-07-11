"""
Implementation of FinancialIdentifier for retrieval and storage in file (Outbound Port)
"""

import json
import logging
import pathlib
from typing import Any

from pydantic import ValidationError

from yfinance_tools.domain import FinancialIdentifierEntry, FinancialIdentifiers, PendingIdentifierEntryUpdate
from yfinance_tools.domain.exceptions import IdentifierRegistryError, IdentifierRegistryFileNotExistingError
from yfinance_tools.services import IdentifierRegistryPort

from .file_identifier_dto import IdentifierEntryDto

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

        data_json: dict[str, Any] = self._load_from_file()
        entries_dto = self._validate_entries(data_json)
        return self._to_domain(entries_dto)

    def update_registry(self, pending_update: list[PendingIdentifierEntryUpdate]) -> tuple[str | None, str | None]:
        """
        Combine pending updates with previous data.

        Backup the previous registry file with an incremented suffix and rewrite the
        current registry file with merged content.

        return: string of updated ressource and backup ressource (file path for File)
        """
        file_path = pathlib.Path(self._file_path)

        data_json = self._load_from_file()

        for pending_entry in pending_update:
            data_json[pending_entry.name] = self._entry_to_dict(pending_entry.merged)

        backup_path = self._backup_file(file_path)
        file_path.rename(backup_path)

        with open(file_path, "w") as f:
            json.dump(data_json, f, indent=2)

        logger.info(f"file updated: {file_path}")
        logger.info(f"created backup file: {backup_path}")
        return str(file_path), str(backup_path)

    def _load_from_file(self) -> dict[str, Any]:

        if not pathlib.Path(self._file_path).exists():
            raise IdentifierRegistryFileNotExistingError("file not existing: " + self._file_path)

        with open(self._file_path, "r") as f:
            try:
                data_json: dict[str, Any] = json.load(f)
            except json.decoder.JSONDecodeError:
                raise IdentifierRegistryError("Invalid JSON format: " + self._file_path)

        return data_json

    def _validate_entries(self, data_json: dict) -> list[IdentifierEntryDto]:
        """Validation of every entry from input data"""

        entries_dto = []
        for name, item in data_json.items():
            try:
                entry_dto = IdentifierEntryDto.model_validate({"name": name, **item})
                entries_dto.append(entry_dto)

            except ValidationError as e:
                logger.warning(f"discard entry: name = {name}, item = {item}")
                logger.warning(f"validation failed for registry data: {e}")

            except Exception as exc:
                logger.error(f"unexpected error occurred: {str(exc)}")
                raise RuntimeError(f"unexpected error occurred: {str(exc)}") from exc

        return entries_dto

    def _backup_file(self, file_path: pathlib.Path) -> pathlib.Path:
        """Return a backup file path using an incremented suffix."""
        directory = file_path.parent
        stem = file_path.stem  # limited to 2-9 ?
        suffix = file_path.suffix

        candidate_index = 2
        while True:
            candidate = directory / f"{stem}{candidate_index}{suffix}"
            if not candidate.exists():
                return candidate
            candidate_index += 1

    # here or Dto ?
    def _entry_to_dict(self, entry: FinancialIdentifierEntry) -> dict[str, str | None]:
        """Serialize a FinancialIdentifierEntry for registry storage."""
        return {
            "yfTicker": entry.yf_ticker,
            "asset_type": entry.asset_type.value,
            "currency": entry.currency,
            "isin": str(entry.isin) if entry.isin is not None else None,
        }

    def _to_domain(self, entries_dto: list[IdentifierEntryDto]) -> FinancialIdentifiers:
        """
        Initialize a FinancialIdentiers domain model from validated entries
        """

        fin_id: FinancialIdentifiers = FinancialIdentifiers()

        for entry_dto in entries_dto:
            # all entries have been validated in DTO, cannot raise error
            entry = FinancialIdentifierEntry(
                entry_dto.yfTicker, asset_type=entry_dto.asset_type, currency=entry_dto.currency, isin=entry_dto.isin
            )
            fin_id.add_entry(entry_dto.name, entry)

        return fin_id
