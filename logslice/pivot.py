"""Pivot log entries into a structured table grouped by a key field."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class PivotTable:
    """A table of log entries grouped by a key."""

    key: str
    groups: Dict[str, List[LogEntry]] = field(default_factory=dict)

    def group_keys(self) -> List[str]:
        """Return sorted list of group keys."""
        return sorted(self.groups.keys())

    def group_counts(self) -> Dict[str, int]:
        """Return a mapping of group key to entry count."""
        return {k: len(v) for k, v in self.groups.items()}

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "groups": {
                k: [e.raw for e in v] for k, v in self.groups.items()
            },
        }

    def __str__(self) -> str:
        lines = [f"PivotTable(key={self.key!r})"]
        for k in self.group_keys():
            lines.append(f"  {k!r}: {len(self.groups[k])} entries")
        return "\n".join(lines)


def _key_severity(entry: LogEntry) -> Optional[str]:
    return entry.severity or "UNKNOWN"


def _key_date(entry: LogEntry) -> Optional[str]:
    if entry.timestamp is None:
        return "no-date"
    return entry.timestamp.strftime("%Y-%m-%d")


def _key_hour(entry: LogEntry) -> Optional[str]:
    if entry.timestamp is None:
        return "no-date"
    return entry.timestamp.strftime("%Y-%m-%dT%H")


_BUILTIN_KEYS: Dict[str, Callable[[LogEntry], Optional[str]]] = {
    "severity": _key_severity,
    "date": _key_date,
    "hour": _key_hour,
}


def pivot(
    entries: List[LogEntry],
    key: str = "severity",
    key_fn: Optional[Callable[[LogEntry], Optional[str]]] = None,
) -> PivotTable:
    """Group *entries* by *key* and return a PivotTable.

    Args:
        entries: Log entries to pivot.
        key: Named key to group by ('severity', 'date', 'hour').
        key_fn: Custom callable that accepts a LogEntry and returns a string
                group label.  When provided, *key* is used only as a label.
    """
    if key_fn is None:
        if key not in _BUILTIN_KEYS:
            raise ValueError(
                f"Unknown pivot key {key!r}. "
                f"Choose from {list(_BUILTIN_KEYS)} or supply key_fn."
            )
        key_fn = _BUILTIN_KEYS[key]

    groups: Dict[str, List[LogEntry]] = defaultdict(list)
    for entry in entries:
        label = key_fn(entry) or "UNKNOWN"
        groups[label].append(entry)

    return PivotTable(key=key, groups=dict(groups))
