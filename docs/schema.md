# Schema Validation

The `logslice.schema` module lets you define structural rules for log entries
and validate a batch of parsed entries against those rules.

## Core Types

### `FieldRule`

Defines a validation constraint for a single field of a `LogEntry`.

```python
from logslice.schema import FieldRule

rule = FieldRule(
    name="severity",
    required=True,
    allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Field name (`timestamp`, `severity`, `message`) |
| `required` | `bool` | Whether a missing/empty value is an error (default `True`) |
| `pattern` | `str \| None` | Regex that the field value must match |
| `allowed_values` | `list[str] \| None` | Whitelist of accepted values (case-insensitive) |

### `Schema`

A collection of `FieldRule` objects.

```python
from logslice.schema import Schema, FieldRule

schema = (
    Schema()
    .add_rule(FieldRule(name="message", required=True))
    .add_rule(FieldRule(name="severity", allowed_values=["INFO", "ERROR"]))
)
```

`add_rule` returns `self`, so rules can be chained.

## Validating Entries

### `schema.validate_entry(entry)`

Returns a list of error strings for a single `LogEntry`. An empty list means
the entry is valid.

```python
errors = schema.validate_entry(entry)
if errors:
    for e in errors:
        print("VALIDATION ERROR:", e)
```

### `validate_entries(entries, schema)`

Validates a list of entries at once. Returns a `dict` mapping the **index** of
each invalid entry to its list of errors. Valid entries are not included.

```python
from logslice.schema import validate_entries, default_schema

results = validate_entries(entries, default_schema())
for idx, errors in results.items():
    print(f"Entry {idx}: {errors}")
```

## Default Schema

`default_schema()` returns a pre-built `Schema` that:

- Requires `message` to be non-empty.
- Accepts `severity` values of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  (case-insensitive; missing severity is allowed).

```python
from logslice.schema import default_schema

schema = default_schema()
```
