from __future__ import annotations

import re
from typing import Iterable

_DIGITS_AT_END_RE = re.compile(r"(\d+)$")


def extract_digits_from_end_of_string(string: str) -> int | None:
    """Extracts digits from the end of a string.

    Args:
        string: The string to extract digits from.

    Returns:
        The extracted digits as an integer, or None if no digits are found.
    """

    match = _DIGITS_AT_END_RE.search(string)
    return int(match.group(1)) if match else None


def remove_digits_from_end_of_string(string: str) -> str:
    """Removes digits from the end of a string.

    Args:
        string: The string to remove digits from.

    Returns:
        The string without digits at the end.
    """

    return _DIGITS_AT_END_RE.sub("", string)


def find_smallest_id(ids: Iterable[int]) -> int:
    """Return the smallest positive integer not present in ids.

    Returns:
        The smallest positive integer ID.
    """

    used = sorted({i for i in ids if i >= 1})

    candidate = 1
    for i in used:
        if i == candidate:
            candidate += 1
        elif i > candidate:
            break

    return candidate


def unique_name_from_list(existing_names: list[str], name: str) -> str:
    """Generates a unique name by appending the smallest possible integer to
    the base name if it already exists in the list.

    Args:
        existing_names: List of existing names to check against.
        name: The base name to make unique.

    Returns:
        A unique name derived from the base name.
    """

    if name not in existing_names:
        return name

    base = remove_digits_from_end_of_string(name)
    used_ids: set[int] = set()

    for existing_name in existing_names:
        if remove_digits_from_end_of_string(existing_name) != base:
            continue
        digits = extract_digits_from_end_of_string(existing_name)
        if digits is not None:
            used_ids.add(digits)

    idx = find_smallest_id(used_ids)

    return f"{base}{idx}"
