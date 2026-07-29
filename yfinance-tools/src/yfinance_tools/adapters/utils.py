"""
Need better file name,
internal use only
"""

from typing import NamedTuple, Optional, TypeGuard

from yfinance_tools.domain import FinancialIdentifierEntry

from .basic_types_dto import AssetNameDto
from .file_identifier_dto import RegistryFileEntryDto


class NamedEntry(NamedTuple):
    name: str
    entry: FinancialIdentifierEntry


class NamedEntryDto(NamedTuple):
    name: AssetNameDto
    entry: RegistryFileEntryDto


def is_not_none(value: Optional[NamedEntryDto]) -> TypeGuard[NamedEntryDto]:
    """Explicit method to help static analysis tools"""
    return value is not None
