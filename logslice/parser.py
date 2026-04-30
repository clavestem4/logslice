"""Core log entry parser for logslice."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

LOG_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
    r"\s+(?P<severity>DEBUG|INFO|WARNING|ERROR|CRITICAL)"
    r"\s+(?P<message>.*)"
)

TIMESTAMP_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
]


@dataclass
class LogEntry:
    timestamp: datetime
    severity: str
    message: str
    raw: str


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Attempt to parse a timestamp string using known formats."""
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return None


def parse_line(line: str) -> Optional[LogEntry]:
    """Parse a single log line into a LogEntry, or return None if unparseable."""
    line = line.rstrip("\n")
    match = LOG_PATTERN.match(line)
    if not match:
        return None

    timestamp = parse_timestamp(match.group("timestamp"))
    if timestamp is None:
        return None

    return LogEntry(
        timestamp=timestamp,
        severity=match.group("severity"),
        message=match.group("message"),
        raw=line,
    )


def parse_lines(lines) -> list[LogEntry]:
    """Parse an iterable of log lines, skipping unparseable entries."""
    entries = []
    for line in lines:
        entry = parse_line(line)
        if entry is not None:
            entries.append(entry)
    return entries
