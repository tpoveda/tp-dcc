from __future__ import annotations

import re
from collections.abc import Callable

# Version format: MAJOR.MINOR.PATCH
VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

# Global registry of versioned functions
_versioned_functions: dict[str, dict[str, Callable]] = {}
_latest_versions: dict[str, str] = {}


def parse_version(version: str) -> tuple[int, ...]:
    """Parse a version string into its components.

    Args:
        version: Version string in format "MAJOR.MINOR.PATCH"

    Returns:
        Tuple of (major, minor, patch) as integers

    Raises:
        ValueError: If the version string is invalid
    """
    match = VERSION_PATTERN.match(version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")

    return tuple(int(x) for x in match.groups())


def compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings.

    Args:
        version1: First version string
        version2: Second version string

    Returns:
        -1 if the version1 < version2, 0 if equal, 1 if the version1 > version2
    """

    v1 = parse_version(version1)
    v2 = parse_version(version2)

    return -1 if v1 < v2 else 1 if v1 > v2 else 0


def versioned(version: str, function_name: str | None = None):
    """Decorator to register a function with a specific version.

    Args:
        version: Version string in format "MAJOR.MINOR.PATCH"
        function_name: Optional name to register the function under

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        nonlocal function_name
        func_name = function_name or func.__name__

        # Register the function with its version.
        if func_name not in _versioned_functions:
            _versioned_functions[func_name] = {}

        _versioned_functions[func_name][version] = func

        # Update the latest version if needed.
        if (
            func_name not in _latest_versions
            or compare_versions(version, _latest_versions[func_name]) > 0
        ):
            _latest_versions[func_name] = version

        # Add version info to the function's docstring.
        original_doc = func.__doc__ or ""
        version_doc = f"\nVersion: {version}\n"
        if "Version:" not in original_doc:
            func.__doc__ = original_doc + version_doc

        return func

    return decorator


def get_versioned_function(name: str, version: str | None = None) -> Callable | None:
    """Get a function with the specified version.

    Args:
        name: Function name
        version: Version string, or None for latest version

    Returns:
        The function if found, otherwise None
    """

    if name not in _versioned_functions:
        return None

    if version is None:
        # Get the latest version
        version = _latest_versions.get(name)
        if not version:
            return None

    return _versioned_functions[name].get(version)


def list_versions(function_name: str) -> list[str]:
    """List all available versions of a function.

    Args:
        function_name: Name of the function

    Returns:
        List of version strings, sorted from oldest to newest
    """

    if function_name not in _versioned_functions:
        return []

    versions = list(_versioned_functions[function_name].keys())
    return sorted(versions, key=lambda v: parse_version(v))


def get_latest_version(function_name: str) -> str | None:
    """Get the latest version of a function.

    Args:
        function_name: Name of the function

    Returns:
        Latest version string, or None if function not found
    """

    return _latest_versions.get(function_name)
