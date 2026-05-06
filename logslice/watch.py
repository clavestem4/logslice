"""Watch a log file for new entries matching optional filters."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Iterator, Optional

from logslice.parser import LogEntry, parse_line
from logslice.filter import apply_filters


def _read_new_lines(fp, last_pos: int) -> tuple[list[str], int]:
    """Read any new lines added since last_pos; return lines and new position."""
    fp.seek(0, 2)  # seek to end to get file size
    end = fp.tell()
    if end < last_pos:
        # File was rotated/truncated
        last_pos = 0
    fp.seek(last_pos)
    lines = fp.readlines()
    new_pos = fp.tell()
    return [l.rstrip("\n") for l in lines], new_pos


def watch_file(
    path: str | Path,
    *,
    min_severity: Optional[str] = None,
    start: Optional[object] = None,
    end: Optional[object] = None,
    poll_interval: float = 0.5,
    max_iterations: Optional[int] = None,
) -> Iterator[LogEntry]:
    """Yield new LogEntry objects as they are appended to *path*.

    Polls the file every *poll_interval* seconds.  Stops after
    *max_iterations* poll cycles when set (useful for testing).
    """
    path = Path(path)
    last_pos = 0
    iterations = 0

    with path.open("r", encoding="utf-8", errors="replace") as fp:
        # Start at the end of the existing file
        fp.seek(0, 2)
        last_pos = fp.tell()

        while True:
            lines, last_pos = _read_new_lines(fp, last_pos)
            entries = [e for line in lines if (e := parse_line(line)) is not None]
            filtered = apply_filters(
                entries,
                min_severity=min_severity,
                start=start,
                end=end,
            )
            for entry in filtered:
                yield entry

            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                break
            time.sleep(poll_interval)


def watch_callback(
    path: str | Path,
    callback: Callable[[LogEntry], None],
    *,
    min_severity: Optional[str] = None,
    poll_interval: float = 0.5,
    max_iterations: Optional[int] = None,
) -> int:
    """Call *callback* for every new entry; return total entries processed."""
    count = 0
    for entry in watch_file(
        path,
        min_severity=min_severity,
        poll_interval=poll_interval,
        max_iterations=max_iterations,
    ):
        callback(entry)
        count += 1
    return count
