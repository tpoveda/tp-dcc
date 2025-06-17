from __future__ import annotations

import time
import threading
from datetime import datetime
from unittest.mock import patch, MagicMock, call

import pytest

from tp.libs.rpc.core.health import HealthMonitor, get_health_monitor


@pytest.fixture
def mock_list_instances():
    """Mock the list_instances function."""
    with patch("tp.libs.rpc.core.health.list_instances") as mock:
        mock.return_value = {
            "maya": {
                "maya-1": {"uri": "PYRO:test@localhost:9001"},
                "maya-2": {"uri": "PYRO:test@localhost:9002"},
            },
            "unreal": {
                "unreal-1": {"uri": "PYRO:test@localhost:9003"},
            },
        }
        yield mock


@pytest.fixture
def mock_cleanup_registry():
    """Mock the cleanup_registry function."""
    with patch("tp.libs.rpc.core.health.cleanup_registry") as mock:
        yield mock


@pytest.fixture
def mock_call_remote_function():
    """Mock the call_remote_function function."""
    with patch("tp.libs.rpc.core.health.call_remote_function") as mock:
        # Default to successful pings
        mock.return_value = {"status": "ok"}
        yield mock


def test_health_monitor_init():
    """Test HealthMonitor initialization."""
    monitor = HealthMonitor(check_interval=30.0)

    assert monitor._check_interval == 30.0
    assert monitor._running is False
    assert monitor._thread is None
    assert isinstance(monitor._status, dict)
    assert len(monitor._status) == 0
    assert isinstance(monitor._callbacks, list)
    assert len(monitor._callbacks) == 0


def test_health_monitor_start_stop():
    """Test starting and stopping the health monitor."""
    with patch("threading.Thread") as mock_thread:
        thread_instance = MagicMock()
        mock_thread.return_value = thread_instance

        monitor = HealthMonitor()

        # Test starting
        monitor.start()

        assert monitor._running is True
        mock_thread.assert_called_once_with(
            target=monitor._monitor_loop,
            daemon=True,
            name="HealthMonitorThread",
        )
        thread_instance.start.assert_called_once()

        # Test starting when already running
        mock_thread.reset_mock()
        thread_instance.start.reset_mock()

        monitor.start()  # Should do nothing

        mock_thread.assert_not_called()
        thread_instance.start.assert_not_called()

        # Test stopping
        monitor.stop()

        assert monitor._running is False
        thread_instance.join.assert_called_once_with(timeout=5.0)
        assert monitor._thread is None


def test_monitor_loop():
    """Test the monitor loop."""
    monitor = HealthMonitor(check_interval=0.1)

    # Mock the _check_all_instances method
    with patch.object(monitor, "_check_all_instances") as mock_check:
        with patch("time.sleep") as mock_sleep:
            # Run the loop for a short time
            def stop_after_one_iteration():
                # Let it run one iteration then stop
                time.sleep(0.05)
                monitor._running = False

            stop_thread = threading.Thread(target=stop_after_one_iteration)
            stop_thread.start()

            monitor._running = True
            monitor._monitor_loop()

            stop_thread.join()

            # Should have called _check_all_instances at least once
            mock_check.assert_called()
            # Should have called sleep at least once
            mock_sleep.assert_called()


def test_check_all_instances(
    mock_list_instances, mock_cleanup_registry, mock_call_remote_function
):
    """Test checking all instances."""
    monitor = HealthMonitor()

    # Test with all instances healthy
    monitor._check_all_instances()

    mock_cleanup_registry.assert_called_once()
    mock_list_instances.assert_called_once()

    # Should have made 3 calls to call_remote_function (one for each instance)
    assert mock_call_remote_function.call_count == 3

    # Check that status was updated for all instances
    assert len(monitor._status) == 3
    assert "maya/maya-1" in monitor._status
    assert "maya/maya-2" in monitor._status
    assert "unreal/unreal-1" in monitor._status

    # All instances should be healthy
    for status in monitor._status.values():
        assert status["healthy"] is True
        assert "last_check" in status
        assert status["error"] is None
        assert status["ping_result"] == {"status": "ok"}


