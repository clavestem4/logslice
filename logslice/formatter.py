"""Output formatters for log entries."""

import json
from typing import List, Optional
from logslice.parser import LogEntry


SUPPORTED_FORMATS = ("text", "json", "csv")


def format_entry_text(entry: LogEntry, show_raw: bool = False) -> str:
    """Format a LogEntry as a human-readable text line."""
    if show_raw and entry.raw:
        return entry.raw
    ts = entry.timestamp.isoformat() if entry.timestamp else "(no timestamp)"
    severity = f"[{entry.severity}]" if entry.severity else ""
    parts = [ts, severity, entry.message]
    return " ".join(p for p in parts if p)


def format_entry_json(entry: LogEntry) -> str:
    """Format a LogEntry as a JSON string."""
    data = {
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        "severity": entry.severity,
        "message": entry.message,
    }
    return json.dumps(data)


def format_entry_csv(entry: LogEntry) -> str:
    """Format a LogEntry as a CSV row (timestamp, severity, message)."""
    ts = entry.timestamp.isoformat() if entry.timestamp else ""
    severity = entry.severity or ""
    message = entry.message.replace('"', '""')
    return f'"{ts}","{severity}","{message}"'


def format_entries(
    entries: List[LogEntry],
    fmt: str = "text",
    show_raw: bool = False,
) -> List[str]:
    """Format a list of LogEntry objects into strings.

    Args:
        entries: List of LogEntry objects to format.
        fmt: Output format — one of 'text', 'json', 'csv'.
        show_raw: If True and fmt is 'text', emit the original raw line.

    Returns:
        List of formatted strings.

    Raises:
        ValueError: If fmt is not a supported format.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format {fmt!r}. Choose from {SUPPORTED_FORMATS}.")

    lines: List[str] = []

    if fmt == "csv":
        lines.append('"timestamp","severity","message"')

    for entry in entries:
        if fmt == "text":
            lines.append(format_entry_text(entry, show_raw=show_raw))
        elif fmt == "json":
            lines.append(format_entry_json(entry))
        elif fmt == "csv":
            lines.append(format_entry_csv(entry))

    return lines


def render(
    entries: List[LogEntry],
    fmt: str = "text",
    show_raw: bool = False,
) -> str:
    """Render entries to a single newline-joined string."""
    return "\n".join(format_entries(entries, fmt=fmt, show_raw=show_raw))
