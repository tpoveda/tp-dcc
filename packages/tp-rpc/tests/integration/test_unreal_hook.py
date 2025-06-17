from __future__ import annotations

import sys
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.hooks.plugins import unreal_plugin
from tp.libs.rpc.core.instances import list_instances, cleanup_registry
from tests.conftest import run_dcc_server_test


def test_unreal_plugin():
    """Test the Unreal plugin initialization and shutdown."""
    # Mock the Unreal module
    unreal_mock = MagicMock()

    with patch.dict("sys.modules", {"unreal": unreal_mock}):
        # Test the plugin
        run_dcc_server_test(unreal_plugin, "unreal")


def test_unreal_runtime_state():
    """Test the Unreal plugin runtime state."""
    # Verify initial state
    assert unreal_plugin._runtime_state["dcc_type"] == "unreal"
    assert unreal_plugin._runtime_state["instance_name"] is None
    assert isinstance(unreal_plugin._runtime_state["handles"], dict)


def test_unreal_tick_callback():
    """Test Unreal's tick callback registration and unregistration."""
    # Mock the Unreal module
    unreal_mock = MagicMock()

    with patch.dict("sys.modules", {"unreal": unreal_mock}):
        # Test _start_post_tick_loop
        unreal_plugin._start_post_tick_loop()

        # Verify register_slate_post_tick_callback was called
        unreal_mock.register_slate_post_tick_callback.assert_called_once()

        # Verify handle was stored
        assert (
            "UNREAL_POST_TICK_DELEGATE_HANDLE"
            in unreal_plugin._runtime_state["handles"]
        )

        # Test _unregister_tick_callback
        unreal_plugin._unregister_tick_callback()

        # Verify unregister_slate_post_tick_callback was called
        unreal_mock.unregister_slate_post_tick_callback.assert_called_once_with(
            unreal_mock.register_slate_post_tick_callback.return_value
        )

        # Verify handle was removed
        assert (
            "UNREAL_POST_TICK_DELEGATE_HANDLE"
            not in unreal_plugin._runtime_state["handles"]
        )


def test_unreal_shutdown_callback():
    """Test Unreal's Python shutdown callback registration."""
    # Mock the Unreal module
    unreal_mock = MagicMock()

    with patch.dict("sys.modules", {"unreal": unreal_mock}):
        # Test _register_python_shutdown_callback
        unreal_plugin._register_python_shutdown_callback()

        # Verify register_python_shutdown_callback was called
        unreal_mock.register_python_shutdown_callback.assert_called_once_with(
            unreal_plugin.shutdown
        )


def test_unreal_initialize_shutdown():
    """Test Unreal's initialize and shutdown functions."""
    # Mock the Unreal module
    unreal_mock = MagicMock()

    with patch.dict("sys.modules", {"unreal": unreal_mock}):
        # Mock dependencies
        with patch(
            "tp.libs.rpc.hooks.shared_loader.load_all_shared_hooks"
        ) as mock_load_hooks:
            with patch(
                "tp.libs.rpc.api.interface.launch_server",
                return_value="test-unreal",
            ) as mock_launch:
                with patch.object(
                    unreal_plugin, "_start_post_tick_loop"
                ) as mock_start_tick:
                    with patch.object(
                        unreal_plugin, "_register_python_shutdown_callback"
                    ) as mock_register_shutdown:
                        # Test initialize
                        instance_name = unreal_plugin.initialize(
                            host="localhost",
                            port=0,
                            instance_name="test-unreal",
                        )

                        # Verify calls
                        mock_load_hooks.assert_called_once()
                        mock_start_tick.assert_called_once()
                        mock_register_shutdown.assert_called_once()
                        mock_launch.assert_called_once_with(
                            host="localhost",
                            port=0,
                            dcc_type="unreal",
                            instance_name="test-unreal",
                            additional_globals={"unreal": unreal_mock},
                        )

                        # Verify instance name
                        assert instance_name == "test-unreal"
                        assert (
                            unreal_plugin._runtime_state["instance_name"]
                            == "test-unreal"
                        )

                        # Test shutdown
                        with patch(
                            "tp.libs.rpc.api.interface.stop_server"
                        ) as mock_stop:
                            with patch.object(
                                unreal_plugin, "_unregister_tick_callback"
                            ) as mock_unregister_tick:
                                with patch(
                                    "tp.libs.rpc.core.instances.unregister_instance"
                                ) as mock_unregister:
                                    unreal_plugin.shutdown()

                                    # Verify calls
                                    mock_stop.assert_called_once()
                                    mock_unregister_tick.assert_called_once()
                                    mock_unregister.assert_called_once_with(
                                        "unreal", "test-unreal"
                                    )
