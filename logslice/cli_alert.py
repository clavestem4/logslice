"""CLI helpers for the alert subcommand."""

from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.alert import AlertRule, process_entries
from logslice.slice import slice_file
from logslice.formatter import render


def _make_printing_callback(fmt: str, out):
    """Return a callback that prints the triggering entry."""

    def _cb(entry, rule):
        line = render([entry], fmt=fmt)
        out.write(f"[ALERT:{rule.name}] {line}\n")

    return _cb


def add_alert_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("file", help="Log file to scan")
    parser.add_argument(
        "--min-severity",
        dest="min_severity",
        default=None,
        help="Minimum severity level to alert on (e.g. WARN, ERROR)",
    )
    parser.add_argument(
        "--pattern",
        default=None,
        help="Regex pattern that must appear in the message",
    )
    parser.add_argument(
        "--rule-name",
        dest="rule_name",
        default="cli-rule",
        help="Name to assign to the alert rule",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        default="text",
        choices=["text", "json", "csv"],
        help="Output format for matched entries",
    )
    parser.add_argument(
        "--count-only",
        dest="count_only",
        action="store_true",
        help="Print only the total number of alerts fired",
    )


def run_alert(
    args: argparse.Namespace,
    out=sys.stdout,
) -> int:
    """Run alert scan. Returns total number of alerts fired."""
    entries = slice_file(args.file)
    fired_lines: List[str] = []

    def _cb(entry, rule):
        line = render([entry], fmt=args.fmt).strip()
        fired_lines.append(f"[ALERT:{rule.name}] {line}")

    rule = AlertRule(
        name=args.rule_name,
        callback=_cb,
        min_severity=args.min_severity,
        pattern=args.pattern,
    )

    total = process_entries(entries, [rule])

    if args.count_only:
        out.write(f"{total}\n")
    else:
        for line in fired_lines:
            out.write(line + "\n")

    return total
