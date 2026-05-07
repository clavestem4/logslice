"""Rate limiting and throttling utilities for log entry streams."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogEntry


@dataclass
class RateWindow:
    """Tracks entry counts within a sliding time window."""

    window_seconds: int
    max_entries: int
    _timestamps: List[datetime] = field(default_factory=list, repr=False)

    def _evict_old(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=self.window_seconds)
        self._timestamps = [t for t in self._timestamps if t >= cutoff]

    def allow(self, entry: LogEntry) -> bool:
        """Return True if the entry is within the allowed rate."""
        now = entry.timestamp if entry.timestamp else datetime.utcnow()
        self._evict_old(now)
        if len(self._timestamps) < self.max_entries:
            self._timestamps.append(now)
            return True
        return False

    @property
    def current_count(self) -> int:
        return len(self._timestamps)

    def as_dict(self) -> dict:
        return {
            "window_seconds": self.window_seconds,
            "max_entries": self.max_entries,
            "current_count": self.current_count,
        }

    def __str__(self) -> str:
        return (
            f"RateWindow(window={self.window_seconds}s, "
            f"max={self.max_entries}, current={self.current_count})"
        )


def throttle_entries(
    entries: Iterable[LogEntry],
    window_seconds: int,
    max_entries: int,
) -> Iterator[LogEntry]:
    """Yield only entries that fall within the allowed rate."""
    window = RateWindow(window_seconds=window_seconds, max_entries=max_entries)
    for entry in entries:
        if window.allow(entry):
            yield entry


def rate_exceeded(
    entries: Iterable[LogEntry],
    window_seconds: int,
    max_entries: int,
) -> List[LogEntry]:
    """Return entries that were dropped due to rate limiting."""
    window = RateWindow(window_seconds=window_seconds, max_entries=max_entries)
    dropped: List[LogEntry] = []
    for entry in entries:
        if not window.allow(entry):
            dropped.append(entry)
    return dropped


def compute_rate(
    entries: List[LogEntry],
    window_seconds: int = 60,
) -> Optional[float]:
    """Return entries-per-second over the span of the entry list."""
    timestamped = [e for e in entries if e.timestamp]
    if len(timestamped) < 2:
        return None
    span = (timestamped[-1].timestamp - timestamped[0].timestamp).total_seconds()
    if span <= 0:
        return None
    return len(timestamped) / span
