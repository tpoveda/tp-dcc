from __future__ import annotations

import os
import sys
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.api.interface import (
    launch_server,
    stop_server,
    call_remote_function,
    remote_call,
    extract_dependency_paths,
    register_function_remotely,
    ping_instance,
    describe_remote_function,
    list_remote_functions,
)


@pytest.fixture
def mock_client():
    """Mock RPCClient."""

    with patch("tp.libs.rpc.api.interface.RPCClient") as mock:
        client_instance = MagicMock()
        mock.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_server():
    """Mock server functions."""

    with patch("tp.libs.rpc.api.interface.start_server") as mock_start:
        with patch("tp.libs.rpc.api.interface.shutdown_server") as mock_stop:
            mock_start.return_value = "test-instance"
            yield mock_start, mock_stop


def test_launch_server(mock_server):
    """Test launching a server."""

    mock_start, _ = mock_server

    result = launch_server(
        host="testhost",
        port=9999,
        dcc_type="test",
        instance_name="test-instance",
        additional_globals={"test_module": MagicMock()},
    )

    mock_start.assert_called_once_with(
        host="testhost",
        port=9999,
        dcc_type="test",
        instance_name="test-instance",
        additional_globals={
            "test_module": mock_start.call_args[1]["additional_globals"][
                "test_module"
            ]
        },
    )
    assert result == "test-instance"


def test_stop_server(mock_server):
    """Test stopping a server."""

    _, mock_stop = mock_server

    stop_server()

    mock_stop.assert_called_once()


def test_call_remote_function_with_uri(mock_client):
    """Test calling a remote function with URI."""

    mock_client.call.return_value = 42

    result = call_remote_function(
        uri="PYRO:test@localhost:9999",
        function_name="test_function",
        arg1=1,
        arg2=2,
    )

    mock_client.call.assert_called_once_with("test_function", arg1=1, arg2=2)
    mock_client.close.assert_called_once()
    assert result == 42


def test_call_remote_function_with_dcc_type(mock_client):
    """Test calling a remote function with DCC type."""

    mock_client.call.return_value = 42

    with patch(
        "tp.libs.rpc.api.interface.get_uri",
        return_value="PYRO:test@localhost:9999",
    ):
        result = call_remote_function(
            dcc_type="maya",
            instance_name="maya-1",
            function_name="test_function",
            arg1=1,
            arg2=2,
        )

        mock_client.call.assert_called_once_with(
            "test_function", arg1=1, arg2=2
        )
        mock_client.close.assert_called_once()
        assert result == 42


def test_call_remote_function_no_uri_or_dcc():
    """Test calling a remote function with no URI or DCC type."""

    with pytest.raises(
        ValueError, match="You must provide either a URI or a DCC type"
    ):
        call_remote_function(function_name="test_function")


def test_call_remote_function_no_instance_found():
    """Test calling a remote function with no instance found."""

    with patch("tp.libs.rpc.api.interface.get_uri", return_value=None):
        with pytest.raises(ValueError, match="No registered instance found"):
            call_remote_function(
                dcc_type="maya",
                instance_name="maya-1",
                function_name="test_function",
            )


def test_call_remote_function_no_function_name():
    """Test calling a remote function with no function name."""

    with pytest.raises(ValueError, match="Function name is required"):
        call_remote_function(
            uri="PYRO:test@localhost:9999", function_name=None
        )


def test_remote_call():
    """Test remote_call function."""

    def test_func(a, b):
        return a + b

    with patch(
        "tp.libs.rpc.api.interface.register_function_remotely"
    ) as mock_register:
        with patch(
            "tp.libs.rpc.api.interface.call_remote_function", return_value=42
        ) as mock_call:
            result = remote_call(test_func, "maya", "maya-1", 1, 2)

            mock_register.assert_called_once_with(
                func=test_func, dcc_type="maya", instance_name="maya-1"
            )
            mock_call.assert_called_once_with(
                dcc_type="maya",
                instance_name="maya-1",
                function_name="test_func",
                a=1,
                b=2,
            )
            assert result == 42


