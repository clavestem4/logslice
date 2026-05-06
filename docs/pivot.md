# logslice.pivot

Group log entries into a structured pivot table by a chosen key.

## Overview

`pivot` organises a list of `LogEntry` objects into named groups, returning a
`PivotTable` that you can inspect, count, or serialise.

## Built-in Keys

| Key        | Groups by                          |
|------------|------------------------------------|
| `severity` | Log level (INFO, ERROR, …)         |
| `date`     | Calendar date (`YYYY-MM-DD`)       |
| `hour`     | Hour bucket (`YYYY-MM-DDTHH`)      |

## Quick Start

```python
from logslice.slice import slice_text
from logslice.pivot import pivot

text = open("app.log").read()
entries = slice_text(text)

table = pivot(entries, key="severity")
print(table)                    # pretty summary
print(table.group_counts())     # {'INFO': 42, 'ERROR': 3, ...}
```

## Custom Key Function

Pass `key_fn` to group by any attribute:

```python
table = pivot(
    entries,
    key="source",
    key_fn=lambda e: e.message.split("[")[0].strip(),
)
```

## API

### `pivot(entries, key="severity", key_fn=None) -> PivotTable`

- **entries** – list of `LogEntry` objects.
- **key** – built-in key name *or* a label used when `key_fn` is supplied.
- **key_fn** – optional `Callable[[LogEntry], str]` that returns a group label.

Raises `ValueError` if *key* is not a built-in name and *key_fn* is `None`.

### `PivotTable`

| Member              | Description                                      |
|---------------------|--------------------------------------------------|
| `key`               | The key name used when creating the table        |
| `groups`            | `dict[str, list[LogEntry]]`                      |
| `group_keys()`      | Sorted list of group labels                      |
| `group_counts()`    | `dict[str, int]` — entries per group             |
| `as_dict()`         | JSON-serialisable representation                 |
| `__str__()`         | Human-readable summary                           |
