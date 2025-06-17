from __future__ import annotations

import re
import os
from typing import Any, Callable, List, Optional, Pattern, Union
from pathlib import Path


# Basic validators
def is_string(value: Any) -> bool:
    """Check if the provided value is a string.

    Args:
        value: Value to check.

    Returns:
        True if the value is a string; False otherwise.
    """

    return isinstance(value, str)


def is_int(value: Any) -> bool:
    """Check if the provided value is an integer.

    Args:
        value: Value to check.

    Returns:
        True if the value is an integer; False otherwise.
    """

    return isinstance(value, int) and not isinstance(value, bool)


def is_float(value: Any) -> bool:
    """Check if the provided value is a integer.

    Args:
        value: Value to check.

    Returns:
        True if the value is a integer; False otherwise.
    """

    return isinstance(value, float)


def is_bool(value: Any) -> bool:
    """Check if the provided value is a boolean.

    Args:
        value: Value to check.

    Returns:
        True if the value is a boolean; False otherwise.
    """

    return isinstance(value, bool)


def is_list(value: Any) -> bool:
    """Check if the provided value is a list.

    Args:
        value: Value to check.

    Returns:
        True if the value is a list; False otherwise.
    """

    return isinstance(value, list)


def is_dict(value: Any) -> bool:
    """Check if the provided value is a dictionary.

    Args:
        value: Value to check.

    Returns:
        True if the value is a dictionary; False otherwise.
    """

    return isinstance(value, dict)


def is_none(value: Any) -> bool:
    """Check if the provided value is None.

    Args:
        value: Value to check.

    Returns:
        True if the value is None; False otherwise.
    """

    return value is None


# Compound validators
def is_string_or_none(value: Any) -> bool:
    """Check if the provided value is a string or None.

    Args:
        value: Value to check.

    Returns:
        True if the value is a string or None; False otherwise.
    """

    return is_string(value) or is_none(value)


def is_int_or_none(value: Any) -> bool:
    """Check if the provided value is an integer or None.

    Args:
        value: Value to check.

    Returns:
        True if the value is an integer or None; False otherwise.
    """

    return is_int(value) or is_none(value)


def is_float_or_none(value: Any) -> bool:
    """Check if the provided value is a float or None.

    Args:
        value: Value to check.

    Returns:
        True if the value is a float or None; False otherwise.
    """

    return is_float(value) or is_none(value)


def is_bool_or_none(value: Any) -> bool:
    """Check if the provided value is a boolean or None.

    Args:
        value: Value to check.

    Returns:
        True if the value is a boolean or None; False otherwise.
    """

    return is_bool(value) or is_none(value)


def is_list_or_none(value: Any) -> bool:
    """Check if the provided value is a list or None.

    Args:
        value: Value to check.

    Returns:
        True if the value is a list or None; False otherwise.
    """

    return is_list(value) or is_none(value)


def is_dict_or_none(value: Any) -> bool:
    """Check if the provided value is a dictionary or None.

    Args:
        value: Value to check.

    Returns:
        True if the value is a dictionary or None; False otherwise.
    """

    return is_dict(value) or is_none(value)


# Factory functions for more complex validators
def matches_pattern(pattern: Union[str, Pattern]) -> Callable[[Any], bool]:
    """Create a validator that checks if a string matches a regex pattern.

    Args:
        pattern: Regular expression pattern.

    Returns:
        Validator function.
    """

    if isinstance(pattern, str):
        compiled = re.compile(pattern)
    else:
        compiled = pattern

    def validator(value: Any) -> bool:
        return is_string(value) and bool(compiled.match(value))

    return validator


def is_in_list(valid_values: List[Any]) -> Callable[[Any], bool]:
    """Create a validator that checks if a value is in a list.

    Args:
        valid_values: List of valid values.

    Returns:
        Validator function.
    """

    def validator(value: Any) -> bool:
        return value in valid_values

    return validator


def is_valid_path(must_exist: bool = False) -> Callable[[Any], bool]:
    """Create a validator that checks if a string is a valid file path.

    Args:
        must_exist: If True, the path must exist.

    Returns:
        Validator function.
    """

    def validator(value: Any) -> bool:
        if not is_string(value):
            return False

        try:
            path = Path(value)
            return not must_exist or path.exists()
        except Exception:
            return False

    return validator


def has_length_between(min_length: int, max_length: int) -> Callable[[Any], bool]:
    """Create a validator that checks if a string or list has a length
    within range.

    Args:
        min_length: Minimum length.
        max_length: Maximum length.

    Returns:
        Validator function.
    """

    def validator(value: Any) -> bool:
        if not hasattr(value, "__len__"):
            return False
        return min_length <= len(value) <= max_length

    return validator


def is_numeric_in_range(
    min_value: Optional[float] = None, max_value: Optional[float] = None
) -> Callable[[Any], bool]:
    """Create a validator that checks if a number is within a range.

    Args:
        min_value: Minimum value (inclusive).
        max_value: Maximum value (inclusive).

    Returns:
        Validator function.
    """

    def validator(value: Any) -> bool:
        if not (is_int(value) or is_float(value)):
            return False

        if min_value is not None and value < min_value:
            return False

        if max_value is not None and value > max_value:
            return False

        return True

    return validator


# Sanitization functions
def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize a string by removing control characters.

    Args:
        value: String to sanitize.
        max_length: Optional maximum length.

    Returns:
        Sanitized string.
    """

    if not is_string(value):
        return ""

    # Remove control characters.
    sanitized = re.sub(r"[\x00-\x1F\x7F]", "", value)

    # Truncate if needed.
    if max_length is not None and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def sanitize_path(value: str) -> str:
    """Sanitize a file path.

    Args:
        value: Path to sanitize.

    Returns:
        Sanitized path.
    """

    if not is_string(value):
        return ""

    # Remove potentially dangerous characters.
    sanitized = re.sub(r'[<>:"|?*]', "_", value)

    # Normalize path separators.
    sanitized = os.path.normpath(sanitized)

    return sanitized
