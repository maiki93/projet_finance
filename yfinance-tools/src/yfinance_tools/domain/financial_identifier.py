"""
Store identifier entries
"""

import copy
from dataclasses import dataclass, field
from typing import Iterator, TypeAlias

from .exceptions import IdentifierError
from .financial_identifier_entry import FinancialIdentifierEntry, PendingIdentifierEntryUpdate

# Alias, str is always the "name", unique identifier
IdentifierEntryDict: TypeAlias = dict[str, FinancialIdentifierEntry]


# no real advantage to use dataclass here, it is a dictionnary or a list (but must include name)
# StaticIdentifiers may be a better name
@dataclass
class FinancialIdentifiers:
    """
    Container of asset identifier entries.

    - allow filtering by name and asset type
    - open-close state with market ? TODO
    """

    _entries: IdentifierEntryDict = field(init=False, default_factory=IdentifierEntryDict)

    # TODO replaced by setter, or keep with better name
    def add_entry(self, name: str, entry: FinancialIdentifierEntry) -> None:
        self._entries[name] = entry

    # TODO replaced by Iterator, or keep for better name
    def get_entries(self) -> list[str]:
        return list(self._entries.keys())

    # TODO replaced by getter, or keep for better name
    def find(self, name: str) -> FinancialIdentifierEntry:
        if name not in self._entries:
            raise IdentifierError(f"Asset name not found: {name}")

        return self._entries[name]

    def candidates_for_update(self, force_all: bool) -> IdentifierEntryDict:
        """Candidates for update are entries with missing or invalid value"""
        if force_all:
            return copy.deepcopy(self._entries)

        need_update = {
            name: copy.deepcopy(entry) for name, entry in self._entries.items() if entry.has_missing_values()
        }
        return need_update

    def evaluate_pending_update(self, incoming: IdentifierEntryDict) -> list[PendingIdentifierEntryUpdate]:
        """Validate which incoming data are relevant for an update
        and propose a merge of incoming and original data
        """
        pendings = []
        for name, incoming_entry in incoming.items():
            # brand new asset
            if name not in self._entries:
                pendings.append(PendingIdentifierEntryUpdate(name, incoming_entry, incoming_entry, original=None))
                continue

            # existing ticker
            existing = self._entries[name]
            merged = existing.merge_with(incoming_entry)

            if merged != existing:
                pendings.append(PendingIdentifierEntryUpdate(name, incoming_entry, merged=merged, original=existing))

        return pendings

    # context should be clear enought to know we are updating the Static Data
    def update_entry(self, name: str, new_entry: FinancialIdentifierEntry) -> None:
        """Add new or replace previous entry"""
        self._entries[name] = new_entry

    #
    # Dictionary interface
    #

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[str]:
        """Yields key values"""
        print("call fin_id.__iter__")
        return iter(self._entries)

    def items(self) -> Iterator[tuple[str, FinancialIdentifierEntry]]:
        """Yields (key, value) pairs"""
        return iter(self._entries.items())

    # Access: obj[key] <=> find()
    def __getitem__(self, name: str) -> FinancialIdentifierEntry:
        if name not in self._entries:
            raise IdentifierError(f"Asset name not found: {name}")

        return self._entries[name]

    # Assignment: obj[key] = value
    def __setitem__(self, name: str, value: FinancialIdentifierEntry) -> None:
        self._entries[name] = value
