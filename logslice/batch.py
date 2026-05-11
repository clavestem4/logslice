"""Batch processing utilities for grouping log entries into fixed-size or time-based chunks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Iterator, List, Optional

from logslice.parser import LogEntry


@dataclass
class Batch:
    """A group of log entries collected together."""

    entries: List[LogEntry] = field(default_factory=list)
    index: int = 0

    @property
    def size(self) -> int:
        return len(self.entries)

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "size": self.size,
            "entries": [
                {"timestamp": str(e.timestamp), "severity": e.severity, "message": e.message}
                for e in self.entries
            ],
        }

    def __str__(self) -> str:  # pragma: no cover
        return f"Batch(index={self.index}, size={self.size})"


def batch_by_size(entries: List[LogEntry], n: int) -> Iterator[Batch]:
    """Yield successive Batch objects each containing at most *n* entries."""
    if n <= 0:
        return
    for batch_index, start in enumerate(range(0, len(entries), n)):
        yield Batch(entries=entries[start : start + n], index=batch_index)


def batch_by_time(
    entries: List[LogEntry],
    window: timedelta,
    *,
    anchor: Optional[object] = None,
) -> Iterator[Batch]:
    """Yield Batch objects where all entries fall within a rolling *window*.

    Entries without a timestamp are placed in the current open batch.
    """
    if window.total_seconds() <= 0:
        return

    current: List[LogEntry] = []
    batch_index = 0
    window_start = anchor  # may be None until first timestamped entry

    for entry in entries:
        ts = entry.timestamp
        if ts is None or window_start is None:
            current.append(entry)
            if ts is not None and window_start is None:
                window_start = ts
            continue

        if (ts - window_start) >= window:
            if current:
                yield Batch(entries=current, index=batch_index)
                batch_index += 1
            current = [entry]
            window_start = ts
        else:
            current.append(entry)

    if current:
        yield Batch(entries=current, index=batch_index)


def count_batches(entries: List[LogEntry], n: int) -> int:
    """Return the number of size-based batches that would be produced."""
    if n <= 0 or not entries:
        return 0
    return (len(entries) + n - 1) // n
