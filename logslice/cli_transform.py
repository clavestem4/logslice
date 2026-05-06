"""CLI subcommand for applying transformations to log files."""

import argparse
import sys
from typing import List

from logslice.slice import slice_file
from logslice.transform import (
    apply_transform,
    normalize_severity,
    redact_message,
    truncate_message,
)
from logslice.formatter import render


def add_transform_arguments(parser: argparse.ArgumentParser) -> None:
    """Register transform subcommand arguments onto parser."""
    parser.add_argument("file", help="Path to the log file")
    parser.add_argument(
        "--normalize-severity",
        action="store_true",
        default=False,
        help="Uppercase and strip severity field",
    )
    parser.add_argument(
        "--redact",
        metavar="PATTERN",
        help="Regex pattern to redact from messages",
    )
    parser.add_argument(
        "--redact-with",
        metavar="REPLACEMENT",
        default="[REDACTED]",
        help="Replacement string for redacted content (default: [REDACTED])",
    )
    parser.add_argument(
        "--truncate",
        metavar="N",
        type=int,
        help="Truncate messages to N characters",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text)",
    )


def run_transform(args: argparse.Namespace, out=None) -> int:
    """Execute transform subcommand; returns number of entries written."""
    if out is None:
        out = sys.stdout

    entries = slice_file(args.file)

    if args.normalize_severity:
        entries = apply_transform(entries, normalize_severity)

    if args.redact:
        entries = apply_transform(
            entries,
            lambda e: redact_message(e, args.redact, args.redact_with),
        )

    if args.truncate is not None:
        if args.truncate < 0:
            print("error: --truncate value must be non-negative", file=sys.stderr)
            return 0
        entries = apply_transform(
            entries,
            lambda e: truncate_message(e, args.truncate),
        )

    output = render(entries, fmt=args.format)
    out.write(output)
    if output and not output.endswith("\n"):
        out.write("\n")

    return len(entries)
