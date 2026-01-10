"""tp.libs.templating.naming - Name templating module.

This module provides token-based naming convention functionality including:
- Token: Key-value pairs for placeholders
- Rule: Expressions with token placeholders
- NamingConvention: Container with parent-child inheritance
"""

from __future__ import annotations

from tp.libs.templating.naming.config import NamingConfiguration
from tp.libs.templating.naming.consts import EditIndexMode, PrefixSuffixType
from tp.libs.templating.naming.convention import (
    NamingConvention,
    NamingConventionChanges,
)
from tp.libs.templating.naming.preset import (
    NameConventionData,
    NamingPreset,
    PresetsManager,
)
from tp.libs.templating.naming.rule import Rule
from tp.libs.templating.naming.token import KeyValue, Token

__all__ = [
    "Token",
    "KeyValue",
    "Rule",
    "NamingConvention",
    "NamingConventionChanges",
    "PresetsManager",
    "NamingPreset",
    "NameConventionData",
    "NamingConfiguration",
    "EditIndexMode",
    "PrefixSuffixType",
]
