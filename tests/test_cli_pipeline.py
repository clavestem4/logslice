"""Tests for logslice.cli_pipeline."""

import argparse
import io
import os
import tempfile
from datetime import datetime

import pytest

from logslice.cli_pipeline import add_pipeline_arguments, run_pipeline_cli


_LOG_LINES = """\
2024-01-01T10:00:00 INFO  startup complete
2024-01-01T10:01:00 DEBUG heartbeat
2024-01-01T10:02:00 ERROR disk full
2024-01-01T10:03:00 ERROR disk full
2024-01-01T10:04:00 WARNING high memory
""".strip()


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "app.log"
    p.write_text(_LOG_LINES + "\n")
    return str(p)


def _make_args(log_file, **kwargs):
    parser = argparse.ArgumentParser()
    add_pipeline_arguments(parser)
    base = {
        "file": log_file,
        "min_severity": None,
        "start": None,
        "end": None,
        "fmt": "text",
        "steps": [],
    }
    base.update(kwargs)
    return argparse.Namespace(**base)


class TestRunPipelineCli:
    def test_returns_entry_count(self, log_file):
        args = _make_args(log_file)
        count = run_pipeline_cli(args, out=io.StringIO())
        assert count == 5

    def test_output_contains_messages(self, log_file):
        args = _make_args(log_file)
        buf = io.StringIO()
        run_pipeline_cli(args, out=buf)
        output = buf.getvalue()
        assert "startup complete" in output
        assert "disk full" in output

    def test_min_severity_filters(self, log_file):
        args = _make_args(log_file, min_severity="WARNING")
        count = run_pipeline_cli(args, out=io.StringIO())
        assert count == 3  # WARNING + 2× ERROR

    def test_errors_only_step(self, log_file):
        args = _make_args(log_file, steps=["errors-only"])
        buf = io.StringIO()
        count = run_pipeline_cli(args, out=buf)
        assert count == 2
        assert "disk full" in buf.getvalue()

    def test_dedup_step_removes_duplicates(self, log_file):
        args = _make_args(log_file, steps=["errors-only", "dedup"])
        count = run_pipeline_cli(args, out=io.StringIO())
        assert count == 1

    def test_unknown_step_raises(self, log_file):
        from logslice.cli_pipeline import _resolve_named_step
        with pytest.raises(ValueError, match="Unknown pipeline step"):
            _resolve_named_step("nonexistent")

    def test_json_format(self, log_file):
        args = _make_args(log_file, fmt="json")
        buf = io.StringIO()
        run_pipeline_cli(args, out=buf)
        import json
        data = json.loads(buf.getvalue())
        assert isinstance(data, list)
        assert len(data) == 5

    def test_time_filter_applied(self, log_file):
        args = _make_args(log_file, start="2024-01-01T10:02:00", end="2024-01-01T10:03:00")
        count = run_pipeline_cli(args, out=io.StringIO())
        assert count == 2

    def test_add_pipeline_arguments_registers_file(self):
        parser = argparse.ArgumentParser()
        add_pipeline_arguments(parser)
        ns = parser.parse_args(["somefile.log"])
        assert ns.file == "somefile.log"
