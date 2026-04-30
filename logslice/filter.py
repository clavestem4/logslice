"""Filtering utilities for log entries by time range and severity."""

from datetime import datetime
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogEntry

# Severity levels ordered from lowest to highest
SEVERITY_LEVELS = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "WARN": 2,
    "ERROR": 3,
    "CRITICAL": 4,
    "FATAL": 4,
}


def severity_rank(level: str) -> int:
    """Return numeric rank for a severity level string."""
    return SEVERITY_LEVELS.get(level.upper(), -1)


def filter_by_time(
    entries: Iterable[LogEntry],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Iterator[LogEntry]:
    """Yield entries whose timestamp falls within [start, end]."""
    for entry in entries:
        if entry.timestamp is None:
            continue
        if start is not None and entry.timestamp < start:
            continue
        if end is not None and entry.timestamp > end:
            continue
        yield entry


def filter_by_severity(
    entries: Iterable[LogEntry],
    min_level: Optional[str] = None,
    max_level: Optional[str] = None,
) -> Iterator[LogEntry]:
    """Yield entries whose severity is within [min_level, max_level]."""
    min_rank = severity_rank(min_level) if min_level else -1
    max_rank = severity_rank(max_level) if max_level else 999

    for entry in entries:
        rank = severity_rank(entry.level) if entry.level else -1
        if rank < min_rank or rank > max_rank:
            continue
        yield entry


def apply_filters(
    entries: Iterable[LogEntry],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    min_level: Optional[str] = None,
    max_level: Optional[str] = None,
) -> List[LogEntry]:
    """Apply time and severity filters and return a list of matching entries."""
    result = filter_by_time(entries, start=start, end=end)
    result = filter_by_severity(result, min_level=min_level, max_level=max_level)
    return list(result)
