"""Tests for logslice.cluster."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.cluster import (
    Cluster,
    cluster_entries,
    message_signature,
)


def make_entry(
    message: str = "hello",
    severity: str = "INFO",
    ts: Optional[datetime] = None,
) -> LogEntry:
    return LogEntry(
        timestamp=ts or datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=message,
    )


# ---------------------------------------------------------------------------
# message_signature
# ---------------------------------------------------------------------------

class TestMessageSignature:
    def test_replaces_integer(self):
        assert message_signature("retry 3 times") == "retry <VAR> times"

    def test_replaces_ip_address(self):
        assert message_signature("connect to 192.168.1.1") == "connect to <VAR>"

    def test_replaces_uuid(self):
        sig = message_signature("job 550e8400-e29b-41d4-a716-446655440000 done")
        assert "<VAR>" in sig
        assert "550e8400" not in sig

    def test_replaces_hex(self):
        assert message_signature("addr 0xFF done") == "addr <VAR> done"

    def test_plain_text_unchanged(self):
        assert message_signature("disk full") == "disk full"

    def test_collapses_whitespace(self):
        assert message_signature("a   b") == "a b"

    def test_empty_string(self):
        assert message_signature("") == ""


# ---------------------------------------------------------------------------
# cluster_entries
# ---------------------------------------------------------------------------

class TestClusterEntries:
    def test_returns_list(self):
        result = cluster_entries([])
        assert isinstance(result, list)

    def test_empty_entries_returns_empty(self):
        assert cluster_entries([]) == []

    def test_single_cluster(self):
        entries = [make_entry("disk full") for _ in range(5)]
        clusters = cluster_entries(entries)
        assert len(clusters) == 1
        assert clusters[0].count == 5

    def test_two_distinct_clusters(self):
        e1 = [make_entry("disk full") for _ in range(3)]
        e2 = [make_entry("connection refused") for _ in range(2)]
        clusters = cluster_entries(e1 + e2)
        assert len(clusters) == 2

    def test_sorted_by_count_descending(self):
        e1 = [make_entry("disk full") for _ in range(2)]
        e2 = [make_entry("timeout after 30 seconds") for _ in range(5)]
        clusters = cluster_entries(e1 + e2)
        assert clusters[0].count >= clusters[1].count

    def test_variable_tokens_merge_into_one_cluster(self):
        entries = [
            make_entry("retry 1 times"),
            make_entry("retry 2 times"),
            make_entry("retry 99 times"),
        ]
        clusters = cluster_entries(entries)
        assert len(clusters) == 1
        assert clusters[0].count == 3

    def test_min_count_filters_small_clusters(self):
        e1 = [make_entry("disk full") for _ in range(1)]
        e2 = [make_entry("timeout after 5 seconds") for _ in range(3)]
        clusters = cluster_entries(e1 + e2, min_count=2)
        assert all(c.count >= 2 for c in clusters)

    def test_top_n_limits_results(self):
        entries = (
            [make_entry("a") for _ in range(5)]
            + [make_entry("b") for _ in range(3)]
            + [make_entry("c") for _ in range(1)]
        )
        clusters = cluster_entries(entries, top_n=2)
        assert len(clusters) == 2

    def test_top_n_zero_returns_empty(self):
        entries = [make_entry("disk full") for _ in range(3)]
        assert cluster_entries(entries, top_n=0) == []


# ---------------------------------------------------------------------------
# Cluster dataclass
# ---------------------------------------------------------------------------

class TestCluster:
    def test_count_reflects_entries(self):
        c = Cluster(signature="disk full")
        c.entries = [make_entry() for _ in range(4)]
        assert c.count == 4

    def test_severities_counts(self):
        c = Cluster(signature="disk full")
        c.entries = [
            make_entry(severity="ERROR"),
            make_entry(severity="ERROR"),
            make_entry(severity="WARN"),
        ]
        assert c.severities["ERROR"] == 2
        assert c.severities["WARN"] == 1

    def test_as_dict_keys(self):
        c = Cluster(signature="test")
        d = c.as_dict()
        assert "signature" in d
        assert "count" in d
        assert "severities" in d

    def test_as_dict_count_matches(self):
        c = Cluster(signature="test")
        c.entries = [make_entry() for _ in range(7)]
        assert c.as_dict()["count"] == 7
