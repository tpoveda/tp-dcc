from __future__ import annotations

import sys
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.hooks.plugins import blender_plugin
from tp.libs.rpc.core.instances import list_instances, cleanup_registry
from tests.conftest import run_dcc_server_test


def test_blender_plugin():
    """Test the Blender plugin initialization and shutdown."""
    # Mock the Blender module
    bpy_mock = MagicMock()

    with patch.dict("sys.modules", {"bpy": bpy_mock}):
        # Test the plugin
        run_dcc_server_test(blender_plugin, "blender")


def test_blender_echo_function():
    """Test the Blender echo function."""
    result = blender_plugin.echo_blender("test message")
    assert result == "[Blender] test message"


def test_blender_initialize():
    """Test Blender's initialize function."""
    # Mock dependencies
    with patch("tp.libs.rpc.api.interface.launch_server") as mock_launch:
        # Test initialize
        blender_plugin.initialize(
            host="localhost", port=0, instance_name="test-blender"
        )

        # Verify launch_server was called
        mock_launch.assert_called_once_with(
            host="localhost",
            port=0,
            dcc_type="blender",
            instance_name="test-blender",
        )


def test_blender_shutdown():
    """Test Blender's shutdown function."""
    # Mock logger
    with patch("loguru.logger.info") as mock_logger:
        # Test shutdown
        blender_plugin.shutdown()

        # Verify logger was called
        mock_logger.assert_called_once_with(
            "[tp-rpc][blender] Shutdown hook not implemented."
        )
