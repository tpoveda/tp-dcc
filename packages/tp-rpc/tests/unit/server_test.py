from __future__ import annotations

from unittest.mock import patch, MagicMock, call

import pytest

from tp.libs.rpc.core.server import RPCService, start_server, shutdown_server


@pytest.fixture
def mock_daemon():
    """Mock Pyro5 daemon."""
    mock = MagicMock()
    with patch("Pyro5.api.Daemon", return_value=mock):
        yield mock


@pytest.fixture
def mock_registry():
    """Mock registry functions."""
    with patch("tp.libs.rpc.core.registry.get_function") as mock_get:
        with patch("tp.libs.rpc.core.registry.list_functions") as mock_list:
            yield mock_get, mock_list


def test_rpc_service_init():
    """Test RPCService initialization."""
    service = RPCService({"test_key": "test_value"})
    assert service.injected_globals == {"test_key": "test_value"}


def test_rpc_service_call(mock_registry):
    """Test RPCService call method."""
    mock_get, _ = mock_registry
    mock_func = MagicMock(return_value=42)
    mock_get.return_value = mock_func

    service = RPCService()
    result = service.call("test_function", 1, 2, key="value")

    mock_get.assert_called_once_with("test_function")
    mock_func.assert_called_once_with(1, 2, key="value")
    assert result == 42


def test_rpc_service_call_function_not_found(mock_registry):
    """Test RPCService call with non-existent function."""
    mock_get, _ = mock_registry
    mock_get.return_value = None

    service = RPCService()

    with pytest.raises(
        ValueError, match="Function 'test_function' is not registered"
    ):
        service.call("test_function")


def test_rpc_service_list_methods(mock_registry):
    """Test RPCService list_methods method."""
    _, mock_list = mock_registry
    mock_list.return_value = ["func1", "func2"]

    service = RPCService()
    result = service.list_methods()

    mock_list.assert_called_once()
    assert result == ["func1", "func2"]


def test_rpc_service_get_globals():
    """Test RPCService get_globals method."""
    service = RPCService({"module1": MagicMock(), "module2": MagicMock()})
    result = service.get_globals()

    assert sorted(result) == ["module1", "module2"]


def test_rpc_service_batch_call(mock_registry):
    """Test RPCService batch_call method."""
    mock_get, _ = mock_registry
    mock_func1 = MagicMock(return_value=3)
    mock_func2 = MagicMock(return_value="hello")
    mock_get.side_effect = lambda name: {
        "func1": mock_func1,
        "func2": mock_func2,
    }.get(name)

    service = RPCService()
    calls = [
        {"function": "func1", "args": [1, 2]},
        {"function": "func2", "args": ["hello"]},
    ]

    result = service.batch_call(calls)

    assert len(result) == 2
    assert result[0]["status"] == "success"
    assert result[0]["result"] == 3
    assert result[1]["status"] == "success"
    assert result[1]["result"] == "hello"


def test_rpc_service_batch_call_error(mock_registry):
    """Test RPCService batch_call with an error."""
    mock_get, _ = mock_registry
    mock_func = MagicMock(side_effect=ValueError("Test error"))
    mock_get.return_value = mock_func

    service = RPCService()
    calls = [{"function": "func1", "args": [1, 2]}]

    result = service.batch_call(calls)

    assert len(result) == 1
    assert result[0]["status"] == "error"
    assert "Test error" in result[0]["error"]
    assert result[0]["type"] == "ValueError"


def test_start_server(mock_daemon):
    """Test start_server function."""
    # Mock the register_instance function
    with patch("tp.libs.rpc.core.server.register_instance") as mock_register:
        # Mock the threading.Thread
        with patch("threading.Thread") as mock_thread:
            # Call the function with explicit instance_name to avoid auto-generation
            instance_name = start_server(
                host="localhost",
                port=9999,
                dcc_type="test",
                instance_name="test_instance",
            )

            # Verify the daemon.register was called
            mock_daemon.register.assert_called_once()

            # Verify register_instance was called with the correct arguments
            mock_register.assert_called_once_with(
                "test", str(mock_daemon.register.return_value), "test_instance"
            )

            # Verify threading.Thread was called
            mock_thread.assert_called_once()

            # Verify the return value
            assert instance_name == "test_instance"


def test_start_server_auto_instance(mock_daemon):
    """Test start_server with auto-generated instance name."""
    # Mock the generate_and_register_instance_name function
    with patch(
        "tp.libs.rpc.core.server.generate_and_register_instance_name"
    ) as mock_generate:
        mock_generate.return_value = "auto-instance"

        # Mock the threading.Thread
        with patch("threading.Thread") as mock_thread:
            # Call the function without instance_name to trigger auto-generation
            instance_name = start_server(
                host="localhost", port=9999, dcc_type="test"
            )

            # Verify generate_and_register_instance_name was called
            mock_generate.assert_called_once_with(
                "test", str(mock_daemon.register.return_value)
            )

            # Verify the return value
            assert instance_name == "auto-instance"


def test_shutdown_server(mock_daemon):
    """Test shutdown_server function."""
    # First start a server
    with patch("threading.Thread"):
        start_server()

    # Then shut it down
    shutdown_server()

    mock_daemon.shutdown.assert_called_once()