def test_check_all_instances_with_errors(
    mock_list_instances, mock_cleanup_registry, mock_call_remote_function
):
    """Test checking instances with some errors."""
    monitor = HealthMonitor()

    # Make one instance fail
    def side_effect(dcc_type, instance_name, function_name, _timeout=None):
        if dcc_type == "maya" and instance_name == "maya-2":
            raise Exception("Test error")
        return {"status": "ok"}

    mock_call_remote_function.side_effect = side_effect

    # Register a callback
    callback = MagicMock()
    monitor.register_callback(callback)

    # Check instances
    monitor._check_all_instances()

    # Should have made 3 calls to call_remote_function
    assert mock_call_remote_function.call_count == 3

    # Check that status was updated for all instances
    assert len(monitor._status) == 3

    # Check healthy instances
    assert monitor._status["maya/maya-1"]["healthy"] is True
    assert monitor._status["unreal/unreal-1"]["healthy"] is True

    # Check unhealthy instance
    assert monitor._status["maya/maya-2"]["healthy"] is False
    assert monitor._status["maya/maya-2"]["error"] == "Test error"

    # Check that callback was called for each instance
    assert callback.call_count == 3
    callback.assert_any_call("maya", "maya-1", True)
    callback.assert_any_call("maya", "maya-2", False)
    callback.assert_any_call("unreal", "unreal-1", True)


def test_callback_error(
    mock_list_instances, mock_cleanup_registry, mock_call_remote_function
):
    """Test handling errors in callbacks."""
    monitor = HealthMonitor()

    # Register a callback that raises an exception
    callback = MagicMock(side_effect=Exception("Callback error"))
    monitor.register_callback(callback)

    # Mock the logger
    with patch("loguru.logger.error") as mock_logger:
        # Check instances
        monitor._check_all_instances()

        # Should have logged the error
        assert mock_logger.call_count == 3  # One for each instance
        mock_logger.assert_any_call(
            "[tp-rpc][health] Error in callback: Callback error"
        )


def test_get_status():
    """Test getting status."""
    monitor = HealthMonitor()

    # Set up some test status data
    monitor._status = {
        "maya/maya-1": {"healthy": True, "last_check": datetime.now()},
        "maya/maya-2": {"healthy": False, "last_check": datetime.now()},
        "unreal/unreal-1": {"healthy": True, "last_check": datetime.now()},
    }

    # Test getting all status
    status = monitor.get_status()
    assert len(status) == 3
    assert "maya/maya-1" in status
    assert "maya/maya-2" in status
    assert "unreal/unreal-1" in status

    # Test filtering by DCC type
    maya_status = monitor.get_status(dcc_type="maya")
    assert len(maya_status) == 2
    assert "maya/maya-1" in maya_status
    assert "maya/maya-2" in maya_status
    assert "unreal/unreal-1" not in maya_status

    # Test filtering by DCC type and instance name
    instance_status = monitor.get_status(
        dcc_type="maya", instance_name="maya-1"
    )
    assert len(instance_status) == 1
    assert "maya/maya-1" in instance_status

    # Test getting status for unknown instance
    unknown_status = monitor.get_status(
        dcc_type="blender", instance_name="blender-1"
    )
    assert len(unknown_status) == 1
    assert "blender/blender-1" in unknown_status
    assert unknown_status["blender/blender-1"]["healthy"] is False
    assert unknown_status["blender/blender-1"]["error"] == "Unknown instance"


def test_register_unregister_callback():
    """Test registering and unregistering callbacks."""
    monitor = HealthMonitor()

    callback1 = lambda dcc, instance, healthy: None
    callback2 = lambda dcc, instance, healthy: None

    # Register callbacks
    monitor.register_callback(callback1)
    assert len(monitor._callbacks) == 1
    assert monitor._callbacks[0] is callback1

    # Register same callback again (should not add duplicate)
    monitor.register_callback(callback1)
    assert len(monitor._callbacks) == 1

    # Register another callback
    monitor.register_callback(callback2)
    assert len(monitor._callbacks) == 2

    # Unregister callback
    monitor.unregister_callback(callback1)
    assert len(monitor._callbacks) == 1
    assert monitor._callbacks[0] is callback2

    # Unregister non-existent callback (should not error)
    monitor.unregister_callback(callback1)
    assert len(monitor._callbacks) == 1


def test_get_health_monitor():
    """Test the get_health_monitor function."""
    # Should return the singleton instance
    monitor1 = get_health_monitor()
    monitor2 = get_health_monitor()

    assert monitor1 is monitor2
    assert isinstance(monitor1, HealthMonitor)
