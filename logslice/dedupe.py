"""Deduplication utilities for log entries."""

from __future__ import annotations

import hashlib
from typing import Iterable, Iterator

from logslice.parser import LogEntry


def entry_fingerprint(entry: LogEntry) -> str:
    """Return a stable hash fingerprint for a log entry.

    The fingerprint is based on the severity and the raw message text,
    ignoring the timestamp so that repeated identical messages emitted at
    different times are considered duplicates.
    """
    key = f"{entry.severity or ''}|{entry.message}"
    return hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()


def deduplicate(
    entries: Iterable[LogEntry],
    *,
    keep: str = "first",
    max_seen: int | None = None,
) -> Iterator[LogEntry]:
    """Yield unique log entries, dropping consecutive or global duplicates.

    Args:
        entries: Iterable of LogEntry objects to filter.
        keep: ``"first"`` keeps the first occurrence of each duplicate group;
              ``"last"`` buffers and yields the final occurrence (requires
              consuming the full iterable).
        max_seen: If given, only remember this many fingerprints to bound
                  memory usage.  Oldest fingerprints are evicted first.

    Yields:
        LogEntry objects with duplicates removed.
    """
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    seen: dict[str, LogEntry] = {}

    for entry in entries:
        fp = entry_fingerprint(entry)

        if keep == "first":
            if fp not in seen:
                if max_seen is not None and len(seen) >= max_seen:
                    # evict the oldest key
                    oldest = next(iter(seen))
                    del seen[oldest]
                seen[fp] = entry
                yield entry
        else:  # keep == "last"
            seen[fp] = entry
            if max_seen is not None and len(seen) > max_seen:
                oldest = next(iter(seen))
                del seen[oldest]

    if keep == "last":
        yield from seen.values()


def count_duplicates(entries: Iterable[LogEntry]) -> dict[str, int]:
    """Return a mapping of fingerprint -> occurrence count."""
    counts: dict[str, int] = {}
    for entry in entries:
        fp = entry_fingerprint(entry)
        counts[fp] = counts.get(fp, 0) + 1
    return counts
