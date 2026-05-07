# Checkpoint

The `logslice.checkpoint` module provides resumable log parsing by persisting
the last processed byte offset and timestamp to disk.

## Overview

When processing large or rotating log files, checkpoints let you resume from
where you left off rather than re-scanning from the beginning.

## Data Model

### `Checkpoint`

| Field | Type | Description |
|-------|------|-------------|
| `file_path` | `str` | Path to the source log file |
| `byte_offset` | `int` | Byte offset of the last processed line |
| `last_timestamp` | `datetime \| None` | Timestamp of the last processed entry |
| `lines_processed` | `int` | Cumulative count of processed lines |
| `created_at` | `datetime` | When the checkpoint was first created |
| `updated_at` | `datetime` | When the checkpoint was last updated |

## Usage

```python
from logslice.checkpoint import Checkpoint, save_checkpoint, load_checkpoint, clear_checkpoint

# Create and advance a checkpoint
cp = Checkpoint(file_path="/var/log/app.log")
cp.advance(byte_offset=4096, timestamp=entry.timestamp, lines=10)

# Persist to disk (stored under .logslice/)
save_checkpoint(cp)

# Resume later
cp = load_checkpoint("/var/log/app.log")
if cp:
    print(f"Resuming from byte {cp.byte_offset}")

# Remove when done
clear_checkpoint("/var/log/app.log")
```

## Storage

Checkpoints are saved as JSON files under a configurable directory
(default: `.logslice/`). The filename is derived from the log file path
with path separators replaced by underscores.

## Integration with `tail_file`

Checkpoints pair naturally with `tail_file` and `watch_file` to build
pipelines that survive restarts without reprocessing old entries.
