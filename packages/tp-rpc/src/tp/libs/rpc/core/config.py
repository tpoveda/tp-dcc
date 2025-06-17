from __future__ import annotations

import json
import threading
from typing import Any

from loguru import logger

from .paths import get_config_path


class ConfigManager:
    """Centralized configuration management for the RPC system."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern implementation."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize the configuration manager."""
        if self._initialized:
            return

        self._config_path = get_config_path()
        self._config: dict[str, Any] = {}
        self._defaults: dict[str, Any] = {
            "server": {
                "host": "localhost",
                "default_port": 0,
                "connection_timeout": 5.0,
                "retry_enabled": True,
                "max_retry_attempts": 3,
                "use_connection_pooling": True,
                "max_connections": 10,
                "idle_timeout": 60.0,
            },
            "security": {
                "allow_remote_control": True,
                "allow_env_control": True,
                "require_authentication": False,
                "encryption_enabled": False,
            },
            "performance": {
                "compression_enabled": False,
                "compression_threshold": 10240,  # 10KB
                "serialization_format": "pickle",
            },
            "logging": {
                "level": "INFO",
                "file_enabled": True,
                "console_enabled": True,
            },
        }

        self._load_config()
        self._initialized = True

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            section: Configuration section.
            key: Configuration key.
            default: Default value if not found.

        Returns:
            Configuration value.
        """

        # noinspection PyBroadException
        try:
            return self._config.get(section, {}).get(key, default)
        except Exception:
            return default

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            section: Configuration section.
            key: Configuration key.
            value: Value to set.
        """

        if section not in self._config:
            self._config[section] = {}

        self._config[section][key] = value
        self._save_config()

    def get_section(self, section: str) -> dict[str, Any]:
        """Get an entire configuration section.

        Args:
            section: Section name.

        Returns:
            Section configuration.
        """

        return self._config.get(section, {}).copy()

    def get_all(self) -> dict[str, Any]:
        """Get the entire configuration.

        Returns:
            Complete configuration.
        """

        return self._config.copy()

    def _load_config(self):
        """Internal function that loads configuration from file or create
        default if not exists.
        """

        try:
            if self._config_path.exists():
                with open(self._config_path, "r") as f:
                    loaded_config = json.load(f)
                    # Merge with defaults for any missing values.
                    self._config = self._merge_configs(self._defaults, loaded_config)
            else:
                # Use defaults and save to file.
                self._config = self._defaults.copy()
                self._save_config()
        except Exception as e:
            logger.error(f"[tp-rpc][config] Error loading config: {e}")
            self._config = self._defaults.copy()

    def _save_config(self):
        """Internal function that saves the current configuration to a file
        in disk.
        """

        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, "w") as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            logger.error(f"[tp-rpc][config] Error saving config: {e}")

    def _merge_configs(
        self, defaults: dict[str, Any], user_config: dict[str, Any]
    ) -> dict[str, Any]:
        """Internal function that recursively merge user configuration with
        defaults.

        Args:
            defaults: Default configuration.
            user_config: User-provided configuration.

        Returns:
            Merged configuration.
        """

        result = defaults.copy()

        for key, value in user_config.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result


# Global instance
_config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """Get the global configuration manager instance.

    Returns:
        ConfigManager instance.
    """
    return _config_manager
