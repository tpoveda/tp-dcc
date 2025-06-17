from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
import Pyro5.errors

from tp.libs.rpc.core.client import RPCClient


@pytest.fixture
def mock_proxy():
    """Create a mock Pyro5 proxy."""

    mock = MagicMock()
    with patch("Pyro5.api.Proxy", return_value=mock):
        yield mock


def test_client_initialization(mock_proxy):
    """Test client initialization."""

    client = RPCClient("PYRO:test@localhost:9999")
    assert client._uri == "PYRO:test@localhost:9999"
    assert client._timeout == 5.0
    assert client._retry_enabled is True
    assert client._max_attempts == 3
    assert client._use_pooling is True


def test_client_call(mock_proxy):
    """Test client call method."""

    client = RPCClient("PYRO:test@localhost:9999", use_pooling=False)
    mock_proxy.call.return_value = 42

    result = client.call("test_function", 1, 2, key="value")

    mock_proxy.call.assert_called_once_with("test_function", 1, 2, key="value")
    assert result == 42


def test_client_list_methods(mock_proxy):
    """Test client list_methods method."""

    client = RPCClient("PYRO:test@localhost:9999", use_pooling=False)
    mock_proxy.list_methods.return_value = ["func1", "func2"]

    result = client.list_methods()

    mock_proxy.list_methods.assert_called_once()
    assert result == ["func1", "func2"]


def test_client_close(mock_proxy):
    """Test client close method."""

    client = RPCClient("PYRO:test@localhost:9999", use_pooling=False)

    client.close()

    mock_proxy._pyroRelease.assert_called_once()


def test_client_retry_on_error(mock_proxy):
    """Test client retry mechanism."""

    client = RPCClient("PYRO:test@localhost:9999", use_pooling=False)

    # Make the first two calls fail, third time succeeds
    mock_proxy.call.side_effect = [
        Pyro5.errors.CommunicationError("Test error"),
        Pyro5.errors.CommunicationError("Test error"),
        42,
    ]

    with patch("time.sleep") as mock_sleep:  # Avoid actual sleeping
        result = client.call("test_function")

        assert mock_proxy.call.call_count == 3
        assert mock_sleep.call_count == 2
        assert result == 42


def test_client_batch_call(mock_proxy):
    """Test client batch_call method."""

    client = RPCClient("PYRO:test@localhost:9999", use_pooling=False)
    mock_proxy.batch_call.return_value = [
        {"status": "success", "result": 3},
        {"status": "success", "result": "hello"},
    ]

    calls = [
        {"function": "add", "args": [1, 2]},
        {"function": "echo", "args": ["hello"]},
    ]

    result = client.batch_call(calls)

    mock_proxy.batch_call.assert_called_once_with(calls)
    assert result == [
        {"status": "success", "result": 3},
        {"status": "success", "result": "hello"},
    ]
