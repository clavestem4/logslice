# logslice

A fast log file parser that extracts and filters structured entries by time range and severity.

---

## Installation

```bash
pip install logslice
```

---

## Usage

```python
from logslice import LogParser

parser = LogParser("app.log")

# Filter by time range and severity
entries = parser.slice(
    start="2024-01-15 08:00:00",
    end="2024-01-15 09:00:00",
    severity=["ERROR", "WARNING"]
)

for entry in entries:
    print(entry.timestamp, entry.level, entry.message)
```

You can also use the CLI:

```bash
logslice app.log --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00" --severity ERROR WARNING
```

### Supported Log Formats

- Common log format (Apache/Nginx)
- JSON structured logs
- Python `logging` module output
- Custom patterns via regex

---

## Features

- ⚡ Fast line-by-line streaming — handles large files with low memory usage
- 🕐 Flexible time range filtering with timezone support
- 🔍 Filter by one or more severity levels
- 📄 Multiple built-in format parsers + custom regex support

---

## License

This project is licensed under the [MIT License](LICENSE).