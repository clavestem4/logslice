"""Offset-based index for fast log file seeking by timestamp."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from logslice.parser import parse_line


@dataclass
class IndexEntry:
    offset: int
    timestamp: datetime
    line_number: int

    def as_dict(self) -> dict:
        return {
            "offset": self.offset,
            "timestamp": self.timestamp.isoformat(),
            "line_number": self.line_number,
        }


@dataclass
class LogIndex:
    source: str
    entries: List[IndexEntry] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "entries": [e.as_dict() for e in self.entries],
        }

    def __len__(self) -> int:
        return len(self.entries)

    def __repr__(self) -> str:
        return f"LogIndex(source={self.source!r}, entries={len(self.entries)})"


def build_index(path: str, step: int = 100) -> LogIndex:
    """Build an offset index by sampling every `step` lines."""
    index = LogIndex(source=path)
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        line_number = 0
        while True:
            offset = fh.tell()
            raw = fh.readline()
            if not raw:
                break
            if line_number % step == 0:
                entry = parse_line(raw)
                if entry is not None and entry.timestamp is not None:
                    index.entries.append(
                        IndexEntry(
                            offset=offset,
                            timestamp=entry.timestamp,
                            line_number=line_number,
                        )
                    )
            line_number += 1
    return index


def seek_to_time(index: LogIndex, target: datetime) -> Optional[int]:
    """Return the file offset of the last index entry at or before `target`."""
    result: Optional[int] = None
    for ie in index.entries:
        if ie.timestamp <= target:
            result = ie.offset
        else:
            break
    return result


def save_index(index: LogIndex, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(index.as_dict(), fh, indent=2)


def load_index(path: str) -> LogIndex:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    entries = [
        IndexEntry(
            offset=e["offset"],
            timestamp=datetime.fromisoformat(e["timestamp"]),
            line_number=e["line_number"],
        )
        for e in data.get("entries", [])
    ]
    return LogIndex(source=data["source"], entries=entries)
