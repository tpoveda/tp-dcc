"""tp.libs.templating.versioning - Version management module.

This module provides version management functionality including:
- VersionToken: Token for version strings with parsing and formatting
- VersionResolver: Filesystem-based version discovery
"""

from __future__ import annotations

from tp.libs.templating.versioning.resolver import VersionResolver
from tp.libs.templating.versioning.token import VersionToken

__all__ = [
    "VersionToken",
    "VersionResolver",
]