def test_extract_dependency_paths():
    """Test extracting dependency paths from a function."""

    def test_func():
        import sys
        from pathlib import Path

        return os.path.join(sys.path[0], str(Path.home()))

    with patch("importlib.util.find_spec") as mock_find_spec:
        # Mock the spec for os module
        os_spec = MagicMock()
        os_spec.origin = "/path/to/os.py"

        # Mock the spec for sys module
        sys_spec = MagicMock()
        sys_spec.origin = "/path/to/sys.py"

        # Mock the spec for pathlib module
        pathlib_spec = MagicMock()
        pathlib_spec.origin = "/path/to/pathlib/__init__.py"

        # Set up the side effect to return different specs for different modules
        def side_effect(name):
            if name == "os":
                return os_spec
            elif name == "sys":
                return sys_spec
            elif name == "pathlib":
                return pathlib_spec
            return None

        mock_find_spec.side_effect = side_effect

        paths = extract_dependency_paths(test_func)

        # Should include paths for os, sys, and pathlib
        assert len(paths) == 3
        assert "/path/to" in paths


def test_register_function_remotely(mock_client):
    """Test registering a function remotely."""

    def test_func(a, b):
        return a + b

    mock_client.call.return_value = {"status": "success"}

    with patch(
        "tp.libs.rpc.api.interface.extract_dependency_paths",
        return_value=["/path/to/deps"],
    ):
        result = register_function_remotely(
            func=test_func, dcc_type="maya", instance_name="maya-1"
        )

        # Check that the client call was made with the right arguments
        mock_client.call.assert_called_once()
        call_args = mock_client.call.call_args[0]
        call_kwargs = mock_client.call.call_args[1]

        assert call_args[0] == "register_remote_function"
        assert call_kwargs["name"] == "test_func"
        assert "source_code" in call_kwargs
        assert call_kwargs["client_paths"] == ["/path/to/deps"] + sys.path

        assert result == {"status": "success"}


def test_register_function_remotely_not_callable():
    """Test registering a non-callable object remotely."""
    with pytest.raises(TypeError, match="Provided object is not a function"):
        register_function_remotely(
            func="not_a_function", dcc_type="maya", instance_name="maya-1"
        )


def test_ping_instance(mock_client):
    """Test pinging an instance."""
    mock_client.call.return_value = {
        "dcc_type": "maya",
        "instance_name": "maya-1",
        "hostname": "testhost",
        "platform": "Windows",
    }

    result = ping_instance("maya", "maya-1")

    mock_client.call.assert_called_once_with("ping")
    assert result["dcc_type"] == "maya"
    assert result["instance_name"] == "maya-1"


def test_describe_remote_function(mock_client):
    """Test describing a remote function."""
    mock_client.call.return_value = {
        "found": True,
        "signature": "test_func(a: int, b: str) -> bool",
        "doc": "Test function docstring.",
    }

    result = describe_remote_function("test_func", "maya", "maya-1")

    mock_client.call.assert_called_once_with(
        "describe_remote_function", name="test_func"
    )
    assert result["found"] is True
    assert result["signature"] == "test_func(a: int, b: str) -> bool"
    assert result["doc"] == "Test function docstring."


def test_list_remote_functions(mock_client):
    """Test listing remote functions."""
    mock_client.call.return_value = ["func1", "func2"]

    result = list_remote_functions("maya", "maya-1")

    mock_client.call.assert_called_once_with(
        "list_registered_functions", verbose=False
    )
    assert result == ["func1", "func2"]


def test_list_remote_functions_verbose(mock_client):
    """Test listing remote functions with verbose output."""
    mock_client.call.return_value = [
        {
            "name": "func1",
            "signature": "func1(a: int, b: str) -> bool",
            "doc": "Function 1 docstring.",
        },
        {
            "name": "func2",
            "signature": "func2() -> None",
            "doc": "Function 2 docstring.",
        },
    ]

    result = list_remote_functions("maya", "maya-1", verbose=True)

    mock_client.call.assert_called_once_with(
        "list_registered_functions", verbose=True
    )
    assert len(result) == 2
    assert result[0]["name"] == "func1"
    assert result[1]["name"] == "func2"
