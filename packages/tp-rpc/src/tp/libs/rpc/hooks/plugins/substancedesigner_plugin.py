from __future__ import annotations

import substance_designer
from loguru import logger

from tp.libs.rpc.core.instances import unregister_instance
from tp.libs.rpc.api.interface import launch_server, stop_server
from tp.libs.rpc.hooks.shared_loader import load_all_shared_hooks
from tp.libs.rpc.core.mainthread import process_main_thread_queue

_runtime_state = {
    "instance_name": None,
    "dcc_type": "substancedesigner",
    "handles": {},
}


def initialize(
    host: str = "localhost", port: int = 0, instance_name: str | None = None
):
    """Start the Substance Designer RPC server.

    Args:
        host: Hostname to bind.
        port: Port to bind to.
        instance_name: Optional instance name for registry.
    """

    load_all_shared_hooks()
    logger.info(
        "[tp-rpc][substancedesigner] Starting Substance Designer RPC "
        "server..."
    )

    _start_tick_timer()

    # noinspection PyTypedDict
    _runtime_state["instance_name"] = launch_server(
        host=host,
        port=port,
        dcc_type="substancedesigner",
        instance_name=instance_name,
        additional_globals={"substance_designer": substance_designer},
    )

    _register_shutdown_callback()

    logger.info(
        f"[tp-rpc][substancedesigner] Registered as instance:"
        f" {_runtime_state['instance_name']}"
    )


def shutdown():
    """Shutdown the RPC server from Substance Designer."""

    try:
        stop_server()
        _stop_tick_timer()

        instance = _runtime_state["instance_name"]
        logger.info(
            f"[tp-rpc][substancedesigner] Stopping RPC server for "
            f"instance: {instance}"
        )
        if instance:
            unregister_instance(_runtime_state["dcc_type"], instance)
        logger.info(
            "[tp-rpc][substancedesigner] RPC server stopped and instance "
            "unregistered."
        )
    except Exception as e:
        logger.error(f"[tp-rpc][substancedesigner] Shutdown error: {e}")


def _start_tick_timer():
    """Starts a Qt timer to process the main-thread queue periodically."""
    if _runtime_state["handles"].get("SD_QT_TIMER"):
        _stop_tick_timer()

    try:
        from PySide2.QtCore import QTimer
        from PySide2.QtWidgets import QApplication

        app = QApplication.instance()
        if not app:
            logger.info(
                "[tp-rpc][substancedesigner] No QApplication instance found. "
                "Creating one."
            )
            app = QApplication([])

        timer = QTimer()
        timer.timeout.connect(process_main_thread_queue)
        timer.start(100)  # Tick every 100ms

        _runtime_state["handles"]["SD_QT_TIMER"] = timer

        logger.info(
            "[tp-rpc][substancedesigner] Qt timer for main-thread queue "
            "started."
        )

    except Exception as e:
        logger.error(
            f"[tp-rpc][substancedesigner] Failed to start Qt timer: {e}"
        )


def _stop_tick_timer():
    """Stops the Qt timer."""
    timer = _runtime_state["handles"].pop("SD_QT_TIMER", None)
    if timer:
        timer.stop()


def _register_shutdown_callback():
    """Register a shutdown callback using Qt's aboutToQuit signal."""
    try:
        from Qt.QtWidgets import QApplication

        app = QApplication.instance()
        if not app:
            logger.info(
                "[tp-rpc][substancedesigner] No QApplication instance found. "
                "Creating one."
            )
            app = QApplication([])

        app.aboutToQuit.connect(shutdown)
        logger.info(
            "[tp-rpc][substancedesigner] Connected to"
            " QApplication.aboutToQuit for shutdown."
        )
    except Exception as e:
        logger.warning(
            f"[tp-rpc][substancedesigner] Could not connect shutdown "
            f"callback: {e}"
        )
