from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from tp.libs.rpc.core.paths import get_registry_path, get_config_path


def test_get_registry_path_windows():
    """Test that get_registry_path returns the correct path on Windows."""

    with patch("platform.system", return_value="Windows"):
        path = get_registry_path()
        expected = Path.home() / "AppData" / "Roaming" / "tp_dcc_rpc" / "registry.json"
        assert path == expected


def test_get_registry_path_unix():
    """Test that get_registry_path returns the correct path on Unix systems."""

    with patch("platform.system", return_value="Linux"):
        path = get_registry_path()
        expected = Path.home() / ".config" / "tp_dcc_rpc" / "registry.json"
        assert path == expected


def test_get_config_path_windows():
    """Test that get_config_path returns the correct path on Windows."""

    with patch("platform.system", return_value="Windows"):
        path = get_config_path()
        expected = Path.home() / "AppData" / "Roaming" / "tp_dcc_rpc" / "config.json"
        assert path == expected


def test_get_config_path_unix():
    """Test that get_config_path returns the correct path on Unix systems."""

    with patch("platform.system", return_value="Linux"):
        path = get_config_path()
        expected = Path.home() / ".config" / "tp_dcc_rpc" / "config.json"
        assert path == expected


def test_directory_creation():
    """Test that the directory is created if it doesn't exist."""

    with patch("platform.system", return_value="Windows"):
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            get_registry_path()
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
