"""Replay log entries at a controlled speed, simulating real-time log streaming."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, Optional

from logslice.parser import LogEntry


@dataclass
class ReplayOptions:
    """Configuration for replaying log entries."""

    speed: float = 1.0          # Multiplier: 2.0 = twice as fast, 0.5 = half speed
    max_delay: float = 5.0      # Cap on inter-entry delay in seconds
    real_time: bool = True      # If False, emit entries with no delay
    on_emit: Optional[Callable[[LogEntry], None]] = field(default=None, repr=False)


def _delay_seconds(prev: LogEntry, current: LogEntry, options: ReplayOptions) -> float:
    """Calculate how long to wait before emitting *current* after *prev*."""
    if not options.real_time or prev.timestamp is None or current.timestamp is None:
        return 0.0
    delta = (current.timestamp - prev.timestamp).total_seconds()
    if delta <= 0:
        return 0.0
    adjusted = delta / max(options.speed, 1e-9)
    return min(adjusted, options.max_delay)


def replay_entries(
    entries: Iterable[LogEntry],
    options: Optional[ReplayOptions] = None,
) -> Iterator[LogEntry]:
    """Yield entries with timing delays that mirror the original log cadence.

    Args:
        entries: Ordered sequence of log entries to replay.
        options: Replay configuration.  Defaults to real-time at 1× speed.

    Yields:
        Each :class:`~logslice.parser.LogEntry` after the appropriate delay.
    """
    if options is None:
        options = ReplayOptions()

    prev: Optional[LogEntry] = None
    for entry in entries:
        if prev is not None:
            delay = _delay_seconds(prev, entry, options)
            if delay > 0:
                time.sleep(delay)
        if options.on_emit:
            options.on_emit(entry)
        yield entry
        prev = entry


def replay_count(entries: Iterable[LogEntry], options: Optional[ReplayOptions] = None) -> int:
    """Replay *entries* and return the total number emitted."""
    total = 0
    for _ in replay_entries(entries, options):
        total += 1
    return total
