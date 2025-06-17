from __future__ import annotations

from loguru import logger

from tp.libs.rpc.api.interface import launch_server
from tp.libs.rpc.api.decorators import register_function


@register_function()
def echo_blender(text: str) -> str:
    """Remote function for Blender.

    Args:
        text: Input string.

    Returns:
        Blender-identified echo message.
    """

    return f"[Blender] {text}"


def initialize(
    host: str = "localhost", port: int = 0, instance_name: str | None = None
):
    """Start the Blender RPC server.

    Args:
        host: Host IP or hostname.
        port: Port number.
        instance_name: Instance name to register.
    """

    logger.info("[tp-rpc][blender] Starting Blender RPC server...")

    launch_server(
        host=host, port=port, dcc_type="blender", instance_name=instance_name
    )


def shutdown():
    """Blender shutdown logic (unimplemented)."""

    logger.info("[tp-rpc][blender] Shutdown hook not implemented.")
