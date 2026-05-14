"""Tests for logslice.cli_classify."""

from __future__ import annotations

import argparse
import io
import json
import textwrap
from pathlib import Path

import pytest

from logslice.cli_classify import add_classify_arguments, run_classify, _parse_rules
from logslice.classify import ClassifyRule


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        2024-01-01T10:00:00 INFO  service started
        2024-01-01T10:01:00 ERROR database connection failed
        2024-01-01T10:02:00 WARNING disk usage high
        2024-01-01T10:03:00 ERROR network timeout
        2024-01-01T10:04:00 DEBUG heartbeat ok
    """)
    p = tmp_path / "app.log"
    p.write_text(content)
    return p


def _make_args(log_file, rules=None, summary=False, as_json=False, min_severity=None):
    ns = argparse.Namespace(
        file=str(log_file),
        rules=rules or [],
        summary=summary,
        as_json=as_json,
        min_severity=min_severity,
    )
    return ns


class TestParseRules:
    def test_single_rule(self):
        rules = _parse_rules(["db:database"])
        assert len(rules) == 1
        assert rules[0].category == "db"
        assert rules[0].pattern == "database"

    def test_multiple_rules(self):
        rules = _parse_rules(["db:database", "net:network"])
        assert len(rules) == 2

    def test_invalid_rule_raises(self):
        with pytest.raises(ValueError):
            _parse_rules(["nodivider"])

    def test_empty_returns_empty(self):
        assert _parse_rules([]) == []


class TestRunClassify:
    def test_returns_entry_count(self, log_file):
        out = io.StringIO()
        count = run_classify(_make_args(log_file), out=out)
        assert count == 5

    def test_output_contains_category_tag(self, log_file):
        out = io.StringIO()
        run_classify(_make_args(log_file, rules=["db:database"]), out=out)
        assert "[db]" in out.getvalue()

    def test_unclassified_entries_present(self, log_file):
        out = io.StringIO()
        run_classify(_make_args(log_file, rules=["db:database"]), out=out)
        assert "[unclassified]" in out.getvalue()

    def test_summary_mode_shows_counts(self, log_file):
        out = io.StringIO()
        run_classify(
            _make_args(log_file, rules=["db:database"], summary=True), out=out
        )
        text = out.getvalue()
        assert "db:" in text
        assert "unclassified:" in text

    def test_json_mode_outputs_valid_json(self, log_file):
        out = io.StringIO()
        run_classify(
            _make_args(log_file, rules=["db:database"], as_json=True), out=out
        )
        data = json.loads(out.getvalue())
        assert isinstance(data, dict)
        assert "db" in data

    def test_min_severity_filters_entries(self, log_file):
        out = io.StringIO()
        count = run_classify(
            _make_args(log_file, min_severity="ERROR"), out=out
        )
        # Only ERROR entries should pass (2 in fixture)
        assert count == 2

    def test_no_rules_all_unclassified(self, log_file):
        out = io.StringIO()
        run_classify(_make_args(log_file, summary=True), out=out)
        text = out.getvalue()
        assert "unclassified:" in text
        assert "db:" not in text
