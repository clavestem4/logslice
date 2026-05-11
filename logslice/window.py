"""Sliding window aggregation over log entries."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Deque, Iterator, List, Optional

from logslice.parser import LogEntry


@dataclass
class WindowResult:
    """A snapshot of entries within a completed window."""

    window_start: datetime
    window_end: datetime
    entries: List[LogEntry]

    @property
    def count(self) -> int:
        return len(self.entries)

    def as_dict(self) -> dict:
        return {
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "count": self.count,
            "entries": [e.raw for e in self.entries],
        }

    def __str__(self) -> str:
        return (
            f"WindowResult({self.window_start.isoformat()} "
            f"-> {self.window_end.isoformat()}, count={self.count})"
        )


@dataclass
class SlidingWindow:
    """Accumulates log entries in a time-based sliding window."""

    duration: timedelta
    _buffer: Deque[LogEntry] = field(default_factory=deque, init=False, repr=False)

    def push(self, entry: LogEntry) -> None:
        """Add an entry and evict entries outside the window."""
        if entry.timestamp is None:
            return
        self._buffer.append(entry)
        self._evict(entry.timestamp)

    def _evict(self, now: datetime) -> None:
        cutoff = now - self.duration
        while self._buffer and (
            self._buffer[0].timestamp is None
            or self._buffer[0].timestamp < cutoff
        ):
            self._buffer.popleft()

    def current(self) -> List[LogEntry]:
        """Return a snapshot of entries currently in the window."""
        return list(self._buffer)

    def __len__(self) -> int:
        return len(self._buffer)


def tumbling_windows(
    entries: List[LogEntry],
    duration: timedelta,
    on_window: Optional[Callable[[WindowResult], None]] = None,
) -> Iterator[WindowResult]:
    """Partition entries into non-overlapping tumbling windows."""
    if not entries:
        return

    timestamped = [e for e in entries if e.timestamp is not None]
    if not timestamped:
        return

    window_start = timestamped[0].timestamp
    window_end = window_start + duration
    bucket: List[LogEntry] = []

    for entry in timestamped:
        while entry.timestamp >= window_end:
            result = WindowResult(window_start, window_end, bucket)
            if on_window:
                on_window(result)
            yield result
            window_start = window_end
            window_end = window_start + duration
            bucket = []
        bucket.append(entry)

    if bucket:
        result = WindowResult(window_start, window_end, bucket)
        if on_window:
            on_window(result)
        yield result
