from __future__ import annotations

import enum

# ==============================================================================
# Environment related constants and enumerators.
# ==============================================================================

ENV_VAR = "TP_ENV"


class EnvironmentMode(enum.Enum):
    """Enumeration that defines the different environment modes."""

    Production = "prod"
    Development = "dev"
    Test = "test"


# ==============================================================================
# Logger related constants and enumerators.
# ==============================================================================

LOGGER_NAME = "tp"
LOG_LEVEL_ENV_VAR = "TP_LOG_LEVEL"
LOG_LEVEL_DEFAULT = "INFO"
