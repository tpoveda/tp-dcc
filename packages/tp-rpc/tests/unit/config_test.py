from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock, call

import pytest

from tp.libs.rpc.core.config import ConfigManager, get_config


@pytest.fixture
def mock_config_path():
    """Mock the config path to avoid file system operations."""
    with patch("tp.libs.rpc.core.paths.get_config_path") as mock_path:
        mock_path.return_value = Path("/mock/path/config.json")
        yield mock_path


@pytest.fixture
def reset_config_manager():
    """Reset the ConfigManager singleton between tests."""
    # Save original instance
    original_instance = ConfigManager._instance
    # Reset for test
    ConfigManager._instance = None
    yield
    # Restore after test
    ConfigManager._instance = original_instance


def test_singleton_pattern():
    """Test that ConfigManager is a singleton."""
    config1 = ConfigManager()
    config2 = ConfigManager()
    assert config1 is config2


def test_get_config():
    """Test that get_config returns the singleton instance."""
    config = get_config()
    assert isinstance(config, ConfigManager)
    assert config is ConfigManager()


def test_default_config(mock_config_path, reset_config_manager):
    """Test that the default config is used when no file exists."""
    with patch("pathlib.Path.exists", return_value=False):
        # Use a context manager to properly handle the mock_open
        m = mock_open()
        with patch("builtins.open", m):
            config = ConfigManager()
            # Check that defaults are loaded
            assert config.get("server", "host") == "localhost"
            assert config.get("security", "allow_remote_control") is True

            # Check that the file is saved - this is the key fix
            # The file should be opened for writing
            m.assert_called_with(mock_config_path.return_value, "w")


def test_load_existing_config(mock_config_path, reset_config_manager):
    """Test loading an existing config file."""
    test_config = {
        "server": {"host": "testhost", "default_port": 8080},
        "security": {"allow_remote_control": False},
    }

    # Create a new ConfigManager instance with a clean slate
    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "builtins.open", mock_open(read_data=json.dumps(test_config))
        ):
            # Force a new instance by resetting the singleton
            ConfigManager._instance = None
            config = ConfigManager()

            # These assertions should now pass with the correct values
            assert config.get("server", "host") == "testhost"
            assert config.get("server", "default_port") == 8080
            assert config.get("security", "allow_remote_control") is False
            assert config.get("server", "connection_timeout") == 5.0


def test_set_config_value(mock_config_path, reset_config_manager):
    """Test setting a config value."""
    with patch("pathlib.Path.exists", return_value=False):
        # Create a mock that can be called multiple times
        m = mock_open()
        with patch("builtins.open", m):
            config = ConfigManager()

            # Reset the call count after initialization
            m.reset_mock()

            # Set a value which should trigger a save
            config.set("server", "host", "newhost")
            assert config.get("server", "host") == "newhost"

            # Verify the file was opened for writing
            assert m.call_count >= 1
            m.assert_called_with(mock_config_path.return_value, "w")


def test_get_section(mock_config_path, reset_config_manager):
    """Test getting an entire section."""
    with patch("pathlib.Path.exists", return_value=False):
        with patch("builtins.open", mock_open()):
            config = ConfigManager()

            # Get the section before modifying it
            section = config.get_section("server")
            assert isinstance(section, dict)
            assert section["host"] == "localhost"
            assert section["default_port"] == 0


def test_get_all(mock_config_path):
    """Test getting the entire config."""
    with patch("pathlib.Path.exists", return_value=False):
        with patch("builtins.open", mock_open()):
            config = ConfigManager()
            all_config = config.get_all()
            assert isinstance(all_config, dict)
            assert "server" in all_config
            assert "security" in all_config


def test_error_handling_load(mock_config_path, reset_config_manager):
    """Test error handling when loading config."""
    with patch("pathlib.Path.exists", return_value=True):
        # Create a mock that raises an exception
        with patch("builtins.open", side_effect=Exception("Test error")):
            # Create a mock for the logger
            mock_logger = MagicMock()
            with patch("loguru.logger.error", mock_logger):
                config = ConfigManager()

                # Verify the logger was called
                mock_logger.assert_called_once()

                # Should fall back to defaults
                assert config.get("server", "host") == "localhost"


def test_error_handling_save(mock_config_path, reset_config_manager):
    """Test error handling when saving config."""
    with patch("pathlib.Path.exists", return_value=False):
        # Create a mock that works for the first call but raises an exception for the second
        m = mock_open()
        m.side_effect = [m.return_value, Exception("Test error")]

        with patch("builtins.open", m):
            config = ConfigManager()

            # Create a mock for the logger
            mock_logger = MagicMock()
            with patch("loguru.logger.error", mock_logger):
                # This should trigger the exception in _save_config
                config.set("server", "host", "newhost")

                # Verify the logger was called
                mock_logger.assert_called_once()
