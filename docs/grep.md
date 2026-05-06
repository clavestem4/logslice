# logslice.grep — Pattern Search

The `grep` module provides regex-based filtering of `LogEntry` objects by message content, modelled after the familiar Unix `grep` tool.

## Functions

### `compile_pattern(pattern, ignore_case=False) -> Pattern`

Compile a regular expression string into a `re.Pattern`.

```python
from logslice.grep import compile_pattern

p = compile_pattern(r"timeout", ignore_case=True)
```

### `matches_entry(entry, pattern) -> bool`

Return `True` if the entry's `message` field matches the compiled pattern.

### `grep_entries(entries, pattern, ignore_case=False, invert=False) -> List[LogEntry]`

Filter a list of entries by regex pattern.

```python
from logslice.grep import grep_entries

errors = grep_entries(entries, r"error|fail", ignore_case=True)
```

| Argument | Type | Default | Description |
|---|---|---|---|
| `entries` | `List[LogEntry]` | — | Entries to search |
| `pattern` | `str` | — | Regex pattern |
| `ignore_case` | `bool` | `False` | Case-insensitive match |
| `invert` | `bool` | `False` | Return non-matching entries |

### `grep_count(entries, pattern, ignore_case=False) -> int`

Return the count of matching entries without building a full list.

```python
from logslice.grep import grep_count

n = grep_count(entries, "timeout")
print(f"{n} timeout entries found")
```

### `first_match(entries, pattern, ignore_case=False) -> Optional[LogEntry]`

Return the first matching entry, or `None` if none match.

```python
from logslice.grep import first_match

entry = first_match(entries, "FATAL")
if entry:
    print("First fatal:", entry.message)
```

## CLI Usage

The `cli_grep` module exposes `run_grep` and `add_grep_arguments` for integration into the main CLI.

```
logslice grep [options] <pattern> <logfile>

Options:
  -i, --ignore-case   Case-insensitive matching
  -v, --invert        Show non-matching entries
  -c, --count         Print match count only
  --format            Output format: text | json | csv
```

## Example

```python
from logslice.slice import slice_file
from logslice.grep import grep_entries

entries = slice_file("app.log")
matches = grep_entries(entries, r"connection (refused|timeout)", ignore_case=True)
for e in matches:
    print(e.timestamp, e.severity, e.message)
```
