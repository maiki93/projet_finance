"""
Implementation of FinancialIdentifier for retrieval and storage in file (Outbound Port)
"""

import logging
import pathlib
from typing import Any

from pydantic import TypeAdapter, ValidationError

from yfinance_tools.adapters.basic_types_dto import AssetNameDto
from yfinance_tools.domain import (
    FinancialIdentifierEntry,
    FinancialIdentifiers,
    PendingIdentifierEntryUpdate,
    SelectorAsset,
)
from yfinance_tools.domain.exceptions import IdentifierRegistryError, IdentifierRegistryFileNotExistingError
from yfinance_tools.services import IdentifierRegistryPort

from .file_identifier_dto import RegistryFileDto, RegistryFileEntryDto
from .utils import NamedEntry, NamedEntryDto, is_not_none

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Reusable Adapters (Compiled once at module import)
# ------------------------------------------------------------------
RAW_DICT_ADAPTER = TypeAdapter(dict[str, dict[str, Any]])
KEY_ADAPTER = TypeAdapter(AssetNameDto)


class InFileIdentifierRegistry(IdentifierRegistryPort):
    """
    Storage of financial static identifiers in JSON file.
    """

    def __init__(self, file_path: pathlib.Path | str):
        if isinstance(file_path, str):
            self._file_path = pathlib.Path(file_path)
        else:
            self._file_path = file_path

    def load(self, selector: SelectorAsset) -> FinancialIdentifiers:
        """
        Initialize FinancailIdentifiers from a JSON file.

        Validation of data using RegistryFileDto, invalid entries are skipped
        """
        logger.info(f"Load static data from JSON file: {str(self._file_path)}")

        raw_json_data = self._load_from_file()

        # full declarative, create a chain of generators
        gen_raw_entries = ((name, entry) for name, entry in raw_json_data.items())
        # Validate entries and filter out None values immediately
        validated_dto = map(self._validate_entries, gen_raw_entries)
        f_validated_dto = filter(is_not_none, validated_dto)
        # transform to domain model
        validated_entry = map(self._dto_to_domain, f_validated_dto)
        # apply  selector
        selected_entry = filter(lambda t: self._apply_filtering(selector, t), validated_entry)

        fin_id = FinancialIdentifiers()
        for name_entry in selected_entry:
            fin_id[name_entry.name] = name_entry.entry

        return fin_id

    def update_registry(self, pendings: list[PendingIdentifierEntryUpdate]) -> tuple[str | None, str | None]:
        """
        Combine pending updates with previous data.

        Backup the previous registry file with an incremented suffix and rewrite the
        current registry with merged content.

        return: updated ressource and backup ressource (filepath stirng for files)
        """
        # load only valid data
        raw_data_json = self._load_from_file()
        # data_dto = self._validate_entries(raw_data_json)

        gen_raw_entries = ((name, entry) for name, entry in raw_data_json.items())
        # Validate entries and filter out None values immediately
        validated_dto = map(self._validate_entries, gen_raw_entries)
        data_dto_it = filter(is_not_none, validated_dto)

        #
        data_dto = dict(data_dto_it)

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

    def _load_from_file(self) -> dict[str, dict[str, Any]]:
        """
        Parses JSON fast (no loaded in memory), validate only the Json format
        """
        if not pathlib.Path(self._file_path).exists():
            raise IdentifierRegistryFileNotExistingError("file not existing: " + str(self._file_path))

        try:
            # validate JSON format, fast still avoiding json.load()
            raw_data = RAW_DICT_ADAPTER.validate_json(self._file_path.read_bytes())
        except ValidationError as ex:
            logger.error(f"Invalid JSON format: {ex}")
            raise IdentifierRegistryError("Invalid JSON format: " + str(self._file_path))

        return raw_data

    def _validate_entries(self, tentry: tuple[str, dict[str, Any]]) -> NamedEntryDto | None:
        """
        Validate FinancialIdentifierEntry with DTO

        Log reason and return None if invalid
        """

        raw_key = tentry[0]
        raw_entry = tentry[1]
        try:
            key = KEY_ADAPTER.validate_python(raw_key)
            entry = RegistryFileEntryDto.model_validate(raw_entry)
            return NamedEntryDto(key, entry)

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
            return None

    @staticmethod
    def _apply_filtering(selector: SelectorAsset, name_entry: NamedEntry) -> bool:
        """
        For file registry, the selector acts as a filter predicate
        """
        return selector.as_filter(name_entry.name, name_entry.entry)

    def _dto_to_domain(self, named_entry_dto: NamedEntryDto) -> NamedEntry:
        """
        Initialize a FinancialIdentierEntry domain model from validated entries
        """

        entry_dto = named_entry_dto.entry
        entry = FinancialIdentifierEntry(
            entry_dto.yfTicker, asset_type=entry_dto.assetType, currency=entry_dto.currency, isin=entry_dto.isin
        )
        return NamedEntry(named_entry_dto.name, entry)

    def _entry_to_dto(self, entry: FinancialIdentifierEntry) -> RegistryFileEntryDto:
        """Create Dto from domain models. Make dump easier, input from domain models are valid"""

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
