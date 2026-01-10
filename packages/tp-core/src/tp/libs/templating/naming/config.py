"""Configuration management for naming conventions."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Callable

from tp.libs.templating import consts

logger = logging.getLogger(__name__)

# Environment variable name for additional preset paths (semicolon-separated on Windows, colon on Unix).
NAMING_PRESET_PATHS_ENV_VAR = "TP_NAMING_PRESET_PATHS"


@dataclass
class NamingConfiguration:
    """Configuration class that stores naming library settings.

    This class allows the naming library to be project agnostic by allowing users to define custom
    preset paths and other configuration options.

    Attributes:
        preset_paths: List of directories to search for naming presets. Paths are searched in order.
        default_preset_name: Name of the default preset to use when no preset is specified.
        environment_variable_resolver: Optional callable to resolve environment variables in paths.
            If not provided, os.path.expandvars will be used.
    """

    preset_paths: list[str] = field(default_factory=list)
    default_preset_name: str = "default"
    environment_variable_resolver: Callable[[str], str] | None = None

    def resolve_path(self, path: str) -> str:
        """Resolves environment variables in the given path.

        Args:
            path: Path that may contain environment variables.

        Returns:
            Resolved path with environment variables expanded.
        """

        if self.environment_variable_resolver:
            return self.environment_variable_resolver(path)
        return os.path.expandvars(path)

    def add_preset_path(self, path: str, prepend: bool = False):
        """Adds a preset path to the configuration.

        Args:
            path: Path to add.
            prepend: If True, adds the path at the beginning of the list (higher priority).
        """

        resolved_path = self.resolve_path(path)
        if resolved_path not in self.preset_paths:
            if prepend:
                self.preset_paths.insert(0, resolved_path)
            else:
                self.preset_paths.append(resolved_path)
            logger.debug(f"Added preset path: {resolved_path}")

    def remove_preset_path(self, path: str) -> bool:
        """Removes a preset path from the configuration.

        Args:
            path: Path to remove.

        Returns:
            True if the path was removed; False otherwise.
        """

        resolved_path = self.resolve_path(path)
        if resolved_path in self.preset_paths:
            self.preset_paths.remove(resolved_path)
            logger.debug(f"Removed preset path: {resolved_path}")
            return True
        return False

    def find_preset_file(self, preset_name: str) -> str | None:
        """Finds a preset file by name in the configured preset paths.

        Args:
            preset_name: Name of the preset to find (without extension).

        Returns:
            Absolute path to the preset file if found; None otherwise.
        """

        for preset_path in self.preset_paths:
            preset_file = os.path.join(
                preset_path, f"{preset_name}.{consts.NAMING_PRESET_EXTENSION}"
            )
            if os.path.isfile(preset_file):
                return preset_file

        return None

    def find_convention_file(self, convention_name: str) -> str | None:
        """Finds a naming convention file by name in the configured preset paths.

        Args:
            convention_name: Name of the convention to find (without extension).

        Returns:
            Absolute path to the convention file if found; None otherwise.
        """

        for preset_path in self.preset_paths:
            convention_file = os.path.join(
                preset_path,
                f"{convention_name}.{consts.NAMING_CONVENTION_EXTENSION}",
            )
            if os.path.isfile(convention_file):
                return convention_file

        return None


# Global configuration instance.
_GLOBAL_CONFIG: NamingConfiguration | None = None

# Path to the built-in presets directory (relative to this module).
_BUILTIN_PRESETS_PATH: str | None = None


def _get_builtin_presets_path() -> str:
    """Returns the path to the built-in presets directory.

    Returns:
        Absolute path to the built-in presets directory.
    """

    global _BUILTIN_PRESETS_PATH
    if _BUILTIN_PRESETS_PATH is None:
        # Navigate up one level from naming/ to templating/, then into presets/
        _BUILTIN_PRESETS_PATH = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "presets",
        )
    return _BUILTIN_PRESETS_PATH


def get_configuration() -> NamingConfiguration:
    """Returns the global naming configuration.

    If the configuration is not yet initialized, it will be created and preset paths
    will be loaded from the TP_NAMING_PRESET_PATHS environment variable if set.
    The built-in presets path is always added as the last fallback.

    Returns:
        Global NamingConfiguration instance.
    """

    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is None:
        _GLOBAL_CONFIG = NamingConfiguration()
        # First load paths from environment (these have higher priority).
        _load_preset_paths_from_environment(_GLOBAL_CONFIG)
        # Then add built-in presets path as fallback.
        builtin_path = _get_builtin_presets_path()
        if os.path.isdir(builtin_path):
            _GLOBAL_CONFIG.add_preset_path(builtin_path)
            logger.debug(f"Added built-in preset path: {builtin_path}")
    return _GLOBAL_CONFIG


def _load_preset_paths_from_environment(config: NamingConfiguration):
    """Loads preset paths from the TP_NAMING_PRESET_PATHS environment variable.

    The environment variable should contain semicolon-separated (Windows) or
    colon-separated (Unix) paths to directories containing naming presets.

    Args:
        config: NamingConfiguration instance to add paths to.
    """

    env_paths = os.environ.get(NAMING_PRESET_PATHS_ENV_VAR, "")
    if not env_paths:
        return

    # Use os.pathsep for platform-appropriate separator (';' on Windows, ':' on Unix).
    paths = env_paths.split(os.pathsep)
    for path in paths:
        path = path.strip()
        if path:
            resolved_path = config.resolve_path(path)
            if os.path.isdir(resolved_path):
                config.add_preset_path(resolved_path)
                logger.debug(
                    f"Added preset path from environment: {resolved_path}"
                )
            else:
                logger.warning(
                    f"Preset path from environment does not exist or is not a directory: {resolved_path}"
                )


def set_configuration(config: NamingConfiguration):
    """Sets the global naming configuration.

    Args:
        config: NamingConfiguration instance to set as global.
    """

    global _GLOBAL_CONFIG
    _GLOBAL_CONFIG = config
    logger.debug("Global naming configuration updated")


def reset_configuration():
    """Resets the global naming configuration to default."""

    global _GLOBAL_CONFIG
    _GLOBAL_CONFIG = None
    logger.debug("Global naming configuration reset")


def add_preset_path(path: str, prepend: bool = False):
    """Convenience function to add a preset path to the global configuration.

    Args:
        path: Path to add.
        prepend: If True, adds the path at the beginning of the list (higher priority).
    """

    get_configuration().add_preset_path(path, prepend=prepend)


def remove_preset_path(path: str) -> bool:
    """Convenience function to remove a preset path from the global configuration.

    Args:
        path: Path to remove.

    Returns:
        True if the path was removed; False otherwise.
    """

    return get_configuration().remove_preset_path(path)


def preset_paths() -> list[str]:
    """Returns the list of configured preset paths.

    Returns:
        List of preset paths.
    """

    return get_configuration().preset_paths.copy()


def builtin_presets_path() -> str:
    """Returns the path to the built-in presets directory.

    This is the directory containing the default naming presets that ship
    with the naming library.

    Returns:
        Absolute path to the built-in presets directory.
    """

    return _get_builtin_presets_path()
