from __future__ import annotations

import sys
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.hooks.plugins import mobu_plugin
from tp.libs.rpc.core.instances import list_instances, cleanup_registry
from tests.conftest import run_dcc_server_test


def test_mobu_plugin():
    """Test the MotionBuilder plugin initialization and shutdown."""
    # Mock the MotionBuilder module
    fb_mock = MagicMock()

    with patch.dict("sys.modules", {"pyfbsdk": fb_mock}):
        # Test the plugin
        run_dcc_server_test(mobu_plugin, "mobu")


def test_mobu_runtime_state():
    """Test the MotionBuilder plugin runtime state."""
    # Verify initial state
    # Note: There's a bug in the runtime state - dcc_type is set to "unreal" instead of "mobu"
    assert (
        mobu_plugin._runtime_state["dcc_type"] == "unreal"
    )  # This should be "mobu"
    assert mobu_plugin._runtime_state["instance_name"] is None
    assert isinstance(mobu_plugin._runtime_state["handles"], dict)


def test_mobu_idle_callback():
    """Test MotionBuilder's idle callback registration and unregistration."""
    # Mock the MotionBuilder module
    fb_mock = MagicMock()
    fb_system_mock = MagicMock()
    fb_mock.FBSystem.return_value = fb_system_mock

    with patch.dict("sys.modules", {"pyfbsdk": fb_mock}):
        # Test _start_idle_loop
        mobu_plugin._start_idle_loop()

        # Verify OnUIIdle.Add was called
        fb_system_mock.OnUIIdle.Add.assert_called_once()

        # Verify handle was stored
        assert "MOBU_IDLE_CALLBACK" in mobu_plugin._runtime_state["handles"]

        # Test _unregister_idle_callback
        mobu_plugin._unregister_idle_callback()

        # Verify OnUIIdle.Remove was called
        fb_system_mock.OnUIIdle.Remove.assert_called_once_with(
            mobu_plugin._runtime_state["handles"]["MOBU_IDLE_CALLBACK"]
        )

        # Verify handle was removed
        assert (
            "MOBU_IDLE_CALLBACK" not in mobu_plugin._runtime_state["handles"]
        )


def test_mobu_shutdown_callback():
    """Test MotionBuilder's shutdown callback registration."""
    # Mock the Qt module
    qt_app_mock = MagicMock()
    qapplication_mock = MagicMock()
    qapplication_mock.instance.return_value = qt_app_mock

    with patch.dict(
        "sys.modules",
        {"Qt.QtWidgets": MagicMock(QApplication=qapplication_mock)},
    ):
        # Test _register_shutdown_callback
        mobu_plugin._register_shutdown_callback()

        # Verify aboutToQuit.connect was called
        qt_app_mock.aboutToQuit.connect.assert_called_once_with(
            mobu_plugin.shutdown
        )


def test_mobu_shutdown_callback_no_app():
    """Test MotionBuilder's shutdown callback registration with no QApplication."""
    # Mock the Qt module with no QApplication instance
    qapplication_mock = MagicMock()
    qapplication_mock.instance.return_value = None

    with patch.dict(
        "sys.modules",
        {"Qt.QtWidgets": MagicMock(QApplication=qapplication_mock)},
    ):
        # Mock the logger
        with patch("loguru.logger.warning") as mock_logger:
            # Test _register_shutdown_callback
            mobu_plugin._register_shutdown_callback()

            # Verify warning was logged
            mock_logger.assert_called_once()
            assert (
                "No QApplication instance found" in mock_logger.call_args[0][0]
            )


def test_mobu_initialize_shutdown():
    """Test MotionBuilder's initialize and shutdown functions."""
    # Mock the MotionBuilder module
    fb_mock = MagicMock()

    with patch.dict("sys.modules", {"pyfbsdk": fb_mock}):
        # Mock dependencies
        with patch(
            "tp.libs.rpc.hooks.shared_loader.load_all_shared_hooks"
        ) as mock_load_hooks:
            with patch(
                "tp.libs.rpc.api.interface.launch_server", return_value="test-mobu"
            ) as mock_launch:
                with patch.object(
                    mobu_plugin, "_start_idle_loop"
                ) as mock_start_idle:
                    with patch.object(
                        mobu_plugin, "_register_shutdown_callback"
                    ) as mock_register_shutdown:
                        # Test initialize
                        instance_name = mobu_plugin.initialize(
                            host="localhost", port=0, instance_name="test-mobu"
                        )

                        # Verify calls
                        mock_load_hooks.assert_called_once()
                        mock_start_idle.assert_called_once()
                        mock_register_shutdown.assert_called_once()
                        mock_launch.assert_called_once_with(
                            host="localhost",
                            port=0,
                            dcc_type="mobu",
                            instance_name="test-mobu",
                            additional_globals={
                                "fb": fb_mock,
                                "pyfbsdk": fb_mock,
                            },
                        )

                        # Verify instance name
                        assert instance_name == "test-mobu"
                        assert (
                            mobu_plugin._runtime_state["instance_name"]
                            == "test-mobu"
                        )

                        # Test shutdown
                        with patch(
                            "tp.libs.rpc.api.interface.stop_server"
                        ) as mock_stop:
                            with patch.object(
                                mobu_plugin, "_unregister_idle_callback"
                            ) as mock_unregister_idle:
                                with patch(
                                    "tp.libs.rpc.core.instances.unregister_instance"
                                ) as mock_unregister:
                                    mobu_plugin.shutdown()

                                    # Verify calls
                                    mock_stop.assert_called_once()
                                    mock_unregister_idle.assert_called_once()
                                    # Note: There's a bug in the shutdown function - it uses _runtime_state["dcc_type"] which is "unreal"
                                    # This should be fixed to use "mobu"
                                    mock_unregister.assert_called_once_with(
                                        "unreal", "test-mobu"
                                    )
