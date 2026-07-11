"""
Store identifier entries
"""

import copy
from dataclasses import dataclass, field
from typing import TypeAlias

from .exceptions import IdentifierError
from .financial_identifier_entry import FinancialIdentifierEntry, PendingIdentifierEntryUpdate

# Alias, str is always the "name", unique identifier
IdentifierEntryDict: TypeAlias = dict[str, FinancialIdentifierEntry]


# no real advantage to use dataclass here, it is a dictionnary or a list (but must include name)
@dataclass
class FinancialIdentifiers:
    """
    Container of asset identifier entries.

    - allow filtering by name / isin, asset type (TODO),
    - open-close state with market ?
    """

    # with init=False: not present in constructor
    _entries: IdentifierEntryDict = field(init=False, default_factory=IdentifierEntryDict)

    # TODO IdentifierEntryDict
    def add_entry(self, name: str, entry: FinancialIdentifierEntry) -> None:
        self._entries[name] = entry

    def get_entries(self) -> list[str]:
        return list(self._entries.keys())

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

    def __len__(self) -> int:
        return len(self._entries)

    def update_entry(self, name: str, new_entry: FinancialIdentifierEntry) -> None:
        """Add new or replace previous entry"""

        # but as CLI forbids human validation
        self._entries[name] = new_entry
