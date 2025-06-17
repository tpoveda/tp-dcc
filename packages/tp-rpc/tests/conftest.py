from __future__ import annotations

import time
import threading
from types import ModuleType

import pytest
from loguru import logger

from tp.libs.rpc.core.instances import list_instances, clear_dcc_instances


@pytest.fixture(autouse=True)
def clean_registry():
    """Automatically clear all 'maya' instances before and after each test."""

    clear_dcc_instances("maya")
    yield
    clear_dcc_instances("maya")


def run_dcc_server_test(
    dcc_module: ModuleType, dcc_name: str, delay: float = 1.0
):
    """Launch a DCC RPC server in a background thread and verify it's
    registered.

    This function is used by all DCC hook tests (e.g. Maya, Unreal, Houdini)
    to validate that the server starts and registers correctly.

    Args:
        dcc_module: The imported DCC hook module (e.g., dcc_hooks.maya).
        dcc_name : The lowercase DCC identifier (e.g., "maya", "unreal").
        delay: Optional number of seconds to wait before checking registry.
    """

    # Ensure the registry is clean before the test
    clear_dcc_instances(dcc_name)

    # Launch the server in a background thread
    thread = threading.Thread(
        target=dcc_module.initialize, kwargs={"port": 0}, daemon=True
    )
    thread.start()

    # Wait for it to spin up
    time.sleep(delay)

    # Verify it registered successfully
    instances = list_instances(dcc_name).get(dcc_name, {})
    assert len(instances) >= 1, (
        f"Expected at least one registered {dcc_name} instance."
    )

    logger.info(f"[{dcc_name}] registered instances:", instances)

    # Clean up after test
    clear_dcc_instances(dcc_name)
