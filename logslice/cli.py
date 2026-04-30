"""Command-line interface for logslice."""

import argparse
import sys
from datetime import datetime
from typing import Optional

from logslice.slice import slice_file
from logslice.formatter import render, SUPPORTED_FORMATS


def parse_dt(value: str) -> datetime:
    """Parse an ISO-8601 datetime string from the CLI."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Cannot parse datetime {value!r}. Use YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD."
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Extract and filter structured log entries by time range and severity.",
    )
    p.add_argument("file", help="Path to the log file to parse.")
    p.add_argument(
        "--start", metavar="DATETIME", type=parse_dt, default=None,
        help="Include entries at or after this timestamp (ISO-8601).",
    )
    p.add_argument(
        "--end", metavar="DATETIME", type=parse_dt, default=None,
        help="Include entries before or at this timestamp (ISO-8601).",
    )
    p.add_argument(
        "--min-severity", metavar="LEVEL", default=None,
        help="Minimum severity level (e.g. WARNING, ERROR).",
    )
    p.add_argument(
        "--format", dest="fmt", choices=SUPPORTED_FORMATS, default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--raw", action="store_true",
        help="When using text format, emit original raw log lines.",
    )
    return p


def main(argv=None) -> int:
    """Entry point for the logslice CLI.

    Returns:
        Exit code (0 = success, 1 = error).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        entries = slice_file(
            args.file,
            start=args.start,
            end=args.end,
            min_severity=args.min_severity,
        )
    except FileNotFoundError:
        print(f"logslice: file not found: {args.file}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"logslice: error reading file: {exc}", file=sys.stderr)
        return 1

    output = render(entries, fmt=args.fmt, show_raw=args.raw)
    if output:
        print(output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
