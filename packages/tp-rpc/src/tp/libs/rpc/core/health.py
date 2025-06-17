from __future__ import annotations

import time
import threading
from typing import Any
from datetime import datetime
from collections.abc import Callable

from loguru import logger

from ..api.interface import call_remote_function
from .instances import list_instances, cleanup_registry


class HealthMonitor:
    """Monitors the health of RPC instances and provides status information.

    Attributes:
        _check_interval: Time between health checks in seconds.
        _running: Flag indicating if the monitor is running.
        _thread: Thread for running the health checks.
        _status: Dictionary to store the health status of instances.
        _callbacks: List of callback functions to notify on health status
            changes.
    """

    def __init__(self, check_interval: float = 60.0):
        """Initialize the health monitor.

        Args:
            check_interval: Time between health checks in seconds.
        """

        self._check_interval = check_interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._status: dict[str, dict[str, Any]] = {}
        self._callbacks: list[Callable[[str, str, bool], None]] = []

    def start(self):
        """Start the health monitoring thread."""

        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="HealthMonitorThread"
        )
        self._thread.start()

        logger.info(
            f"[tp-rpc][health] Health monitor started "
            f"(interval: {self._check_interval}s)"
        )

    def stop(self):
        """Stop the health monitoring thread."""

        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

        logger.info("[tp-rpc][health] Health monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop that runs in a background thread."""

        while self._running:
            try:
                self._check_all_instances()
            except Exception as e:
                logger.error(f"[tp-rpc][health] Error in health check: {e}")

            # Sleep for the check interval.
            for _ in range(int(self._check_interval * 2)):
                if not self._running:
                    break
                time.sleep(0.5)

    def _check_all_instances(self):
        """Check the health of all registered instances."""

        # Clean up stale instances first.
        cleanup_registry()

        # Get all current instances.
        instances = list_instances()

        for dcc_type, dcc_instances in instances.items():
            for instance_name, instance_data in dcc_instances.items():
                instance_key = f"{dcc_type}/{instance_name}"

                try:
                    # Try to ping the instance.
                    result = call_remote_function(
                        dcc_type=dcc_type,
                        instance_name=instance_name,
                        function_name="ping",
                        _timeout=2.0,  # Short timeout for health checks
                    )

                    # Update status.
                    healthy = True
                    self._status[instance_key] = {
                        "healthy": True,
                        "last_check": datetime.now(),
                        "error": None,
                        "ping_result": result,
                    }

                except Exception as e:
                    # Update status with error.
                    healthy = False
                    self._status[instance_key] = {
                        "healthy": False,
                        "last_check": datetime.now(),
                        "error": str(e),
                        "ping_result": None,
                    }

                # Notify callbacks of with a status change.
                for callback in self._callbacks:
                    try:
                        callback(dcc_type, instance_name, healthy)
                    except Exception as cb_err:
                        logger.error(f"[tp-rpc][health] Error in callback: {cb_err}")

    def get_status(
        self,
        dcc_type: str | None = None,
        instance_name: str | None = None,
    ) -> dict:
        """Get the current health status of instances.

        Args:
            dcc_type: Filter by DCC type.
            instance_name: Filter by instance name.

        Returns:
            Dictionary of health status information.
        """

        if dcc_type and instance_name:
            key = f"{dcc_type}/{instance_name}"
            return {
                key: self._status.get(
                    key, {"healthy": False, "error": "Unknown instance"}
                )
            }

        if dcc_type:
            return {
                k: v for k, v in self._status.items() if k.startswith(f"{dcc_type}/")
            }

        return self._status

    def register_callback(self, callback: Callable[[str, str, bool], None]):
        """Register a callback to be notified of health status changes.

        Args:
            callback: Function that takes (dcc_type, instance_name, is_healthy)
        """

        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[str, str, bool], None]):
        """Unregister a previously registered callback.

        Args:
            callback: The callback function to remove.
        """

        if callback in self._callbacks:
            self._callbacks.remove(callback)


# Singleton instance
_health_monitor = HealthMonitor()


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance.

    Returns:
        The singleton HealthMonitor instance.
    """

    return _health_monitor
