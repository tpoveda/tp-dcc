"""Constants for tp.libs.templating."""

from __future__ import annotations

# =============================================================================
# Naming Constants
# =============================================================================

NAMING_PRESET_EXTENSION = "preset"
NAMING_CONVENTION_EXTENSION = "yaml"
REGEX_FILTER = r"(?<={)[^}]*"
REGEX_TOKEN_RESOLVER = r"(_*{token}_*)"
CLASS_NAME_ATTR = "_className"
CLASS_VERSION_ATTR = "_version"
DEFAULT_NAMING_PRESET_NAME = "default"

# =============================================================================
# Path Constants
# =============================================================================

START_ANCHOR = 1
END_ANCHOR = 2
BOTH_ANCHOR = 3
RELAXED_PARSE = 1
STRICT_PARSE = 2

# Code replacements for characters not allowed in regex group names
PERIOD_CODE = "_LPD_"
AT_CODE = "_WXV_"
