"""High-level API for slicing log files by time range and severity."""

from datetime import datetime
from typing import List, Optional, Union
from pathlib import Path

from logslice.parser import LogEntry, parse_lines
from logslice.filter import apply_filters


def slice_file(
    path: Union[str, Path],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    min_level: Optional[str] = None,
    max_level: Optional[str] = None,
    encoding: str = "utf-8",
) -> List[LogEntry]:
    """Parse a log file and return entries matching the given criteria.

    Args:
        path: Path to the log file.
        start: Inclusive lower bound for entry timestamps.
        end: Inclusive upper bound for entry timestamps.
        min_level: Minimum severity level (e.g. 'INFO').
        max_level: Maximum severity level (e.g. 'ERROR').
        encoding: File encoding (default 'utf-8').

    Returns:
        List of matching LogEntry objects.

    Raises:
        FileNotFoundError: If the specified path does not exist.
        IsADirectoryError: If the specified path is a directory.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"Expected a file, got a directory: {path}")

    with path.open(encoding=encoding, errors="replace") as fh:
        lines = fh.readlines()

    entries = parse_lines(lines)
    return apply_filters(
        entries,
        start=start,
        end=end,
        min_level=min_level,
        max_level=max_level,
    )


def slice_text(
    text: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    min_level: Optional[str] = None,
    max_level: Optional[str] = None,
) -> List[LogEntry]:
    """Parse a log string and return entries matching the given criteria.

    Args:
        text: Raw log content as a string.
        start: Inclusive lower bound for entry timestamps.
        end: Inclusive upper bound for entry timestamps.
        min_level: Minimum severity level.
        max_level: Maximum severity level.

    Returns:
        List of matching LogEntry objects.
    """
    lines = text.splitlines(keepends=True)
    entries = parse_lines(lines)
    return apply_filters(
        entries,
        start=start,
        end=end,
        min_level=min_level,
        max_level=max_level,
    )
