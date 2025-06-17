from __future__ import annotations

import sys
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.hooks.plugins import houdini_plugin
from tp.libs.rpc.core.instances import list_instances, cleanup_registry
from tests.conftest import run_dcc_server_test


def test_houdini_plugin():
    """Test the Houdini plugin initialization and shutdown."""
    # Mock the Houdini module
    hou_mock = MagicMock()

    with patch.dict("sys.modules", {"hou": hou_mock}):
        # Test the plugin
        run_dcc_server_test(houdini_plugin, "houdini")


def test_houdini_initialize_shutdown():
    """Test Houdini's initialize and shutdown functions."""
    # Mock the Houdini module
    hou_mock = MagicMock()

    with patch.dict("sys.modules", {"hou": hou_mock}):
        # Mock dependencies
        with patch(
            "tp.libs.rpc.hooks.shared_loader.load_all_shared_hooks"
        ) as mock_load_hooks:
            with patch(
                "tp.libs.rpc.api.interface.launch_server",
                return_value="test-houdini",
            ) as mock_launch:
                # Test initialize
                instance_name = houdini_plugin.initialize(
                    host="localhost", port=0, instance_name="test-houdini"
                )

                # Verify calls
                mock_load_hooks.assert_called_once()
                mock_launch.assert_called_once_with(
                    host="localhost",
                    port=0,
                    dcc_type="houdini",
                    instance_name="test-houdini",
                    additional_globals={"hou": hou_mock},
                )

                # Verify instance name
                assert instance_name == "test-houdini"
                assert (
                    houdini_plugin._runtime_state["instance_name"]
                    == "test-houdini"
                )

                # Test shutdown
                with patch("tp.libs.rpc.api.interface.stop_server") as mock_stop:
                    with patch(
                        "tp.libs.rpc.core.instances.unregister_instance"
                    ) as mock_unregister:
                        houdini_plugin.shutdown()

                        # Verify calls
                        mock_stop.assert_called_once()
                        mock_unregister.assert_called_once_with(
                            "houdini", "test-houdini"
                        )
