"""diff.py — Compare two sequences of log entries and report additions, removals, and changes.

Useful for auditing log output across deployments or time windows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence, Tuple

from logslice.parser import LogEntry
from logslice.dedupe import entry_fingerprint


@dataclass
class DiffResult:
    """Holds the outcome of comparing two entry sequences."""

    added: List[LogEntry] = field(default_factory=list)
    removed: List[LogEntry] = field(default_factory=list)
    common: List[LogEntry] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Derived counts
    # ------------------------------------------------------------------ #

    @property
    def added_count(self) -> int:
        return len(self.added)

    @property
    def removed_count(self) -> int:
        return len(self.removed)

    @property
    def common_count(self) -> int:
        return len(self.common)

    def as_dict(self) -> dict:
        """Return a plain-dict summary suitable for JSON serialisation."""
        return {
            "added": self.added_count,
            "removed": self.removed_count,
            "common": self.common_count,
        }

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"DiffResult(added={self.added_count}, "
            f"removed={self.removed_count}, "
            f"common={self.common_count})"
        )


# --------------------------------------------------------------------------- #
# Core comparison helpers
# --------------------------------------------------------------------------- #


def _fingerprint_set(
    entries: Sequence[LogEntry],
) -> dict[str, LogEntry]:
    """Map fingerprint -> first matching entry (duplicates collapsed)."""
    result: dict[str, LogEntry] = {}
    for entry in entries:
        fp = entry_fingerprint(entry)
        if fp not in result:
            result[fp] = entry
    return result


def diff_entries(
    before: Sequence[LogEntry],
    after: Sequence[LogEntry],
) -> DiffResult:
    """Compare *before* and *after* entry lists by fingerprint.

    An entry present only in *after* is considered **added**.
    An entry present only in *before* is considered **removed**.
    Entries whose fingerprint appears in both lists are **common**.

    Args:
        before: The baseline sequence of log entries.
        after:  The new sequence of log entries to compare against *before*.

    Returns:
        A :class:`DiffResult` instance populated with the three categories.
    """
    before_map = _fingerprint_set(before)
    after_map = _fingerprint_set(after)

    before_fps = set(before_map)
    after_fps = set(after_map)

    added = [after_map[fp] for fp in sorted(after_fps - before_fps)]
    removed = [before_map[fp] for fp in sorted(before_fps - after_fps)]
    common = [before_map[fp] for fp in sorted(before_fps & after_fps)]

    return DiffResult(added=added, removed=removed, common=common)


def diff_summary(result: DiffResult) -> str:
    """Return a human-readable one-line summary of a :class:`DiffResult`."""
    parts: List[str] = []
    if result.added_count:
        parts.append(f"+{result.added_count} added")
    if result.removed_count:
        parts.append(f"-{result.removed_count} removed")
    if result.common_count:
        parts.append(f"={result.common_count} common")
    return ", ".join(parts) if parts else "no differences"


def changed_entries(
    before: Sequence[LogEntry],
    after: Sequence[LogEntry],
) -> List[Tuple[LogEntry, LogEntry]]:
    """Return pairs of (before, after) entries whose raw text differs but
    whose fingerprint (severity + normalised message) is the same.

    This catches entries that share a fingerprint yet have a different raw
    log line — e.g. the same message with an updated timestamp.

    Args:
        before: Baseline entries.
        after:  Comparison entries.

    Returns:
        List of *(before_entry, after_entry)* tuples where the raw text
        differs despite matching fingerprints.
    """
    before_map = _fingerprint_set(before)
    after_map = _fingerprint_set(after)

    pairs: List[Tuple[LogEntry, LogEntry]] = []
    for fp in set(before_map) & set(after_map):
        b = before_map[fp]
        a = after_map[fp]
        if b.raw != a.raw:
            pairs.append((b, a))
    return pairs
