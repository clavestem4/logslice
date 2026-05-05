"""Command-line interface for logslice."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import Optional

from logslice.formatter import render
from logslice.slice import slice_file
from logslice.summary import summarize


def parse_dt(value: str) -> datetime:
    """Parse an ISO-8601-ish datetime string from the CLI."""
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
    raise argparse.ArgumentTypeError(f"Cannot parse datetime: {value!r}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Extract and filter structured log entries by time range and severity.",
    )
    p.add_argument("file", help="Path to the log file")
    p.add_argument("--from", dest="start", type=parse_dt, metavar="DATETIME",
                   help="Include entries at or after this timestamp")
    p.add_argument("--to", dest="end", type=parse_dt, metavar="DATETIME",
                   help="Include entries at or before this timestamp")
    p.add_argument("--severity", "-s", metavar="LEVEL",
                   help="Minimum severity level (e.g. WARNING)")
    p.add_argument("--format", "-f", dest="fmt",
                   choices=["text", "json", "csv"], default="text",
                   help="Output format (default: text)")
    p.add_argument("--summary", action="store_true",
                   help="Print a summary instead of individual entries")
    p.add_argument("--show-raw", action="store_true",
                   help="Include the raw log line in text output")
    return p


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        entries = slice_file(
            args.file,
            start=args.start,
            end=args.end,
            min_severity=args.severity,
        )
    except FileNotFoundError:
        print(f"logslice: file not found: {args.file}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"logslice: {exc}", file=sys.stderr)
        return 1

    if args.summary:
        print(summarize(entries))
        return 0

    output = render(entries, fmt=args.fmt, show_raw=args.show_raw)
    if output:
        print(output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
