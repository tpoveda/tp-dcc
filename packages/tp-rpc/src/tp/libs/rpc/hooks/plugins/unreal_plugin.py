from __future__ import annotations

import unreal
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
    """Start the Unreal Engine RPC server.

    Warnings:
        This should only be called from Unreal's main/game thread.

    Args:
        host: Hostname to bind.
        port: Port to bind to.
        instance_name: Optional instance name for registry.
    """

    load_all_shared_hooks()
    logger.info("[tp-rpc][unreal] Starting Unreal RPC server...")

    _start_post_tick_loop()

    # noinspection PyTypedDict
    _runtime_state["instance_name"] = launch_server(
        host=host,
        port=port,
        dcc_type="unreal",
        instance_name=instance_name,
        additional_globals={"unreal": unreal},
    )

    _register_python_shutdown_callback()

    logger.info(
        f"[tp-rpc][unreal] Registered as instance:"
        f" {_runtime_state['instance_name']}"
    )


def shutdown():
    """Shutdown the RPC server from Unreal."""

    try:
        stop_server()
        _unregister_tick_callback()

        instance = _runtime_state["instance_name"]
        logger.info(
            f"[tp-rpc][maya] Stopping RPC server for instance: {instance}"
        )
        if instance:
            unregister_instance(_runtime_state["dcc_type"], instance)
        logger.info(
            "[tp-rpc][unreal] RPC server stopped and instance unregistered."
        )
    except Exception as e:
        logger.error(f"[tp-rpc][unreal] Shutdown error: {e}")


def _start_post_tick_loop():
    """Internal function that register Unreal tick callback to process the
    main-thread queue.
    """

    if _runtime_state["handles"].get("UNREAL_POST_TICK_DELEGATE_HANDLE"):
        _unregister_tick_callback()

    handle = unreal.register_slate_post_tick_callback(
        process_main_thread_queue
    )
    _runtime_state["handles"]["UNREAL_POST_TICK_DELEGATE_HANDLE"] = handle

    logger.info("[tp-rpc][unreal] Main-thread queue tick registered.")


def _unregister_tick_callback():
    """Internal function that unregister Unreal's tick callback.

    This function is called when the server is stopped.
    """

    handle = _runtime_state["handles"].pop(
        "UNREAL_POST_TICK_DELEGATE_HANDLE", None
    )
    if handle:
        unreal.unregister_slate_post_tick_callback(handle)


def _register_python_shutdown_callback():
    """Internal function that register Unreal's Python shutdown callback to
    clean up the RPC server.
    """

    try:
        unreal.register_python_shutdown_callback(shutdown)
        logger.info("[tp-rpc][unreal] Registered shutdown callback.")
    except Exception as e:
        logger.warning(
            f"[tp-rpc][unreal] Could not register shutdown callback: {e}"
        )
