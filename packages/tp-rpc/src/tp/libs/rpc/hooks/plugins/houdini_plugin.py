from __future__ import annotations

import hou
from loguru import logger

from tp.libs.rpc.core.instances import unregister_instance
from tp.libs.rpc.api.interface import launch_server, stop_server
from tp.libs.rpc.hooks.shared_loader import load_all_shared_hooks
from tp.libs.rpc.core.mainthread import process_main_thread_queue

_runtime_state = {
    "instance_name": None,
    "dcc_type": "houdini",
    "handles": {},
}


def initialize(
    host: str = "localhost", port: int = 0, instance_name: str | None = None
):
    """Start the Houdini RPC server.

    Args:
        host: Hostname to bind.
        port: Port to bind to.
        instance_name: Optional instance name for registry.
    """

    load_all_shared_hooks()
    logger.info("[tp-rpc][houdini] Starting Houdini RPC server...")

    _start_event_loop_callback()

    # noinspection PyTypedDict
    _runtime_state["instance_name"] = launch_server(
        host=host,
        port=port,
        dcc_type="houdini",
        instance_name=instance_name,
        additional_globals={"hou": hou},
    )

    _register_shutdown_callback()

    logger.info(
        f"[tp-rpc][houdini] Registered as instance:"
        f" {_runtime_state['instance_name']}"
    )


def shutdown():
    """Houdini shutdown hook (not implemented)."""

    try:
        stop_server()
        _unregister_event_loop_callback()

        instance = _runtime_state["instance_name"]
        logger.info(
            f"[tp-rpc][houdini] Stopping RPC server for instance: {instance}"
        )
        if instance:
            unregister_instance(_runtime_state["dcc_type"], instance)
        logger.info(
            "[tp-rpc][houdini] RPC server stopped and instance unregistered."
        )
    except Exception as e:
        logger.error(f"[tp-rpc][houdini] Shutdown error: {e}")


def _start_event_loop_callback():
    """Internal function that registers an event loop callback to process
    the main-thread queue.
    """

    if _runtime_state["handles"].get("HOUDINI_EVENT_CALLBACK"):
        _unregister_event_loop_callback()

    def _on_event_loop():
        process_main_thread_queue()

    hou.ui.addEventLoopCallback(_on_event_loop)
    _runtime_state["handles"]["HOUDINI_EVENT_CALLBACK"] = _on_event_loop

    logger.info(
        "[tp-rpc][houdini] Main-thread queue event loop callback registered."
    )


def _unregister_event_loop_callback():
    """Internal function that removes the event loop callback."""

    cb = _runtime_state["handles"].pop("HOUDINI_EVENT_CALLBACK", None)
    if cb:
        try:
            hou.ui.removeEventLoopCallback(cb)
        except Exception as e:
            logger.warning(
                f"[tp-rpc][houdini] Could not remove event loop callback: {e}"
            )


def _register_shutdown_callback():
    """Register a shutdown callback using Qt's aboutToQuit or mainWindow
    close.
    """
    try:
        main_window = hou.qt.mainWindow()
        if main_window:
            main_window.destroyed.connect(shutdown)
            logger.info(
                "[tp-rpc][houdini] Connected to mainWindow.destroyed for "
                "shutdown."
            )
        else:
            logger.warning("[tp-rpc][houdini] Could not get mainWindow.")

    except Exception as e:
        logger.warning(
            f"[tp-rpc][houdini] Could not connect shutdown callback: {e}"
        )
