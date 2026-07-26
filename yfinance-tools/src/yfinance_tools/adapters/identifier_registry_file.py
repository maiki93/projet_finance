"""
Implementation of FinancialIdentifier for retrieval and storage in file (Outbound Port)
"""

import logging
import pathlib

from pydantic import TypeAdapter, ValidationError

from yfinance_tools.adapters.basic_types_dto import AssetNameDto
from yfinance_tools.domain import (
    FilterAsset,
    FinancialIdentifierEntry,
    FinancialIdentifiers,
    PendingIdentifierEntryUpdate,
)
from yfinance_tools.domain.exceptions import IdentifierRegistryError, IdentifierRegistryFileNotExistingError
from yfinance_tools.services import IdentifierRegistryPort

from .file_identifier_dto import RegistryFileDto, RegistryFileEntryDto

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Reusable Adapters (Compiled once at module import)
# ------------------------------------------------------------------
RAW_DICT_ADAPTER: TypeAdapter[dict[str, dict]] = TypeAdapter(dict[str, dict])
KEY_ADAPTER: TypeAdapter[AssetNameDto] = TypeAdapter(AssetNameDto)


class InFileIdentifierRegistry(IdentifierRegistryPort):
    """
    Storage of financial static identifiers in JSON file.
    """

    def __init__(self, file_path: pathlib.Path | str):
        if isinstance(file_path, str):
            self._file_path = pathlib.Path(file_path)
        else:
            self._file_path = file_path

    def load(self, selector: FilterAsset) -> FinancialIdentifiers:
        """
        Initialize FinancailIdentifiers from a JSON file.

        Validation of data using RegistryFileDto, invalid entries are skipped
        """
        logger.info(f"Load static data from JSON file: {str(self._file_path)}")

        entries_dto = self._load_from_file()
        return self._dto_to_domain(entries_dto, selector)

    def update_registry(self, pendings: list[PendingIdentifierEntryUpdate]) -> tuple[str | None, str | None]:
        """
        Combine pending updates with previous data.

        Backup the previous registry file with an incremented suffix and rewrite the
        current registry with merged content.

        return: string of updated ressource and backup ressource (file path for File)
        """
        # load all validated data
        data_dto = self._load_from_file()

        for pending_entry in pendings:
            assert pending_entry.name is not None
            data_dto[pending_entry.name] = self._entry_to_dto(pending_entry.merged)

        backup_path = self._backup_file(self._file_path)
        self._file_path.rename(backup_path)

        try:
            json_bytes = RegistryFileDto.dump_json(data_dto, indent=2, exclude_none=True)
            self._file_path.write_bytes(json_bytes)

        # a priori PydanticSerializationError
        except Exception as ex:
            logger.error(f"Dump_json or write_bytes with file_path {self._file_path} : {ex}")
            raise IdentifierRegistryError(f"Writing JSON to registry {self._file_path}: {ex}")

        logger.info(f"file updated: {self._file_path}")
        logger.info(f"created backup file: {backup_path}")
        return str(self._file_path), str(backup_path)

    def _load_from_file(self) -> dict[AssetNameDto, RegistryFileEntryDto]:
        """
        Parses JSON fast, skips invalid entries, and returns all valid ones
        """
        if not pathlib.Path(self._file_path).exists():
            raise IdentifierRegistryFileNotExistingError("file not existing: " + str(self._file_path))

        try:
            # validate JSON format, fast still avoiding json.load()
            raw_data = RAW_DICT_ADAPTER.validate_json(self._file_path.read_bytes())
        except ValidationError as ex:
            logger.error(f"Invalid JSON format: {ex}")
            raise IdentifierRegistryError("Invalid JSON format: " + str(self._file_path))

        valid_entries: dict[AssetNameDto, RegistryFileEntryDto] = {}

        # Validate item-by-item, only discard invalid entries
        for raw_key, raw_entry in raw_data.items():
            try:
                key = KEY_ADAPTER.validate_python(raw_key)
                entry = RegistryFileEntryDto.model_validate(raw_entry)
                valid_entries[key] = entry

            except ValidationError as err:
                # pretty logging, may save for later print to the user, use helper method
                first_error = err.errors()[0]
                error_msg = first_error.get("msg", "Unknown error")
                error_type = first_error.get("type", "unknown")
                error_loc = " -> ".join(str(loc) for loc in first_error.get("loc", ()))
                logger.warning(
                    f"Skip invalid entry '{raw_key}': '{raw_entry}'."
                    f"Error in '{error_loc}': {error_msg} (type: {error_type})"
                )

        return valid_entries

    def _dto_to_domain(
        self, entries_dto: dict[AssetNameDto, RegistryFileEntryDto], filter: FilterAsset
    ) -> FinancialIdentifiers:
        """
        Initialize a FinancialIdentiers domain model from validated entries
        and if they pass the filter selection
        """

        fin_id: FinancialIdentifiers = FinancialIdentifiers()

        for name, entry_dto in entries_dto.items():
            # all entries have been validated by DTO, cannot raise error
            entry = FinancialIdentifierEntry(
                entry_dto.yfTicker, asset_type=entry_dto.assetType, currency=entry_dto.currency, isin=entry_dto.isin
            )

            if filter(name, entry):
                fin_id[name] = entry

        return fin_id

    def _entry_to_dto(self, entry: FinancialIdentifierEntry) -> RegistryFileEntryDto:
        """Create Dto from domain models. Make dump easier, input are valid"""

        return RegistryFileEntryDto(
            yfTicker=entry.yf_ticker, assetType=entry.asset_type, currency=entry.currency, isin=entry.isin
        )

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
