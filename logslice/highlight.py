"""Terminal color highlighting for log entries by severity."""

from typing import Optional

# ANSI escape codes
RESET = "\033[0m"
BOLD = "\033[1m"

COLORS = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_red": "\033[91m",
    "bright_yellow": "\033[93m",
    "bright_cyan": "\033[96m",
}

# Severity -> (color, bold)
SEVERITY_STYLES: dict[str, tuple[str, bool]] = {
    "debug": ("cyan", False),
    "info": ("green", False),
    "notice": ("bright_cyan", False),
    "warning": ("bright_yellow", True),
    "warn": ("bright_yellow", True),
    "error": ("red", True),
    "err": ("red", True),
    "critical": ("bright_red", True),
    "fatal": ("bright_red", True),
    "emergency": ("bright_red", True),
}


def colorize(text: str, color: str, bold: bool = False) -> str:
    """Wrap text in ANSI color codes."""
    code = COLORS.get(color, "")
    prefix = BOLD if bold else ""
    return f"{prefix}{code}{text}{RESET}"


def highlight_line(line: str, severity: Optional[str], enabled: bool = True) -> str:
    """Apply severity-based color to a log line.

    Args:
        line: The formatted log line string.
        severity: The severity level (e.g. 'error', 'info').
        enabled: If False, return line unchanged (e.g. when not a TTY).

    Returns:
        The line with ANSI codes applied, or unchanged if disabled.
    """
    if not enabled or severity is None:
        return line

    key = severity.lower()
    style = SEVERITY_STYLES.get(key)
    if style is None:
        return line

    color, bold = style
    return colorize(line, color, bold)


def supports_color(stream) -> bool:
    """Return True if the given stream appears to support ANSI color codes."""
    import os
    if hasattr(stream, "isatty") and stream.isatty():
        return os.environ.get("TERM", "") != "dumb"
    return False
