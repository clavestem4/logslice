# Terminal Highlighting

`logslice` supports ANSI color output when writing to a terminal.
Severity levels are mapped to colors automatically.

## Severity Color Map

| Severity         | Color         | Bold |
|------------------|---------------|------|
| `debug`          | cyan          | no   |
| `info`           | green         | no   |
| `notice`         | bright cyan   | no   |
| `warning`/`warn` | bright yellow | yes  |
| `error`/`err`    | red           | yes  |
| `critical`       | bright red    | yes  |
| `fatal`          | bright red    | yes  |
| `emergency`      | bright red    | yes  |

## CLI Usage

Color is enabled automatically when writing to a terminal.
Use `--color` / `--no-color` to override:

```bash
# Force color on (e.g. when piping to less -R)
logslice app.log --color

# Disable color
logslice app.log --no-color
```

## Programmatic Usage

```python
from logslice.highlight import highlight_line, supports_color
import sys

use_color = supports_color(sys.stdout)
line = highlight_line("[ERROR] disk full", severity="error", enabled=use_color)
print(line)
```

## Notes

- Color is suppressed when `TERM=dumb` even if the stream is a TTY.
- When `fmt` is `json` or `csv`, color codes are never applied.
