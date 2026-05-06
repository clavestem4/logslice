# logslice.watch

Real-time log file watching with optional severity and time-range filtering.

## Overview

`watch.py` polls a log file for newly appended lines and yields parsed
`LogEntry` objects as they arrive.  It is designed for long-running processes
such as dashboards, alerting pipelines, or live tailing with filtering.

## Functions

### `watch_file(path, *, min_severity, start, end, poll_interval, max_iterations)`

Yields `LogEntry` objects for every new line appended to `path`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `path` | `str \| Path` | — | Path to the log file |
| `min_severity` | `str \| None` | `None` | Minimum severity level to include |
| `start` | `datetime \| None` | `None` | Ignore entries before this time |
| `end` | `datetime \| None` | `None` | Ignore entries after this time |
| `poll_interval` | `float` | `0.5` | Seconds between file polls |
| `max_iterations` | `int \| None` | `None` | Stop after N poll cycles (testing) |

If the file is truncated or rotated the watcher resets to the beginning
automatically.

### `watch_callback(path, callback, *, min_severity, poll_interval, max_iterations)`

Convenience wrapper that calls `callback(entry)` for every new entry.
Returns the total number of entries processed.

## Example

```python
from logslice.watch import watch_file

for entry in watch_file("/var/log/app.log", min_severity="WARNING"):
    print(entry)
```

```python
from logslice.watch import watch_callback

def alert(entry):
    if entry.severity == "ERROR":
        send_alert(entry.message)

watch_callback("/var/log/app.log", alert, min_severity="ERROR")
```

## Notes

- Uses simple polling; for inotify-based watching consider `watchdog`.
- `max_iterations` is intended for unit tests and scripts with a finite run.
- Entries that cannot be parsed are silently skipped.
