from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tp.libs.rpc.api.interface import launch_server, call_remote_function
from tp.libs.rpc.core.instances import list_instances, cleanup_registry


@pytest.fixture
def mock_maya_server():
    """Start a mock Maya RPC server."""

    # Mock the Maya modules
    maya_mock = MagicMock()
    cmds_mock = MagicMock()
    utils_mock = MagicMock()
    mel_mock = MagicMock()

    with patch.dict(
        "sys.modules",
        {
            "maya": maya_mock,
            "maya.cmds": cmds_mock,
            "maya.utils": utils_mock,
            "maya.mel": mel_mock,
        },
    ):
        # Start the server
        instance_name = launch_server(
            host="localhost",
            port=0,  # Use any available port
            dcc_type="maya",
            instance_name="test_maya",
            additional_globals={
                "maya": maya_mock,
                "cmds": cmds_mock,
                "utils": utils_mock,
                "mel": mel_mock,
            },
        )

        # Register a test function
        call_remote_function(
            dcc_type="maya",
            instance_name="test_maya",
            function_name="register_remote_function",
            name="maya_test_func",
            source_code="""
def maya_test_func(value):
    return f"Maya processed: {value}"
            """,
        )

        yield instance_name

        # Clean up
        call_remote_function(
            dcc_type="maya",
            instance_name="test_maya",
            function_name="stop_rpc_server",
        )
        cleanup_registry()


@pytest.fixture
def mock_unreal_server():
    """Start a mock Unreal RPC server."""
    # Mock the Unreal module
    unreal_mock = MagicMock()

    with patch.dict("sys.modules", {"unreal": unreal_mock}):
        # Start the server
        instance_name = launch_server(
            host="localhost",
            port=0,  # Use any available port
            dcc_type="unreal",
            instance_name="test_unreal",
            additional_globals={"unreal": unreal_mock},
        )

        # Register a test function
        call_remote_function(
            dcc_type="unreal",
            instance_name="test_unreal",
            function_name="register_remote_function",
            name="unreal_test_func",
            source_code="""
def unreal_test_func(value):
    return f"Unreal processed: {value}"
            """,
        )

        yield instance_name

        # Clean up
        call_remote_function(
            dcc_type="unreal",
            instance_name="test_unreal",
            function_name="stop_rpc_server",
        )
        cleanup_registry()


def test_maya_to_unreal_communication(mock_maya_server, mock_unreal_server):
    """Test communication from Maya to Unreal."""

    # Get the Unreal URI
    instances = list_instances()
    assert "unreal" in instances
    assert "test_unreal" in instances["unreal"]

    # Register a function in Maya that calls Unreal
    call_remote_function(
        dcc_type="maya",
        instance_name="test_maya",
        function_name="register_remote_function",
        name="call_unreal",
        source_code="""
from tp.libs.rpc.api.interface import call_remote_function

def call_unreal(value):
    return call_remote_function(
        dcc_type="unreal",
        instance_name="test_unreal",
        function_name="unreal_test_func",
        value=value
    )
        """,
    )

    # Call the Maya function that calls Unreal
    result = call_remote_function(
        dcc_type="maya",
        instance_name="test_maya",
        function_name="call_unreal",
        value="test data",
    )

    assert result == "Unreal processed: test data"


def test_unreal_to_maya_communication(mock_maya_server, mock_unreal_server):
    """Test communication from Unreal to Maya."""

    # Register a function in Unreal that calls Maya
    call_remote_function(
        dcc_type="unreal",
        instance_name="test_unreal",
        function_name="register_remote_function",
        name="call_maya",
        source_code="""
from tp.libs.rpc.api.interface import call_remote_function

def call_maya(value):
    return call_remote_function(
        dcc_type="maya",
        instance_name="test_maya",
        function_name="maya_test_func",
        value=value
    )
        """,
    )

    # Call the Unreal function that calls Maya
    result = call_remote_function(
        dcc_type="unreal",
        instance_name="test_unreal",
        function_name="call_maya",
        value="test data",
    )

    assert result == "Maya processed: test data"
