"""Unified error classes for tp.libs.templating."""

from __future__ import annotations

__all__ = [
    # Path errors (from pathsolver)
    "ParseError",
    "FormatError",
    "ResolveError",
    # Naming errors
    "TokenNotFoundError",
    "RuleNotFoundError",
    "ConventionNotFoundError",
    # Validation errors
    "ValidationError",
    # Version errors
    "VersionParseError",
    # Configuration errors
    "ConfigurationError",
]


# =============================================================================
# Path Errors (from pathsolver)
# =============================================================================


class ParseError(Exception):
    """Raised when a template is unable to parse a path."""


class FormatError(Exception):
    """Raised when a template is unable to format data into a path."""


class ResolveError(Exception):
    """Raised when a template reference cannot be resolved."""


# =============================================================================
# Naming Errors
# =============================================================================


class TokenNotFoundError(Exception):
    """Raised when a token is not found in the naming convention."""


class RuleNotFoundError(Exception):
    """Raised when a rule is not found in the naming convention."""


class ConventionNotFoundError(Exception):
    """Raised when a naming convention is not found."""


# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(Exception):
    """Raised when asset validation fails."""

    def __init__(
        self,
        message: str,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
    ):
        super().__init__(message)
        self.errors = errors or []
        self.warnings = warnings or []


# =============================================================================
# Version Errors
# =============================================================================


class VersionParseError(Exception):
    """Raised when a version string cannot be parsed."""


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""
