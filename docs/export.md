# Export

The `logslice.export` module lets you persist filtered log entries to disk in
several formats without going through the CLI.

## Supported Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| `text` | `.txt`    | One human-readable line per entry |
| `jsonl` | `.jsonl` | Newline-delimited JSON (streaming-friendly) |
| `json` | `.json`   | Pretty-printed JSON array |
| `csv`  | `.csv`    | CSV with header row |

## Quick Start

```python
from pathlib import Path
from logslice.slice import slice_file
from logslice.export import export_entries

entries = slice_file("app.log", severity_min="WARN")
written = export_entries(entries, Path("warnings.jsonl"), fmt="jsonl")
print(f"Exported {written} entries")
```

## API Reference

### `export_entries(entries, dest, fmt="text") -> int`

High-level dispatcher. Writes *entries* to *dest* using the chosen *fmt*.
Returns the number of entries written.

Raises `ValueError` for unknown format strings.

### `export_text(entries, dest) -> int`

Writes entries using the same plain-text format as the CLI default output.

### `export_jsonl(entries, dest) -> int`

Writes one JSON object per line.  Safe to stream and append.

### `export_json(entries, dest) -> int`

Writes a pretty-printed JSON array.  Loads the full list into memory first.

### `export_csv(entries, dest) -> int`

Writes a CSV file with columns: `timestamp`, `severity`, `message`, `raw`.

## CLI Integration

The `--output` / `-o` flag and `--format` flag in `logslice.cli` delegate to
`export_entries` when a destination path is provided.
