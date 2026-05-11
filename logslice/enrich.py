"""logslice.enrich — Attach derived fields to log entries.

Provides utilities for enriching LogEntry objects with computed metadata
such as hostname tags, environment labels, source file references, or
arbitrary key/value annotations stored in the entry's extras dict.
"""

from __future__ import annotations

import re
import socket
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from logslice.parser import LogEntry


# ---------------------------------------------------------------------------
# Enricher protocol
# ---------------------------------------------------------------------------

EnricherFn = Callable[[LogEntry], LogEntry]


def _clone_with_extras(entry: LogEntry, updates: Dict[str, str]) -> LogEntry:
    """Return a shallow copy of *entry* with *updates* merged into extras."""
    new_extras = dict(entry.extras or {})
    new_extras.update(updates)
    return LogEntry(
        timestamp=entry.timestamp,
        severity=entry.severity,
        message=entry.message,
        raw=entry.raw,
        extras=new_extras,
    )


# ---------------------------------------------------------------------------
# Built-in enrichers
# ---------------------------------------------------------------------------

def add_hostname(entry: LogEntry, hostname: Optional[str] = None) -> LogEntry:
    """Tag *entry* with the current (or supplied) hostname.

    Args:
        entry: The log entry to enrich.
        hostname: Override value; defaults to ``socket.gethostname()``.

    Returns:
        A new LogEntry with ``extras['hostname']`` set.
    """
    host = hostname or socket.gethostname()
    return _clone_with_extras(entry, {"hostname": host})


def add_static_fields(entry: LogEntry, fields: Dict[str, str]) -> LogEntry:
    """Attach a fixed dict of key/value pairs to every entry.

    Useful for tagging entries with environment, region, service name, etc.

    Args:
        entry: The log entry to enrich.
        fields: Mapping of field names to static string values.

    Returns:
        A new LogEntry with *fields* merged into extras.
    """
    return _clone_with_extras(entry, fields)


def extract_fields(entry: LogEntry, pattern: str, flags: int = 0) -> LogEntry:
    """Parse named groups from the message and store them in extras.

    Example pattern: ``r'user=(?P<user>\\S+) action=(?P<action>\\S+)'``

    Args:
        entry: The log entry to enrich.
        pattern: A regex string with named capture groups.
        flags: Optional ``re`` flags (e.g. ``re.IGNORECASE``).

    Returns:
        A new LogEntry with any matched groups added to extras.
    """
    match = re.search(pattern, entry.message, flags)
    if not match:
        return entry
    return _clone_with_extras(entry, match.groupdict())


# ---------------------------------------------------------------------------
# Pipeline helper
# ---------------------------------------------------------------------------

@dataclass
class Enricher:
    """Composable chain of enricher functions applied to each log entry.

    Example::

        enricher = (
            Enricher()
            .add(lambda e: add_hostname(e))
            .add(lambda e: add_static_fields(e, {"env": "prod"}))
        )
        enriched = enricher.run(entries)
    """

    _steps: List[EnricherFn] = field(default_factory=list, init=False, repr=False)

    def add(self, fn: EnricherFn) -> "Enricher":
        """Append *fn* to the enrichment chain and return *self*."""
        self._steps.append(fn)
        return self

    def apply(self, entry: LogEntry) -> LogEntry:
        """Run all enrichment steps on a single *entry*."""
        for step in self._steps:
            entry = step(entry)
        return entry

    def run(self, entries: List[LogEntry]) -> List[LogEntry]:
        """Apply the full enrichment chain to every entry in *entries*.

        Args:
            entries: Source log entries.

        Returns:
            A new list of enriched LogEntry objects.
        """
        return [self.apply(e) for e in entries]

    def __len__(self) -> int:  # pragma: no cover
        return len(self._steps)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Enricher(steps={len(self._steps)})"
