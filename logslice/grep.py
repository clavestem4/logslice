"""Pattern-based filtering and searching within log entries."""

import re
from typing import List, Optional, Pattern
from logslice.parser import LogEntry


def compile_pattern(pattern: str, ignore_case: bool = False) -> Pattern:
    """Compile a regex pattern with optional case-insensitivity."""
    flags = re.IGNORECASE if ignore_case else 0
    return re.compile(pattern, flags)


def matches_entry(entry: LogEntry, pattern: Pattern) -> bool:
    """Return True if the entry's message matches the compiled pattern."""
    if entry.message is None:
        return False
    return bool(pattern.search(entry.message))


def grep_entries(
    entries: List[LogEntry],
    pattern: str,
    ignore_case: bool = False,
    invert: bool = False,
) -> List[LogEntry]:
    """Filter entries whose message matches (or does not match) a regex pattern.

    Args:
        entries: List of LogEntry objects to search.
        pattern: Regular expression pattern string.
        ignore_case: If True, matching is case-insensitive.
        invert: If True, return entries that do NOT match.

    Returns:
        Filtered list of LogEntry objects.
    """
    compiled = compile_pattern(pattern, ignore_case=ignore_case)
    result = []
    for entry in entries:
        matched = matches_entry(entry, compiled)
        if invert:
            if not matched:
                result.append(entry)
        else:
            if matched:
                result.append(entry)
    return result


def grep_count(
    entries: List[LogEntry],
    pattern: str,
    ignore_case: bool = False,
) -> int:
    """Return the number of entries whose message matches the pattern."""
    return len(grep_entries(entries, pattern, ignore_case=ignore_case))


def first_match(
    entries: List[LogEntry],
    pattern: str,
    ignore_case: bool = False,
) -> Optional[LogEntry]:
    """Return the first entry whose message matches the pattern, or None."""
    compiled = compile_pattern(pattern, ignore_case=ignore_case)
    for entry in entries:
        if matches_entry(entry, compiled):
            return entry
    return None
