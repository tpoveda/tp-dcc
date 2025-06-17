from __future__ import annotations

import sys
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.hooks.plugins import maya_plugin
from tp.libs.rpc.core.instances import list_instances, cleanup_registry
from tests.conftest import run_dcc_server_test


def test_maya_plugin():
    """Test the Maya plugin initialization and shutdown."""
    # Mock the Maya modules
    maya_mock = MagicMock()
    cmds_mock = MagicMock()
    utils_mock = MagicMock()
    mel_mock = MagicMock()

    with patch.dict(
        "sys.modules",
        {
            "maya": maya_mock,
            "maya.cmds": cmds_mock,
            "maya.utils": utils_mock,
            "maya.mel": mel_mock,
        },
    ):
        # Test the plugin
        run_dcc_server_test(maya_plugin, "maya")


def test_maya_plugin_interface():
    """Test the Maya plugin interface implementation."""
    # Mock the Maya modules
    maya_mock = MagicMock()
    cmds_mock = MagicMock()
    utils_mock = MagicMock()
    mel_mock = MagicMock()

    with patch.dict(
        "sys.modules",
        {
            "maya": maya_mock,
            "maya.cmds": cmds_mock,
            "maya.utils": utils_mock,
            "maya.mel": mel_mock,
        },
    ):
        # Create a plugin instance
        plugin = maya_plugin.MayaPlugin()

        # Test DCC_TYPE
        assert plugin.DCC_TYPE == "maya"

        # Test SUPPORTS_THREADING
        assert plugin.SUPPORTS_THREADING is True

        # Test get_dcc_globals
        globals_dict = plugin.get_dcc_globals()
        assert "maya" in globals_dict
        assert "cmds" in globals_dict
        assert "utils" in globals_dict
        assert "mel" in globals_dict

        # Test initialize and shutdown
        with patch(
            "tp.libs.rpc.api.interface.launch_server", return_value="test-maya"
        ):
            with patch("tp.libs.rpc.hooks.shared_loader.load_all_shared_hooks"):
                with patch.object(plugin, "register_shutdown_hook"):
                    with patch.object(plugin, "setup_main_thread_execution"):
                        # Initialize
                        instance_name = plugin.initialize(
                            host="localhost", port=0, instance_name="test-maya"
                        )

                        assert instance_name == "test-maya"
                        assert plugin._instance_name == "test-maya"

                        # Shutdown
                        with patch("tp.libs.rpc.api.interface.stop_server"):
                            with patch(
                                "tp.libs.rpc.core.instances.unregister_instance"
                            ):
                                plugin.shutdown()


def test_maya_main_thread_execution():
    """Test Maya's main thread execution setup."""
    # Mock the Maya modules
    maya_mock = MagicMock()
    utils_mock = MagicMock()

    with patch.dict(
        "sys.modules", {"maya": maya_mock, "maya.utils": utils_mock}
    ):
        # Create a plugin instance
        plugin = maya_plugin.MayaPlugin()

        # Test setup_main_thread_execution
        plugin.setup_main_thread_execution()

        # Verify executeDeferred was called
        utils_mock.executeDeferred.assert_called()


def test_maya_shutdown_hook():
    """Test Maya's shutdown hook registration."""
    # Mock the Maya modules
    maya_mock = MagicMock()
    cmds_mock = MagicMock()

    with patch.dict(
        "sys.modules", {"maya": maya_mock, "maya.cmds": cmds_mock}
    ):
        # Create a plugin instance
        plugin = maya_plugin.MayaPlugin()

        # Test register_shutdown_hook
        with patch("atexit.register") as mock_atexit:
            plugin.register_shutdown_hook()

            # Verify atexit.register was called
            mock_atexit.assert_called_once_with(plugin.shutdown)

            # Verify scriptJob was called
            cmds_mock.scriptJob.assert_called_once()
            assert (
                cmds_mock.scriptJob.call_args[1]["event"][0]
                == "quitApplication"
            )
            assert cmds_mock.scriptJob.call_args[1]["runOnce"] is True
