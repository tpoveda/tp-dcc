from __future__ import annotations

import enum


class PrefixSuffixType(enum.Enum):
    """
    Enum that defines the type of prefix or suffix to apply to the given object.
    """

    Prefix = "prefix"
    Suffix = "suffix"


class EditIndexMode(enum.Enum):
    """
    Enum that defines the mode to edit the index item.
    """

    Insert = "insert"
    Replace = "replace"
    Remove = "remove"
