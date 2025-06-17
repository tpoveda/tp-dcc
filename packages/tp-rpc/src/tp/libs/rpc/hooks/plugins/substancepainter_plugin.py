from __future__ import annotations

import substance_painter
from loguru import logger

from tp.libs.rpc.core.instances import unregister_instance
from tp.libs.rpc.api.interface import launch_server, stop_server
from tp.libs.rpc.hooks.shared_loader import load_all_shared_hooks
from tp.libs.rpc.core.mainthread import process_main_thread_queue

_runtime_state = {
    "instance_name": None,
    "dcc_type": "substancepainter",
    "handles": {},
}


def initialize(
    host: str = "localhost", port: int = 0, instance_name: str | None = None
):
    """Start the Substance Painter RPC server.

    Args:
        host: Hostname to bind.
        port: Port to bind to.
        instance_name: Optional instance name for registry.
    """

    load_all_shared_hooks()
    logger.info(
        "[tp-rpc][substancepainter] Starting Substance Painter RPC server..."
    )

    _start_tick_timer()

    # noinspection PyTypedDict
    _runtime_state["instance_name"] = launch_server(
        host=host,
        port=port,
        dcc_type="substancepainter",
        instance_name=instance_name,
        additional_globals={"substance_painter": substance_painter},
    )

    _register_shutdown_callback()

    logger.info(
        f"[tp-rpc][substancepainter] Registered as instance:"
        f" {_runtime_state['instance_name']}"
    )


def shutdown():
    """Shutdown the RPC server from Substance Painter."""

    try:
        stop_server()
        _stop_tick_timer()

        instance = _runtime_state["instance_name"]
        logger.info(
            f"[tp-rpc][substancepainter] Stopping RPC server for instance: {instance}"
        )
        if instance:
            unregister_instance(_runtime_state["dcc_type"], instance)
        logger.info(
            "[tp-rpc][substancepainter] RPC server stopped and instance unregistered."
        )
    except Exception as e:
        logger.error(f"[tp-rpc][substancepainter] Shutdown error: {e}")


def _start_tick_timer():
    """Internal function that starts a Qt timer to process the main-thread
    queue periodically.
    """

    if _runtime_state["handles"].get("SP_QT_TIMER"):
        _stop_tick_timer()

    try:
        from Qt.QtCore import QTimer
        from Qt.QtWidgets import QApplication

        app = QApplication.instance()
        if not app:
            logger.error(
                "[tp-rpc][substancepainter] No QApplication instance found."
            )
            return

        timer = QTimer()
        timer.timeout.connect(process_main_thread_queue)
        timer.start(100)  # Tick every 100ms

        _runtime_state["handles"]["SP_QT_TIMER"] = timer

        logger.info(
            "[tp-rpc][substancepainter] Qt timer for main-thread queue "
            "started."
        )

    except Exception as e:
        logger.error(
            f"[tp-rpc][substancepainter] Failed to start Qt timer: {e}"
        )


def _stop_tick_timer():
    """Internal function that stops the Qt timer."""

    timer = _runtime_state["handles"].pop("SP_QT_TIMER", None)
    if timer:
        timer.stop()


def _register_shutdown_callback():
    """Internal function that register a shutdown callback using Qt's
    aboutToQuit signal.
    """

    try:
        from Qt.QtWidgets import QApplication

        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(shutdown)
            logger.info(
                "[tp-rpc][substancepainter] Connected to "
                "QApplication.aboutToQuit for shutdown."
            )
        else:
            logger.warning(
                "[tp-rpc][substancepainter] No QApplication instance found."
            )
    except Exception as e:
        logger.warning(
            f"[tp-rpc][substancepainter] Could not connect shutdown "
            f"callback: {e}"
        )
