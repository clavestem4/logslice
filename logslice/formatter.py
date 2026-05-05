"""Formatting utilities for LogEntry objects."""

import json
from typing import Iterable, Optional
from logslice.parser import LogEntry
from logslice.highlight import highlight_line, supports_color
import sys


def format_entry_text(entry: LogEntry, show_raw: bool = False) -> str:
    """Format a LogEntry as a human-readable text line."""
    if show_raw and entry.raw:
        return entry.raw
    parts = []
    if entry.timestamp:
        parts.append(entry.timestamp.isoformat(sep=" "))
    if entry.severity:
        parts.append(f"[{entry.severity.upper()}]")
    if entry.message:
        parts.append(entry.message)
    return " ".join(parts) if parts else (entry.raw or "")


def format_entry_json(entry: LogEntry) -> str:
    """Format a LogEntry as a JSON string."""
    data = {
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        "severity": entry.severity,
        "message": entry.message,
    }
    return json.dumps(data)


def format_entry_csv(entry: LogEntry) -> str:
    """Format a LogEntry as a CSV row (timestamp,severity,message)."""
    import csv
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        entry.timestamp.isoformat() if entry.timestamp else "",
        entry.severity or "",
        entry.message or "",
    ])
    return buf.getvalue().rstrip("\r\n")


def format_entries(
    entries: Iterable[LogEntry],
    fmt: str = "text",
    show_raw: bool = False,
    color: Optional[bool] = None,
    stream=None,
) -> Iterable[str]:
    """Yield formatted strings for each entry.

    Args:
        entries: Iterable of LogEntry objects.
        fmt: Output format — 'text', 'json', or 'csv'.
        show_raw: If True and fmt='text', emit the raw log line.
        color: Force color on/off; None = auto-detect from stream.
        stream: Output stream used for color auto-detection.
    """
    if stream is None:
        stream = sys.stdout
    use_color = supports_color(stream) if color is None else color

    for entry in entries:
        if fmt == "json":
            yield format_entry_json(entry)
        elif fmt == "csv":
            yield format_entry_csv(entry)
        else:
            line = format_entry_text(entry, show_raw=show_raw)
            yield highlight_line(line, entry.severity, enabled=use_color)


def render(
    entries: Iterable[LogEntry],
    fmt: str = "text",
    show_raw: bool = False,
    color: Optional[bool] = None,
    stream=None,
) -> str:
    """Render all entries to a single newline-joined string."""
    lines = list(format_entries(entries, fmt=fmt, show_raw=show_raw, color=color, stream=stream))
    return "\n".join(lines)
