"""Tests for logslice.stats."""

from datetime import datetime, timedelta, timezone

import pytest

from logslice.parser import LogEntry
from logslice.stats import BucketStats, bucket_key, compute_stats


def make_entry(ts: datetime | None, severity: str = "INFO") -> LogEntry:
    return LogEntry(timestamp=ts, severity=severity, message="msg", raw=f"{severity} msg")


UTC = timezone.utc


class TestBucketKey:
    def test_aligns_to_minute(self):
        ts = datetime(2024, 3, 15, 12, 7, 45, tzinfo=UTC)
        key = bucket_key(ts, timedelta(minutes=1))
        assert key == datetime(2024, 3, 15, 12, 7, 0, tzinfo=UTC)

    def test_aligns_to_five_minutes(self):
        ts = datetime(2024, 3, 15, 12, 7, 45, tzinfo=UTC)
        key = bucket_key(ts, timedelta(minutes=5))
        assert key == datetime(2024, 3, 15, 12, 5, 0, tzinfo=UTC)

    def test_exact_boundary_unchanged(self):
        ts = datetime(2024, 3, 15, 12, 5, 0, tzinfo=UTC)
        key = bucket_key(ts, timedelta(minutes=5))
        assert key == ts


class TestComputeStats:
    def test_empty_list(self):
        result = compute_stats([])
        assert result == []

    def test_skips_none_timestamps(self):
        entries = [make_entry(None), make_entry(None)]
        result = compute_stats(entries)
        assert result == []

    def test_single_bucket(self):
        ts = datetime(2024, 1, 1, 0, 0, 30, tzinfo=UTC)
        entries = [make_entry(ts, "INFO"), make_entry(ts, "ERROR")]
        result = compute_stats(entries, timedelta(minutes=1))
        assert len(result) == 1
        assert result[0].total == 2
        assert result[0].severity_counts == {"INFO": 1, "ERROR": 1}

    def test_multiple_buckets(self):
        e1 = make_entry(datetime(2024, 1, 1, 0, 0, 10, tzinfo=UTC), "DEBUG")
        e2 = make_entry(datetime(2024, 1, 1, 0, 1, 10, tzinfo=UTC), "WARN")
        e3 = make_entry(datetime(2024, 1, 1, 0, 2, 10, tzinfo=UTC), "ERROR")
        result = compute_stats([e1, e2, e3], timedelta(minutes=1))
        assert len(result) == 3
        assert result[0].severity_counts == {"DEBUG": 1}
        assert result[1].severity_counts == {"WARN": 1}
        assert result[2].severity_counts == {"ERROR": 1}

    def test_result_is_sorted(self):
        e1 = make_entry(datetime(2024, 1, 1, 0, 5, 0, tzinfo=UTC))
        e2 = make_entry(datetime(2024, 1, 1, 0, 1, 0, tzinfo=UTC))
        result = compute_stats([e1, e2], timedelta(minutes=1))
        assert result[0].bucket_start < result[1].bucket_start

    def test_severity_normalised_to_upper(self):
        ts = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        entries = [make_entry(ts, "info"), make_entry(ts, "Info")]
        result = compute_stats(entries)
        assert result[0].severity_counts == {"INFO": 2}

    def test_unknown_severity_label(self):
        ts = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        entry = LogEntry(timestamp=ts, severity=None, message="msg", raw="msg")
        result = compute_stats([entry])
        assert result[0].severity_counts == {"UNKNOWN": 1}


class TestBucketStatsAsDict:
    def test_as_dict_keys(self):
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=UTC)
        bs = BucketStats(bucket_start=ts, total=3, severity_counts={"INFO": 3})
        d = bs.as_dict()
        assert set(d.keys()) == {"bucket_start", "total", "severity_counts"}

    def test_str_contains_total(self):
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=UTC)
        bs = BucketStats(bucket_start=ts, total=5, severity_counts={"ERROR": 5})
        assert "total=5" in str(bs)
