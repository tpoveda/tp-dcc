from __future__ import annotations

import time
import threading
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.api.interface import launch_server, call_remote_function
from tp.libs.rpc.core.instances import list_instances, cleanup_registry


@pytest.fixture
def cleanup():
    """Clean up registry before and after tests."""
    cleanup_registry()
    yield
    cleanup_registry()


def test_multiple_maya_instances(cleanup):
    """Test running multiple Maya instances simultaneously."""
    # Mock the Maya modules
    maya_mock = MagicMock()

    with patch.dict("sys.modules", {"maya": maya_mock}):
        # Start three Maya instances
        instance_names = []
        for i in range(3):
            name = f"maya-test-{i}"
            instance_name = launch_server(
                host="localhost",
                port=0,
                dcc_type="maya",
                instance_name=name,
                additional_globals={"maya": maya_mock},
            )
            instance_names.append(instance_name)

            # Register a test function on each instance
            call_remote_function(
                dcc_type="maya",
                instance_name=name,
                function_name="register_remote_function",
                name=f"test_func_{i}",
                source_code=f"""
def test_func_{i}():
    return "Instance {i}"
                """,
            )

        # Verify all instances are registered
        instances = list_instances("maya")
        for name in instance_names:
            assert name in instances["maya"]

        # Call functions on each instance
        for i, name in enumerate(instance_names):
            result = call_remote_function(
                dcc_type="maya",
                instance_name=name,
                function_name=f"test_func_{i}",
            )
            assert result == f"Instance {i}"

        # Clean up
        for name in instance_names:
            call_remote_function(
                dcc_type="maya",
                instance_name=name,
                function_name="stop_rpc_server",
            )


def test_mixed_dcc_instances(cleanup):
    """Test running multiple different DCC instances simultaneously."""
    # Mock the DCC modules
    maya_mock = MagicMock()
    unreal_mock = MagicMock()
    blender_mock = MagicMock()

    with patch.dict(
        "sys.modules",
        {"maya": maya_mock, "unreal": unreal_mock, "bpy": blender_mock},
    ):
        # Start one instance of each DCC type
        instances = {
            "maya": launch_server(
                host="localhost",
                port=0,
                dcc_type="maya",
                instance_name="maya-test",
                additional_globals={"maya": maya_mock},
            ),
            "unreal": launch_server(
                host="localhost",
                port=0,
                dcc_type="unreal",
                instance_name="unreal-test",
                additional_globals={"unreal": unreal_mock},
            ),
            "blender": launch_server(
                host="localhost",
                port=0,
                dcc_type="blender",
                instance_name="blender-test",
                additional_globals={"bpy": blender_mock},
            ),
        }

        # Register a test function on each instance
        for dcc_type, instance_name in instances.items():
            call_remote_function(
                dcc_type=dcc_type,
                instance_name=instance_name,
                function_name="register_remote_function",
                name="identify",
                source_code=f"""
def identify():
    return "{dcc_type}"
                """,
            )

        # Verify all instances are registered
        all_instances = list_instances()
        for dcc_type, instance_name in instances.items():
            assert dcc_type in all_instances
            assert instance_name in all_instances[dcc_type]

        # Call functions on each instance
        for dcc_type, instance_name in instances.items():
            result = call_remote_function(
                dcc_type=dcc_type,
                instance_name=instance_name,
                function_name="identify",
            )
            assert result == dcc_type

        # Clean up
        for dcc_type, instance_name in instances.items():
            call_remote_function(
                dcc_type=dcc_type,
                instance_name=instance_name,
                function_name="stop_rpc_server",
            )
