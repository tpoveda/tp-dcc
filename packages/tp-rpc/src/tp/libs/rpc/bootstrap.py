"""Auto-bootstrap the correct DCC RPC server based on runtime environment."""

from __future__ import annotations

import os
import sys
import importlib
import threading

from loguru import logger

# Mapping of known DCC environments to their module.
DCC_ENV_MAP = {
    "maya": {
        "check": lambda: "MAYA_APP_DIR" in os.environ
        or "maya" in sys.executable.lower(),
        "hook": "tp.libs.rpc.hooks.plugins.maya_plugin",
        "thread_safe": True,
    },
    "unreal": {
        "check": lambda: "ue" in sys.executable.lower()
        or "unreal" in sys.executable.lower(),
        "hook": "tp.libs.rpc.hooks.plugins.unreal_plugin",
        "thread_safe": False,  # Cannot initialize from a background thread.
    },
    "motionbuilder": {
        "check": lambda: "motionbuilder" in sys.executable.lower(),
        "hook": "tp.libs.rpc.hooks.plugins.motionbuilder_plugin",
        "thread_safe": True,
    },
    "houdini": {
        "check": lambda: "houdini" in sys.executable.lower(),
        "hook": "tp.libs.rpc.hooks.plugins.houdini_plugin",
        "thread_safe": True,
    },
    "substancepainter": {
        "check": lambda: "substancepainter" in sys.executable.lower(),
        "hook": "tp.libs.rpc.hooks.plugins.substancepainter_plugin",
        "thread_safe": True,
    },
    "substancedesigner": {
        "check": lambda: "substancedesigner" in sys.executable.lower(),
        "hook": "tp.libs.rpc.hooks.plugins.substancedesigner_plugin",
        "thread_safe": True,
    },
}


def detect_dcc() -> str | None:
    """Detect the active DCC based on environment or process.

    Returns:
        The detected DCC type (e.g., "maya", "unreal"); None if not found.
    """

    for dcc, config in DCC_ENV_MAP.items():
        if config["check"]():
            return dcc

    return None


def threaded_initialize(dcc_type: str, port: int, instance_name: str | None = None):
    """Initialize the RPC server in a separate thread.

    Args:
        dcc_type: The type of DCC (e.g., "maya", "unreal").
        port: The port to use for the RPC server.
        instance_name: The name of the instance to connect to (optional).
    """

    # noinspection PyBroadException
    try:
        config = DCC_ENV_MAP[dcc_type]
        hook = importlib.import_module(DCC_ENV_MAP[dcc_type]["hook"])

        # If this DCC supports thread-based boot:
        if config.get("thread_safe", False):
            logger.info(
                f"[tp-rpc][bootstrap] Starting {dcc_type} RPC server in "
                f"background thread."
            )
            thread = threading.Thread(
                target=hook.initialize,
                kwargs={"port": port, "instance_name": instance_name},
                name=f"tp_dcc_rpc_{dcc_type}_server",
                daemon=True,
            )
            thread.start()
            logger.info(
                f"[tp-rpc][bootstrap] Started {dcc_type} RPC server in "
                f"background thread."
            )
        else:
            logger.info(
                f"[tp-rpc][bootstrap] Starting {dcc_type} RPC server in "
                f"main thread (threading not supported)."
            )
            hook.initialize(port=port, instance_name=instance_name)
    except Exception as err:
        logger.error(f"[tp-rpc][bootstrap] Failed to initialize {dcc_type} RPC: {err}")


def initialize_rpc():
    """Auto-initialize the RPC server for the current DCC context.

    Optionally supports:
    - TP_DCC_RPC_PORT (int)
    - TP_DCC_RPC_INSTANCE (str)
    """

    dcc_type = detect_dcc()
    if not dcc_type:
        logger.info("[tp-rpc][bootstrap] No supported DCC detected.")
        return

    port = int(os.getenv("TP_DCC_RPC_PORT", "0"))
    instance_name = os.getenv("TP_DCC_RPC_INSTANCE", None)

    threaded_initialize(dcc_type, port, instance_name)


# Run on import
initialize_rpc()
