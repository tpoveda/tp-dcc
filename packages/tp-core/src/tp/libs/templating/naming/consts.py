from __future__ import annotations

from enum import Enum


class PrefixSuffixType(str, Enum):
    """Enum that defines the type of prefix or suffix to apply to the given object."""

    Prefix = "prefix"
    Suffix = "suffix"


class EditIndexMode(str, Enum):
    """Enum that defines the mode to edit the index item."""

    Insert = "insert"
    Replace = "replace"
    Remove = "remove"
