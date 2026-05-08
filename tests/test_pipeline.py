"""Tests for logslice.pipeline."""

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.pipeline import Pipeline, build_pipeline, run_pipeline


def make_entry(msg: str, severity: str = "INFO", ts: datetime | None = None) -> LogEntry:
    return LogEntry(
        timestamp=ts or datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=msg,
        raw=f"{severity} {msg}",
    )


# ---------------------------------------------------------------------------
# Pipeline construction
# ---------------------------------------------------------------------------

class TestPipelineConstruction:
    def test_empty_pipeline_has_no_steps(self):
        p = Pipeline()
        assert len(p) == 0

    def test_add_step_increases_length(self):
        p = Pipeline()
        p.add_step(lambda e: e)
        assert len(p) == 1

    def test_add_step_returns_self(self):
        p = Pipeline()
        result = p.add_step(lambda e: e)
        assert result is p

    def test_build_pipeline_sets_steps(self):
        fn1 = lambda e: e
        fn2 = lambda e: e
        p = build_pipeline(fn1, fn2, name="test")
        assert len(p) == 2
        assert p.name == "test"


# ---------------------------------------------------------------------------
# Pipeline.run
# ---------------------------------------------------------------------------

class TestPipelineRun:
    def test_empty_pipeline_returns_all_entries(self):
        entries = [make_entry("a"), make_entry("b")]
        p = Pipeline()
        assert p.run(entries) == entries

    def test_single_filter_step(self):
        entries = [make_entry("keep"), make_entry("drop")]
        keep_step = lambda e: [x for x in e if x.message == "keep"]
        p = build_pipeline(keep_step)
        result = p.run(entries)
        assert len(result) == 1
        assert result[0].message == "keep"

    def test_steps_applied_in_order(self):
        entries = [make_entry("x", "DEBUG"), make_entry("y", "ERROR"), make_entry("z", "INFO")]
        step1 = lambda e: [x for x in e if x.severity != "DEBUG"]
        step2 = lambda e: [x for x in e if x.severity != "INFO"]
        p = build_pipeline(step1, step2)
        result = p.run(entries)
        assert len(result) == 1
        assert result[0].severity == "ERROR"

    def test_transform_step_modifies_entries(self):
        from dataclasses import replace
        entries = [make_entry("hello")]
        upper_step = lambda e: [replace(x, message=x.message.upper()) for x in e]
        result = build_pipeline(upper_step).run(entries)
        assert result[0].message == "HELLO"

    def test_run_accepts_generator(self):
        def gen():
            yield make_entry("a")
            yield make_entry("b")
        p = Pipeline()
        result = p.run(gen())
        assert len(result) == 2

    def test_empty_input_returns_empty(self):
        p = build_pipeline(lambda e: e)
        assert p.run([]) == []


# ---------------------------------------------------------------------------
# run_pipeline helper
# ---------------------------------------------------------------------------

class TestRunPipeline:
    def test_no_steps_passthrough(self):
        entries = [make_entry("a")]
        assert run_pipeline(entries) == entries

    def test_applies_steps(self):
        entries = [make_entry("a"), make_entry("b")]
        result = run_pipeline(entries, lambda e: e[:1])
        assert len(result) == 1

    def test_multiple_steps(self):
        entries = [make_entry("a", "INFO"), make_entry("b", "DEBUG"), make_entry("c", "ERROR")]
        result = run_pipeline(
            entries,
            lambda e: [x for x in e if x.severity != "DEBUG"],
            lambda e: [x for x in e if x.severity != "INFO"],
        )
        assert len(result) == 1
        assert result[0].message == "c"
