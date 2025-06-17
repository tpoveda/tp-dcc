from __future__ import annotations

import time
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


def test_auto_instance_naming(cleanup):
    """Test that instances are automatically named when no name is provided."""
    # Mock the Maya modules
    maya_mock = MagicMock()

    with patch.dict("sys.modules", {"maya": maya_mock}):
        # Start the first server without specifying an instance name
        instance_name1 = launch_server(
            host="localhost",
            port=0,
            dcc_type="maya",
            additional_globals={"maya": maya_mock},
        )

        # Start a second server without specifying an instance name
        instance_name2 = launch_server(
            host="localhost",
            port=0,
            dcc_type="maya",
            additional_globals={"maya": maya_mock},
        )

        # Verify that unique names were generated
        assert instance_name1 != instance_name2
        assert instance_name1.startswith("maya-")
        assert instance_name2.startswith("maya-")

        # Verify both instances are registered
        instances = list_instances("maya")
        assert instance_name1 in instances["maya"]
        assert instance_name2 in instances["maya"]

        # Clean up
        call_remote_function(
            dcc_type="maya",
            instance_name=instance_name1,
            function_name="stop_rpc_server",
        )

        call_remote_function(
            dcc_type="maya",
            instance_name=instance_name2,
            function_name="stop_rpc_server",
        )


def test_explicit_instance_naming(cleanup):
    """Test that explicitly named instances use the provided name."""
    # Mock the Maya modules
    maya_mock = MagicMock()

    with patch.dict("sys.modules", {"maya": maya_mock}):
        # Start a server with an explicit instance name
        explicit_name = "my-custom-maya"
        instance_name = launch_server(
            host="localhost",
            port=0,
            dcc_type="maya",
            instance_name=explicit_name,
            additional_globals={"maya": maya_mock},
        )

        # Verify the name was used
        assert instance_name == explicit_name

        # Verify the instance is registered
        instances = list_instances("maya")
        assert explicit_name in instances["maya"]

        # Clean up
        call_remote_function(
            dcc_type="maya",
            instance_name=explicit_name,
            function_name="stop_rpc_server",
        )
