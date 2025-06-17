from __future__ import annotations

import os
import re
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.core.validation import (
    # Basic validators
    is_string,
    is_int,
    is_float,
    is_bool,
    is_list,
    is_dict,
    is_none,
    # Compound validators
    is_string_or_none,
    is_int_or_none,
    is_float_or_none,
    is_bool_or_none,
    is_list_or_none,
    is_dict_or_none,
    # Factory functions
    matches_pattern,
    is_in_list,
    is_valid_path,
    has_length_between,
    is_numeric_in_range,
    # Sanitization functions
    sanitize_string,
    sanitize_path,
)


# Test basic validators
def test_is_string():
    assert is_string("test") is True
    assert is_string(123) is False
    assert is_string(None) is False
    assert is_string(True) is False


def test_is_int():
    assert is_int(123) is True
    assert is_int(123.0) is False
    assert is_int("123") is False
    assert is_int(True) is False  # Booleans are a subclass of int in Python


def test_is_float():
    assert is_float(123.0) is True
    assert is_float(123) is False
    assert is_float("123.0") is False
    assert is_float(True) is False


def test_is_bool():
    assert is_bool(True) is True
    assert is_bool(False) is True
    assert is_bool(1) is False
    assert is_bool(0) is False
    assert is_bool("True") is False


def test_is_list():
    assert is_list([]) is True
    assert is_list([1, 2, 3]) is True
    assert is_list((1, 2, 3)) is False
    assert is_list("test") is False


def test_is_dict():
    assert is_dict({}) is True
    assert is_dict({"key": "value"}) is True
    assert is_dict([]) is False
    assert is_dict("test") is False


def test_is_none():
    assert is_none(None) is True
    assert is_none(0) is False
    assert is_none("") is False
    assert is_none(False) is False


# Test compound validators
def test_is_string_or_none():
    assert is_string_or_none("test") is True
    assert is_string_or_none(None) is True
    assert is_string_or_none(123) is False


def test_is_int_or_none():
    assert is_int_or_none(123) is True
    assert is_int_or_none(None) is True
    assert is_int_or_none("123") is False


def test_is_float_or_none():
    assert is_float_or_none(123.0) is True
    assert is_float_or_none(None) is True
    assert is_float_or_none(123) is False


def test_is_bool_or_none():
    assert is_bool_or_none(True) is True
    assert is_bool_or_none(None) is True
    assert is_bool_or_none(1) is False


def test_is_list_or_none():
    assert is_list_or_none([]) is True
    assert is_list_or_none(None) is True
    assert is_list_or_none({}) is False


def test_is_dict_or_none():
    assert is_dict_or_none({}) is True
    assert is_dict_or_none(None) is True
    assert is_dict_or_none([]) is False


# Test factory functions
def test_matches_pattern():
    # Test with string pattern
    validator = matches_pattern(r"^\d{3}-\d{2}-\d{4}$")
    assert validator("123-45-6789") is True
    assert validator("12345-6789") is False
    assert validator(None) is False
    assert validator(12345) is False

    # Test with compiled pattern
    compiled_pattern = re.compile(r"^[A-Z][a-z]+$")
    validator = matches_pattern(compiled_pattern)
    assert validator("Hello") is True
    assert validator("hello") is False


def test_is_in_list():
    validator = is_in_list([1, 2, 3, "test"])
    assert validator(1) is True
    assert validator("test") is True
    assert validator(4) is False
    assert validator("other") is False


def test_is_valid_path():
    # Test without existence check
    validator = is_valid_path(must_exist=False)
    assert validator("/valid/path") is True
    assert validator(123) is False

    # Test with existence check
    with patch("pathlib.Path.exists", return_value=True):
        validator = is_valid_path(must_exist=True)
        assert validator("/existing/path") is True

    with patch("pathlib.Path.exists", return_value=False):
        validator = is_valid_path(must_exist=True)
        assert validator("/non-existing/path") is False

    # Test with exception
    with patch("pathlib.Path", side_effect=Exception("Test error")):
        validator = is_valid_path()
        assert validator("/error/path") is False


def test_has_length_between():
    validator = has_length_between(2, 5)

    # Test with string
    assert validator("abc") is True
    assert validator("a") is False
    assert validator("abcdef") is False

    # Test with list
    assert validator([1, 2, 3]) is True
    assert validator([1]) is False
    assert validator([1, 2, 3, 4, 5, 6]) is False

    # Test with non-length object
    assert validator(123) is False


def test_is_numeric_in_range():
    # Test with min and max
    validator = is_numeric_in_range(min_value=0, max_value=100)
    assert validator(50) is True
    assert validator(0) is True
    assert validator(100) is True
    assert validator(-1) is False
    assert validator(101) is False
    assert validator("50") is False

    # Test with only min
    validator = is_numeric_in_range(min_value=0)
    assert validator(0) is True
    assert validator(1000) is True
    assert validator(-1) is False

    # Test with only max
    validator = is_numeric_in_range(max_value=100)
    assert validator(100) is True
    assert validator(-1000) is True
    assert validator(101) is False


# Test sanitization functions
def test_sanitize_string():
    # Test normal string
    assert sanitize_string("Hello World") == "Hello World"

    # Test with control characters
    assert sanitize_string("Hello\x00World\x1f") == "HelloWorld"

    # Test with max length
    assert sanitize_string("Hello World", max_length=5) == "Hello"

    # Test with non-string
    assert sanitize_string(123) == ""


def test_sanitize_path():
    # Test normal path
    assert sanitize_path("/valid/path") == os.path.normpath("/valid/path")

    # Test with invalid characters
    assert sanitize_path("/invalid/path?with*chars") == os.path.normpath(
        "/invalid/path_with_chars"
    )

    # Test with non-string
    assert sanitize_path(123) == ""
