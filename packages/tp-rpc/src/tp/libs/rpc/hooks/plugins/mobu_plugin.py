from __future__ import annotations

import pyfbsdk as fb
from loguru import logger

from tp.libs.rpc.core.instances import unregister_instance
from tp.libs.rpc.api.interface import launch_server, stop_server
from tp.libs.rpc.hooks.shared_loader import load_all_shared_hooks
from tp.libs.rpc.core.mainthread import process_main_thread_queue

_runtime_state = {
    "instance_name": None,
    "dcc_type": "unreal",
    "handles": {},
}


def initialize(
    host: str = "localhost", port: int = 0, instance_name: str | None = None
):
    """Start the MotionBuilder RPC server.

    Args:
        host: Hostname to bind.
        port: Port to bind to.
        instance_name: Optional instance name for registry.
    """

    load_all_shared_hooks()
    logger.info(
        "[tp-rpc][motionbuilder] Starting MotionBuilder RPC server..."
    )

    _start_idle_loop()

    # noinspection PyTypedDict
    _runtime_state["instance_name"] = launch_server(
        host=host,
        port=port,
        dcc_type="mobu",
        instance_name=instance_name,
        additional_globals={
            "fb": fb,
            "pyfbsdk": fb,
        },
    )

    _register_shutdown_callback()

    logger.info(
        f"[tp-rpc][motionbuilder] Registered as instance:"
        f" {_runtime_state['instance_name']}"
    )


def shutdown():
    """MotionBuilder shutdown hook (not implemented)."""

    try:
        stop_server()
        _unregister_idle_callback()

        instance = _runtime_state["instance_name"]
        logger.info(
            f"[tp-rpc][motionbuilder] Stopping RPC server for "
            f"instance: {instance}"
        )
        if instance:
            unregister_instance(_runtime_state["dcc_type"], instance)
        logger.info(
            "[tp-rpc][motionbuilder] RPC server stopped and instance "
            "unregistered."
        )
    except Exception as e:
        logger.error(f"[tp-rpc][motionbuilder] Shutdown error: {e}")


def _start_idle_loop():
    """Internal function that registers an idle callback to process the
    main-thread queue.
    """

    if _runtime_state["handles"].get("MOBU_IDLE_CALLBACK"):
        _unregister_idle_callback()

    # Use FBSystem.OnUIIdle to process main thread queue.
    def _on_idle(control, event):
        process_main_thread_queue()

    fb.FBSystem().OnUIIdle.Add(_on_idle)
    _runtime_state["handles"]["MOBU_IDLE_CALLBACK"] = _on_idle

    logger.info(
        "[tp-rpc][motionbuilder] Main-thread queue idle callback registered."
    )


def _unregister_idle_callback():
    """Internal function that removes the idle callback."""

    cb = _runtime_state["handles"].pop("MOBU_IDLE_CALLBACK", None)
    if cb:
        fb.FBSystem().OnUIIdle.Remove(cb)


def _register_shutdown_callback():
    """Register a shutdown callback using Qt's aboutToQuit signal."""
    try:
        from Qt.QtWidgets import QApplication

        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(shutdown)
            logger.info(
                "[tp-rpc][motionbuilder] Connected to "
                "QApplication.aboutToQuit for shutdown."
            )
        else:
            logger.warning(
                "[tp-rpc][motionbuilder] No QApplication instance found."
            )
    except Exception as e:
        logger.warning(
            f"[tp-rpc][motionbuilder] Could not connect shutdown callback: {e}"
        )
