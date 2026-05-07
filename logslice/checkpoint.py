"""Checkpoint support for resumable log parsing."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Checkpoint:
    """Tracks the last successfully processed position in a log file."""

    file_path: str
    byte_offset: int = 0
    last_timestamp: Optional[datetime] = None
    lines_processed: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def advance(self, byte_offset: int, timestamp: Optional[datetime], lines: int = 1) -> None:
        """Update the checkpoint after processing lines."""
        self.byte_offset = byte_offset
        if timestamp is not None:
            self.last_timestamp = timestamp
        self.lines_processed += lines
        self.updated_at = datetime.utcnow()

    def as_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "byte_offset": self.byte_offset,
            "last_timestamp": self.last_timestamp.isoformat() if self.last_timestamp else None,
            "lines_processed": self.lines_processed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


def save_checkpoint(checkpoint: Checkpoint, checkpoint_dir: str = ".logslice") -> Path:
    """Persist a checkpoint to disk as JSON."""
    dirpath = Path(checkpoint_dir)
    dirpath.mkdir(parents=True, exist_ok=True)
    safe_name = checkpoint.file_path.replace(os.sep, "_").replace("/", "_").strip("_")
    dest = dirpath / f"{safe_name}.checkpoint.json"
    dest.write_text(json.dumps(checkpoint.as_dict(), indent=2))
    return dest


def load_checkpoint(file_path: str, checkpoint_dir: str = ".logslice") -> Optional[Checkpoint]:
    """Load a previously saved checkpoint, or return None if not found."""
    safe_name = file_path.replace(os.sep, "_").replace("/", "_").strip("_")
    src = Path(checkpoint_dir) / f"{safe_name}.checkpoint.json"
    if not src.exists():
        return None
    data = json.loads(src.read_text())
    ts = datetime.fromisoformat(data["last_timestamp"]) if data.get("last_timestamp") else None
    return Checkpoint(
        file_path=data["file_path"],
        byte_offset=data["byte_offset"],
        last_timestamp=ts,
        lines_processed=data["lines_processed"],
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )


def clear_checkpoint(file_path: str, checkpoint_dir: str = ".logslice") -> bool:
    """Delete a checkpoint file. Returns True if deleted, False if not found."""
    safe_name = file_path.replace(os.sep, "_").replace("/", "_").strip("_")
    target = Path(checkpoint_dir) / f"{safe_name}.checkpoint.json"
    if target.exists():
        target.unlink()
        return True
    return False
