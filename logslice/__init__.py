"""logslice — A fast log file parser that extracts and filters structured entries
by time range and severity.
"""

__version__ = "0.1.0"

from logslice.parser import LogEntry, parse_line, parse_lines

__all__ = ["LogEntry", "parse_line", "parse_lines"]
