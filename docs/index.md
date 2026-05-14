# logslice.index — Offset-Based Log Index

The `index` module builds an in-memory (and optionally persisted) offset index
over a log file so that time-range queries can **seek directly** to the right
byte position instead of scanning from the start.

## Core types

### `IndexEntry`

Holds one sampled position in the file:

| Field | Type | Description |
|---|---|---|
| `offset` | `int` | Byte offset in the file (`fh.tell()`) |
| `timestamp` | `datetime` | Parsed timestamp of the sampled line |
| `line_number` | `int` | Zero-based line number |

### `LogIndex`

Container for all sampled entries for a single source file.

```python
from logslice.index import LogIndex, IndexEntry
idx = LogIndex(source="app.log")
print(len(idx))   # 0
```

## Building an index

```python
from logslice.index import build_index

idx = build_index("app.log", step=200)
print(idx)  # LogIndex(source='app.log', entries=512)
```

`step` controls how often a line is sampled (every *N* lines).  Smaller values
give finer granularity at the cost of memory; larger values are faster to build.

## Seeking to a timestamp

```python
from datetime import datetime
from logslice.index import seek_to_time

target = datetime(2024, 6, 1, 12, 0, 0)
offset = seek_to_time(idx, target)
if offset is not None:
    with open("app.log") as fh:
        fh.seek(offset)
        # read from here
```

`seek_to_time` returns the byte offset of the **last** indexed entry whose
timestamp is ≤ `target`, or `None` if the target is before all entries.

## Persisting an index

Indexes can be saved to a JSON file and reloaded, avoiding the cost of
rebuilding on every run:

```python
from logslice.index import save_index, load_index

save_index(idx, ".logslice/app.idx")
idx2 = load_index(".logslice/app.idx")
```

## Notes

- Lines without a parseable timestamp are silently skipped during indexing.
- The index does **not** auto-update when the file grows; rebuild or combine
  with `logslice.checkpoint` to track progress.
