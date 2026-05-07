# Rate Limiting

The `logslice.rate` module provides utilities for throttling log entry streams
and measuring entry throughput over time.

## RateWindow

A sliding-window counter that tracks how many entries have been seen within a
given number of seconds.

```python
from logslice.rate import RateWindow

window = RateWindow(window_seconds=60, max_entries=100)
for entry in entries:
    if window.allow(entry):
        process(entry)
    else:
        print("Rate limit exceeded, dropping entry")
```

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `window_seconds` | `int` | Length of the sliding window in seconds |
| `max_entries` | `int` | Maximum entries allowed within the window |
| `current_count` | `int` | Number of entries currently tracked in the window |

## throttle_entries

Filter an iterable of `LogEntry` objects, yielding only those that fall within
the allowed rate.

```python
from logslice.rate import throttle_entries

allowed = list(throttle_entries(entries, window_seconds=60, max_entries=50))
```

## rate_exceeded

Return the entries that were **dropped** because they exceeded the rate limit.
Useful for auditing or alerting on burst activity.

```python
from logslice.rate import rate_exceeded

dropped = rate_exceeded(entries, window_seconds=60, max_entries=50)
print(f"{len(dropped)} entries were rate-limited")
```

## compute_rate

Estimate the average entries-per-second across a list of entries.

```python
from logslice.rate import compute_rate

rate = compute_rate(entries)
if rate is not None:
    print(f"Average rate: {rate:.2f} entries/sec")
```

Returns `None` if fewer than two timestamped entries are provided or if all
entries share the same timestamp.
