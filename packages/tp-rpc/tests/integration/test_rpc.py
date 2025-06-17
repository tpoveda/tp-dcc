from __future__ import annotations

import time
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.api.interface import (
    launch_server,
    call_remote_function,
    register_function_remotely,
    remote_call,
)
from tp.libs.rpc.core.instances import cleanup_registry


@pytest.fixture
def test_server():
    """Start a test RPC server."""
    # Mock a generic module
    test_module = MagicMock()

    instance_name = launch_server(
        host="localhost",
        port=0,
        dcc_type="test",
        instance_name="rpc_test",
        additional_globals={"test_module": test_module},
    )

    yield instance_name

    # Clean up
    call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="stop_rpc_server",
    )
    cleanup_registry()


def test_basic_rpc_call(test_server):
    """Test basic RPC function call."""
    # Register a simple function
    call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="register_remote_function",
        name="add",
        source_code="""
def add(a, b):
    return a + b
        """,
    )

    # Call the function
    result = call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="add",
        a=5,
        b=7,
    )

    assert result == 12


def test_register_function_remotely(test_server):
    """Test registering a function remotely using register_function_remotely."""

    # Define a function locally
    def multiply(a, b):
        return a * b

    # Register it remotely
    register_function_remotely(
        func=multiply, dcc_type="test", instance_name="rpc_test"
    )

    # Call the function
    result = call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="multiply",
        a=6,
        b=7,
    )

    assert result == 42


def test_remote_call(test_server):
    """Test the remote_call function that registers and calls in one step."""

    # Define a function locally
    def subtract(a, b):
        return a - b

    # Register and call in one step
    result = remote_call(
        subtract, dcc_type="test", instance_name="rpc_test", a=5, b=3
    )

    assert result == 2

    # Verify the function was registered
    functions = call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="list_registered_functions",
    )

    assert "subtract" in functions


def test_complex_data_structures(test_server):
    """Test sending and receiving complex data structures."""
    # Register a function that manipulates complex data
    call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="register_remote_function",
        name="process_data",
        source_code="""
def process_data(data):
    if isinstance(data, dict):
        return {k.upper(): v * 2 for k, v in data.items()}
    elif isinstance(data, list):
        return [x * 2 for x in data]
    else:
        return data
        """,
    )

    # Test with dictionary
    dict_result = call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="process_data",
        data={"a": 1, "b": 2, "c": 3},
    )

    assert dict_result == {"A": 2, "B": 4, "C": 6}

    # Test with list
    list_result = call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="process_data",
        data=[1, 2, 3, 4, 5],
    )

    assert list_result == [2, 4, 6, 8, 10]


def test_error_handling(test_server):
    """Test error handling in RPC calls."""
    # Register a function that raises an exception
    call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="register_remote_function",
        name="error_function",
        source_code="""
def error_function(should_error=True):
    if should_error:
        raise ValueError("This is a test error")
    return "No error"
        """,
    )

    # Test successful call
    result = call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="error_function",
        should_error=False,
    )

    assert result == "No error"

    # Test error case
    with pytest.raises(Exception) as excinfo:
        call_remote_function(
            dcc_type="test",
            instance_name="rpc_test",
            function_name="error_function",
            should_error=True,
        )

    assert "This is a test error" in str(excinfo.value)


def test_batch_call(test_server):
    """Test batch call functionality."""
    # Register some test functions
    call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="register_remote_function",
        name="add",
        source_code="""
def add(a, b):
    return a + b
        """,
    )

    call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="register_remote_function",
        name="multiply",
        source_code="""
def multiply(a, b):
    return a * b
        """,
    )

    call_remote_function(
        dcc_type="test",
        instance_name="rpc_test",
        function_name="register_remote_function",
        name="error_func",
        source_code="""
def error_func():
    raise ValueError("Test error")
        """,
    )

    # Create a client directly to use batch_call
    from tp.libs.rpc.core.client import RPCClient
    from tp.libs.rpc.core.instances import get_uri

    uri = get_uri("test", "rpc_test")
    client = RPCClient(uri)

    try:
        # Prepare batch calls
        calls = [
            {"function": "add", "args": [1, 2]},
            {"function": "multiply", "args": [3, 4]},
            {"function": "error_func"},
        ]

        # Execute batch call
        results = client.batch_call(calls)

        # Verify results
        assert len(results) == 3
        assert results[0]["status"] == "success"
        assert results[0]["result"] == 3
        assert results[1]["status"] == "success"
        assert results[1]["result"] == 12
        assert results[2]["status"] == "error"
        assert "Test error" in results[2]["error"]
    finally:
        client.close()
