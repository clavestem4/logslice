"""Export log entries to various file formats."""

from __future__ import annotations

import csv
import json
import io
from pathlib import Path
from typing import Iterable, Literal

from logslice.parser import LogEntry
from logslice.formatter import format_entry_json, format_entry_csv, format_entry_text

ExportFormat = Literal["text", "json", "csv", "jsonl"]


def export_text(entries: Iterable[LogEntry], dest: Path) -> int:
    """Write entries as plain text lines. Returns count written."""
    count = 0
    with dest.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(format_entry_text(entry) + "\n")
            count += 1
    return count


def export_jsonl(entries: Iterable[LogEntry], dest: Path) -> int:
    """Write entries as newline-delimited JSON. Returns count written."""
    count = 0
    with dest.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(format_entry_json(entry) + "\n")
            count += 1
    return count


def export_json(entries: Iterable[LogEntry], dest: Path) -> int:
    """Write entries as a JSON array. Returns count written."""
    records = []
    for entry in entries:
        records.append(json.loads(format_entry_json(entry)))
    with dest.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, default=str)
    return len(records)


def export_csv(entries: Iterable[LogEntry], dest: Path) -> int:
    """Write entries as CSV with a header row. Returns count written."""
    count = 0
    with dest.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "severity", "message", "raw"])
        for entry in entries:
            row = format_entry_csv(entry)
            writer.writerow(row.split(",", 3))
            count += 1
    return count


def export_entries(
    entries: Iterable[LogEntry],
    dest: Path,
    fmt: ExportFormat = "text",
) -> int:
    """Dispatch export to the appropriate format handler."""
    handlers = {
        "text": export_text,
        "jsonl": export_jsonl,
        "json": export_json,
        "csv": export_csv,
    }
    if fmt not in handlers:
        raise ValueError(f"Unsupported export format: {fmt!r}")
    return handlers[fmt](entries, dest)
