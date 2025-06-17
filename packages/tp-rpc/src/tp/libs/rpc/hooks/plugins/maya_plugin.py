from __future__ import annotations

import atexit

import maya
from typing import Any
from loguru import logger
from maya import mel, cmds, utils

from tp.libs.rpc.core.instances import unregister_instance
from tp.libs.rpc.api.interface import launch_server, stop_server
from tp.libs.rpc.hooks.shared_loader import load_all_shared_hooks
from tp.libs.rpc.core.mainthread import process_main_thread_queue
from tp.libs.rpc.hooks.plugin_interface import DCCPluginInterface


class MayaPlugin(DCCPluginInterface):
    """Maya implementation of the DCC plugin interface."""

    DCC_TYPE = "maya"
    SUPPORTS_THREADING = True

    def __init__(self):
        """Initialize the Maya plugin."""

        self._instance_name = None

    def initialize(
        self,
        host: str = "localhost",
        port: int = 0,
        instance_name: str | None = None,
    ) -> str:
        """Initialize the Maya RPC server.

        Args:
            host: Host address to bind the server to.
            port: Port to bind the server to.
            instance_name: Optional instance name for registry.

        Returns:
            The registered instance name.
        """

        load_all_shared_hooks()
        logger.info("[tp-rpc][maya] Launching RPC server...")

        self.register_shutdown_hook()
        self.setup_main_thread_execution()

        self._instance_name = launch_server(
            host=host,
            port=port,
            dcc_type=self.DCC_TYPE,
            instance_name=instance_name,
            additional_globals=self.get_dcc_globals(),
        )

        logger.info(
            f"[tp-rpc][maya] Registered as instance: {self._instance_name}"
        )

        return self._instance_name

    def shutdown(self) -> None:
        """Shutdown the RPC server and clean up resources."""

        try:
            stop_server()
            logger.info(
                f"[tp-rpc][maya] Stopping RPC server for "
                f"instance: {self._instance_name}"
            )
            if self._instance_name:
                unregister_instance(self.DCC_TYPE, self._instance_name)
            logger.info(
                "[tp-rpc][maya] RPC server stopped and instance unregistered."
            )
        except Exception as e:
            logger.error(f"[tp-rpc][maya] Shutdown error: {e}")

    def setup_main_thread_execution(self) -> None:
        """Set up the mechanism for executing code in Maya's main thread."""

        try:

            def loop():
                """This function is called in a deferred manner to process the
                main thread queue.
                """
                try:
                    process_main_thread_queue()
                finally:
                    utils.executeDeferred(loop)

            utils.executeDeferred(loop)
            logger.info(
                "[tp-rpc][maya] Started main-thread loop via deferred execution"
            )

        except Exception as err:
            logger.error(
                f"[tp-rpc][maya] Failed to start main-thread queue loop: {err}"
            )

    def register_shutdown_hook(self) -> None:
        """Register a hook to be called when Maya is shutting down."""
        atexit.register(self.shutdown)

        try:
            cmds.scriptJob(
                event=["quitApplication", self.shutdown],
                runOnce=True,
                killWithScene=True,
            )
        except Exception as e:
            logger.error(
                f"[tp-rpc][maya] Failed to attach shutdown hook: {e}"
            )

    def get_dcc_globals(self) -> dict[str, Any]:
        """Get Maya-specific globals to inject into the RPC server.

        Returns:
            Dictionary of Maya modules to inject.
        """
        return {
            "maya": maya,
            "cmds": cmds,
            "utils": utils,
            "mel": mel,
        }


# Create a singleton instance
_maya_plugin = MayaPlugin()


# Expose the initialize and shutdown functions at the module level for
# backward compatibility
def initialize(
    host: str = "localhost", port: int = 0, instance_name: str | None = None
) -> str:
    """Initialize the Maya RPC server (backward compatibility function)."""
    return _maya_plugin.initialize(host, port, instance_name)


def shutdown() -> None:
    """Shutdown the Maya RPC server (backward compatibility function)."""
    _maya_plugin.shutdown()


_runtime_state = {
    "instance_name": None,
    "dcc_type": "maya",
}
