"""Entry transformation utilities for logslice."""

from typing import Callable, List, Optional
from logslice.parser import LogEntry


def redact_message(entry: LogEntry, pattern: str, replacement: str = "[REDACTED]") -> LogEntry:
    """Return a new LogEntry with pattern replaced in the message."""
    import re
    new_message = re.sub(pattern, replacement, entry.message)
    return LogEntry(
        timestamp=entry.timestamp,
        severity=entry.severity,
        message=new_message,
        raw=entry.raw,
    )


def normalize_severity(entry: LogEntry) -> LogEntry:
    """Return a new LogEntry with severity uppercased and stripped."""
    new_severity = entry.severity.strip().upper() if entry.severity else entry.severity
    return LogEntry(
        timestamp=entry.timestamp,
        severity=new_severity,
        message=entry.message,
        raw=entry.raw,
    )


def truncate_message(entry: LogEntry, max_length: int) -> LogEntry:
    """Return a new LogEntry with message truncated to max_length characters."""
    if max_length < 0:
        raise ValueError("max_length must be non-negative")
    new_message = entry.message[:max_length] if len(entry.message) > max_length else entry.message
    return LogEntry(
        timestamp=entry.timestamp,
        severity=entry.severity,
        message=new_message,
        raw=entry.raw,
    )


def apply_transform(
    entries: List[LogEntry],
    transform: Callable[[LogEntry], Optional[LogEntry]],
) -> List[LogEntry]:
    """Apply a transform function to each entry, dropping None results."""
    result = []
    for entry in entries:
        transformed = transform(entry)
        if transformed is not None:
            result.append(transformed)
    return result
