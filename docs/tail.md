# `logslice.tail` — Tail & Follow Log Files

The `tail` module lets you inspect the **most recent entries** in a log file
and optionally **follow** it in real time as new lines are appended.

---

## Functions

### `tail_entries(lines, n=20) -> List[LogEntry]`

Parse an in-memory list of raw log strings and return the last `n` entries.

```python
from logslice.tail import tail_entries

with open("app.log") as fh:
    entries = tail_entries(fh.readlines(), n=50)
```

### `tail_file(path, n=20) -> List[LogEntry]`

Convenience wrapper that opens `path` and returns the last `n` entries.

```python
from logslice.tail import tail_file

for entry in tail_file("/var/log/app.log", n=10):
    print(entry)
```

### `follow_file(path, callback, poll_interval=0.25, stop_after=None)`

Watch `path` for new lines.  For every new parseable line, `callback` is
called with the resulting `LogEntry`.  Blocks until `stop_after` seconds
elapse or `KeyboardInterrupt` is raised.

```python
from logslice.tail import follow_file

follow_file("/var/log/app.log", callback=print)
```

### `iter_tail(path, n=20, follow=False, poll_interval=0.25) -> Iterator[LogEntry]`

Yield the last `n` entries then, if `follow=True`, continue yielding new
entries as they appear.

```python
from logslice.tail import iter_tail

for entry in iter_tail("/var/log/app.log", n=5, follow=True):
    print(entry.severity, entry.message)
```

---

## CLI integration

The `--tail` flag (added to `logslice.cli`) exposes this functionality:

```
logslice --tail 20 app.log
logslice --tail 20 --follow app.log
```

---

## Notes

- Lines that cannot be parsed (no recognisable timestamp / severity) are
  silently skipped.
- `follow_file` uses polling (`time.sleep`) rather than `inotify` so it
  works on all platforms.
