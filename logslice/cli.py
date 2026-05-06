"""Command-line interface for logslice."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import Sequence

from logslice.dedupe import deduplicate
from logslice.formatter import render
from logslice.slice import slice_file


def parse_dt(value: str) -> datetime:
    """Parse a datetime string from the CLI (ISO-8601, with or without T)."""
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Cannot parse datetime: {value!r}. "
        "Expected ISO-8601 format, e.g. '2024-01-15T08:30:00'."
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Extract and filter structured log entries by time range and severity.",
    )
    p.add_argument("file", help="Path to the log file.")
    p.add_argument("--start", type=parse_dt, metavar="DATETIME", help="Include entries at or after this time.")
    p.add_argument("--end", type=parse_dt, metavar="DATETIME", help="Include entries before or at this time.")
    p.add_argument("--level", metavar="SEVERITY", help="Minimum severity level (e.g. WARNING).")
    p.add_argument(
        "--format",
        choices=("text", "json", "csv"),
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--dedupe", "-D",
        action="store_true",
        default=False,
        help="Remove duplicate log entries (same severity + message).",
    )
    p.add_argument(
        "--keep",
        choices=("first", "last"),
        default="first",
        help="Which duplicate occurrence to keep when --dedupe is active (default: first).",
    )
    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        entries = slice_file(
            args.file,
            start=args.start,
            end=args.end,
            min_severity=args.level,
        )
    except OSError as exc:
        print(f"logslice: error: {exc}", file=sys.stderr)
        return 1

    if args.dedupe:
        entries = list(deduplicate(entries, keep=args.keep))

    output = render(entries, fmt=args.fmt)
    print(output, end="" if output.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
