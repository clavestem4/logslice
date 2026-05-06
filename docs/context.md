# Context Window Extraction

The `logslice.context` module lets you retrieve surrounding log entries
around a match — analogous to `grep -A` (after), `-B` (before), and
`-C` (context).

## Data Model

```python
@dataclass
class ContextWindow:
    entry: LogEntry        # the matched entry
    before: List[LogEntry] # entries immediately before
    after:  List[LogEntry] # entries immediately after
```

`ContextWindow.all_entries()` returns a flat list `before + [entry] + after`.

## API

### `extract_context(entries, indices, before=0, after=0)`

Build one `ContextWindow` per matched index.

| Parameter | Type        | Description                              |
|-----------|-------------|------------------------------------------|
| `entries` | `list`      | Full ordered list of `LogEntry` objects  |
| `indices` | `list[int]` | Positions of matched entries             |
| `before`  | `int`       | Lines to include before each match       |
| `after`   | `int`       | Lines to include after each match        |

Boundaries are clamped automatically — no `IndexError` at the start or
end of the list.

### `context_around(entries, entry, before=0, after=0)`

Convenience wrapper that locates `entry` by identity (`is`) and returns
a single `ContextWindow`, or `None` if the entry is not present.

## Example

```python
from logslice.slice import slice_text
from logslice.grep import grep_entries, compile_pattern
from logslice.context import extract_context

entries = slice_text(log_text)
pattern = compile_pattern("ERROR", ignore_case=True)
matches = grep_entries(entries, pattern)

# find original indices
index_map = {id(e): i for i, e in enumerate(entries)}
indices = [index_map[id(m)] for m in matches]

windows = extract_context(entries, indices, before=2, after=2)
for w in windows:
    for e in w.all_entries():
        print(e.raw)
    print("---")
```
