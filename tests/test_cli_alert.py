"""Tests for logslice.cli_alert."""

from __future__ import annotations

import argparse
import io
import os
import tempfile
from datetime import datetime

import pytest

from logslice.cli_alert import add_alert_arguments, run_alert


LOG_LINES = [
    "2024-01-01T10:00:00 INFO  startup complete\n",
    "2024-01-01T10:01:00 WARN  disk usage high\n",
    "2024-01-01T10:02:00 ERROR disk full\n",
    "2024-01-01T10:03:00 ERROR connection timeout\n",
    "2024-01-01T10:04:00 DEBUG heartbeat\n",
]


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("".join(LOG_LINES))
    return str(p)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        min_severity=None,
        pattern=None,
        rule_name="test-rule",
        fmt="text",
        count_only=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestRunAlert:
    def test_returns_alert_count(self, log_file):
        args = _make_args(file=log_file, min_severity="ERROR")
        total = run_alert(args, out=io.StringIO())
        assert total == 2

    def test_output_contains_alert_tag(self, log_file):
        out = io.StringIO()
        args = _make_args(file=log_file, min_severity="ERROR")
        run_alert(args, out=out)
        text = out.getvalue()
        assert "[ALERT:test-rule]" in text

    def test_count_only_prints_number(self, log_file):
        out = io.StringIO()
        args = _make_args(file=log_file, min_severity="WARN", count_only=True)
        total = run_alert(args, out=out)
        assert out.getvalue().strip() == str(total)

    def test_pattern_filter(self, log_file):
        out = io.StringIO()
        args = _make_args(file=log_file, pattern=r"disk")
        total = run_alert(args, out=out)
        assert total == 2
        assert "disk" in out.getvalue().lower()

    def test_no_match_returns_zero(self, log_file):
        out = io.StringIO()
        args = _make_args(file=log_file, pattern=r"xyzzy_not_found")
        total = run_alert(args, out=out)
        assert total == 0
        assert out.getvalue() == ""

    def test_combined_severity_and_pattern(self, log_file):
        out = io.StringIO()
        args = _make_args(file=log_file, min_severity="ERROR", pattern=r"timeout")
        total = run_alert(args, out=out)
        assert total == 1

    def test_no_conditions_matches_all(self, log_file):
        args = _make_args(file=log_file)
        total = run_alert(args, out=io.StringIO())
        assert total == len(LOG_LINES)

    def test_rule_name_in_output(self, log_file):
        out = io.StringIO()
        args = _make_args(file=log_file, min_severity="ERROR", rule_name="my-rule")
        run_alert(args, out=out)
        assert "[ALERT:my-rule]" in out.getvalue()


class TestAddAlertArguments:
    def test_adds_file_argument(self):
        parser = argparse.ArgumentParser()
        add_alert_arguments(parser)
        args = parser.parse_args(["app.log"])
        assert args.file == "app.log"

    def test_defaults(self):
        parser = argparse.ArgumentParser()
        add_alert_arguments(parser)
        args = parser.parse_args(["app.log"])
        assert args.min_severity is None
        assert args.pattern is None
        assert args.rule_name == "cli-rule"
        assert args.fmt == "text"
        assert args.count_only is False
