"""Context window extraction for log entries.

Provides utilities to retrieve N lines of context before and/or after
a matching log entry, similar to grep -A / -B / -C.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from logslice.parser import LogEntry


@dataclass
class ContextWindow:
    """A matched entry together with its surrounding context lines."""

    entry: LogEntry
    before: List[LogEntry] = field(default_factory=list)
    after: List[LogEntry] = field(default_factory=list)

    def all_entries(self) -> List[LogEntry]:
        """Return before + entry + after as a flat list."""
        return self.before + [self.entry] + self.after


def extract_context(
    entries: List[LogEntry],
    indices: List[int],
    before: int = 0,
    after: int = 0,
) -> List[ContextWindow]:
    """Build ContextWindow objects for each matched index.

    Args:
        entries: Full list of log entries.
        indices: Positions of matched entries within *entries*.
        before: Number of entries to include before each match.
        after:  Number of entries to include after each match.

    Returns:
        One ContextWindow per matched index, in order.
    """
    total = len(entries)
    windows: List[ContextWindow] = []
    for idx in indices:
        b_start = max(0, idx - before)
        a_end = min(total, idx + after + 1)
        window = ContextWindow(
            entry=entries[idx],
            before=entries[b_start:idx],
            after=entries[idx + 1 : a_end],
        )
        windows.append(window)
    return windows


def context_around(
    entries: List[LogEntry],
    entry: LogEntry,
    before: int = 0,
    after: int = 0,
) -> Optional[ContextWindow]:
    """Return a ContextWindow for a single entry by identity.

    Returns None if the entry is not found in the list.
    """
    try:
        idx = next(i for i, e in enumerate(entries) if e is entry)
    except StopIteration:
        return None
    return extract_context(entries, [idx], before=before, after=after)[0]
