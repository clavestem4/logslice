# Window

The `logslice.window` module provides time-based **sliding** and **tumbling** window aggregation over `LogEntry` streams.

## Classes

### `WindowResult`

A snapshot produced when a window closes.

| Attribute | Type | Description |
|---|---|---|
| `window_start` | `datetime` | Inclusive start of the window |
| `window_end` | `datetime` | Exclusive end of the window |
| `entries` | `List[LogEntry]` | Entries captured in the window |
| `count` | `int` | Number of entries (property) |

```python
result.as_dict()   # serialisable dict
str(result)        # human-readable summary
```

### `SlidingWindow`

Accumulates entries in a rolling time window. Old entries are evicted automatically when a newer entry is pushed.

```python
from datetime import timedelta
from logslice.window import SlidingWindow

sw = SlidingWindow(duration=timedelta(minutes=5))
for entry in entries:
    sw.push(entry)
    print(f"Window size: {len(sw)}")
```

Entries without a `timestamp` are silently ignored.

## Functions

### `tumbling_windows(entries, duration, on_window=None)`

Partitions a list of entries into consecutive, non-overlapping windows of the given `duration`.

```python
from datetime import timedelta
from logslice.window import tumbling_windows

for window in tumbling_windows(entries, timedelta(minutes=1)):
    print(window.window_start, window.count)
```

An optional `on_window` callback is invoked for each `WindowResult` as it is produced:

```python
def alert(result):
    if result.count > 100:
        print(f"Spike detected: {result.count} entries in {result.window_start}")

list(tumbling_windows(entries, timedelta(minutes=1), on_window=alert))
```

## Notes

- Only entries with a non-`None` `timestamp` participate in windowing.
- `SlidingWindow` is stateful and designed for streaming use; `tumbling_windows` operates on an in-memory list.
