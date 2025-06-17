from __future__ import annotations

import time
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.core.connection_pool import (
    PooledConnection,
    ConnectionPool,
    get_connection_pool,
    PooledRPCClient,
)


@pytest.fixture
def mock_pyro_proxy():
    """Mock Pyro5 proxy."""
    with patch("Pyro5.api.Proxy") as mock:
        yield mock


def test_pooled_connection_init(mock_pyro_proxy):
    """Test PooledConnection initialization."""
    conn = PooledConnection("PYRO:test@localhost:9999", timeout=10.0)

    mock_pyro_proxy.assert_called_once_with("PYRO:test@localhost:9999")
    assert conn.uri == "PYRO:test@localhost:9999"
    assert conn.proxy._pyroTimeout == 10.0
    assert conn.in_use is False


def test_pooled_connection_acquire():
    """Test PooledConnection acquire method."""
    conn = PooledConnection("PYRO:test@localhost:9999")

    # Reset last_used to a known value
    conn.last_used = 0

    with patch("time.time", return_value=123.0):
        conn.acquire()

        assert conn.in_use is True
        assert conn.last_used == 123.0


def test_pooled_connection_release():
    """Test PooledConnection release method."""
    conn = PooledConnection("PYRO:test@localhost:9999")
    conn.in_use = True

    # Reset last_used to a known value
    conn.last_used = 0

    with patch("time.time", return_value=123.0):
        conn.release()

        assert conn.in_use is False
        assert conn.last_used == 123.0


def test_pooled_connection_close():
    """Test PooledConnection close method."""
    conn = PooledConnection("PYRO:test@localhost:9999")

    conn.close()

    conn.proxy._pyroRelease.assert_called_once()


def test_connection_pool_init():
    """Test ConnectionPool initialization."""
    with patch("threading.Thread") as mock_thread:
        pool = ConnectionPool(
            max_connections=5,
            connection_timeout=10.0,
            idle_timeout=30.0,
            cleanup_interval=15.0,
        )

        assert pool._max_connections == 5
        assert pool._connection_timeout == 10.0
        assert pool._idle_timeout == 30.0
        assert len(pool._pools) == 0

        # Check that cleanup thread was started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()


def test_connection_pool_get_connection():
    """Test ConnectionPool get_connection method."""
    with patch("threading.Thread"):
        pool = ConnectionPool()

        with patch(
            "tp.libs.rpc.core.connection_pool.PooledConnection"
        ) as mock_conn:
            mock_instance = MagicMock()
            mock_conn.return_value = mock_instance

            # First call should create a new connection
            conn1 = pool.get_connection("PYRO:test@localhost:9999")

            mock_conn.assert_called_once_with("PYRO:test@localhost:9999", 5.0)
            mock_instance.acquire.assert_called_once()
            assert conn1 == mock_instance

            # Reset mocks
            mock_conn.reset_mock()
            mock_instance.acquire.reset_mock()

            # Second call should reuse the connection if it's not in use
            mock_instance.in_use = False
            conn2 = pool.get_connection("PYRO:test@localhost:9999")

            mock_conn.assert_not_called()
            mock_instance.acquire.assert_called_once()
            assert conn2 == mock_instance


def test_connection_pool_get_connection_at_capacity():
    """Test ConnectionPool get_connection method when at capacity."""
    with patch("threading.Thread"):
        pool = ConnectionPool(max_connections=1)

        # Create a mock connection that's in use
        mock_conn = MagicMock()
        mock_conn.in_use = True
        mock_conn.last_used = 100.0

        # Add it to the pool
        pool._pools["PYRO:test@localhost:9999"] = [mock_conn]

        # Getting a connection should return the existing one even though it's in use
        conn = pool.get_connection("PYRO:test@localhost:9999")

        assert conn == mock_conn
        assert mock_conn.acquire.call_count == 1


def test_connection_pool_release_connection():
    """Test ConnectionPool release_connection method."""
    with patch("threading.Thread"):
        pool = ConnectionPool()

        # Create a mock connection
        mock_conn = MagicMock()
        mock_conn.uri = "PYRO:test@localhost:9999"

        # Add it to the pool
        pool._pools["PYRO:test@localhost:9999"] = [mock_conn]

        # Release the connection
        pool.release_connection(mock_conn)

        mock_conn.release.assert_called_once()


def test_connection_pool_cleanup_idle_connections():
    """Test ConnectionPool _cleanup_idle_connections method."""
    with patch("threading.Thread"):
        pool = ConnectionPool(idle_timeout=10.0)

        # Create mock connections
        mock_conn1 = MagicMock()  # Active connection
        mock_conn1.in_use = True
        mock_conn1.last_used = time.time()

        mock_conn2 = MagicMock()  # Idle connection (recent)
        mock_conn2.in_use = False
        mock_conn2.last_used = time.time()

        mock_conn3 = MagicMock()  # Idle connection (old)
        mock_conn3.in_use = False
        mock_conn3.last_used = time.time() - 20.0  # Older than idle_timeout

        # Add them to the pool
        pool._pools["uri1"] = [mock_conn1]
        pool._pools["uri2"] = [mock_conn2, mock_conn3]

        # Run cleanup
        pool._cleanup_idle_connections()

        # Check that only the old idle connection was closed and removed
        mock_conn1.close.assert_not_called()
        mock_conn2.close.assert_not_called()
        mock_conn3.close.assert_called_once()

        assert len(pool._pools["uri1"]) == 1
        assert len(pool._pools["uri2"]) == 1
        assert pool._pools["uri2"][0] == mock_conn2


def test_connection_pool_shutdown():
    """Test ConnectionPool shutdown method."""
    with patch("threading.Thread") as mock_thread:
        thread_instance = MagicMock()
        mock_thread.return_value = thread_instance

        pool = ConnectionPool()

        # Create mock connections
        mock_conn1 = MagicMock()
        mock_conn2 = MagicMock()

        # Add them to the pool
        pool._pools["uri1"] = [mock_conn1]
        pool._pools["uri2"] = [mock_conn2]

        # Shutdown the pool
        pool.shutdown()

        # Check that connections were closed
        mock_conn1.close.assert_called_once()
        mock_conn2.close.assert_called_once()

        # Check that the pool was cleared
        assert len(pool._pools) == 0

        # Check that the cleanup thread was stopped
        assert pool._running is False


def test_get_connection_pool():
    """Test get_connection_pool function."""
    # First call should create a new pool
    pool1 = get_connection_pool()

    # Second call should return the same pool
    pool2 = get_connection_pool()

    assert pool1 is pool2
    assert isinstance(pool1, ConnectionPool)


def test_pooled_rpc_client_init():
    """Test PooledRPCClient initialization."""
    with patch("tp.libs.rpc.core.connection_pool.get_connection_pool"):
        client = PooledRPCClient(
            uri="PYRO:test@localhost:9999",
            timeout=10.0,
            retry_enabled=False,
            max_attempts=5,
        )

        assert client._uri == "PYRO:test@localhost:9999"
        assert client._timeout == 10.0
        assert client._retry_enabled is False
        assert client._max_attempts == 5


def test_pooled_rpc_client_context_manager():
    """Test PooledRPCClient as a context manager."""
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_pool.get_connection.return_value = mock_conn

    with patch(
        "tp.libs.rpc.core.connection_pool.get_connection_pool",
        return_value=mock_pool,
    ):
        client = PooledRPCClient("PYRO:test@localhost:9999")

        with client as ctx:
            assert ctx == client
            assert client._connection == mock_conn
            mock_pool.get_connection.assert_called_once_with(
                "PYRO:test@localhost:9999"
            )

        mock_pool.release_connection.assert_called_once_with(mock_conn)
        assert client._connection is None


def test_pooled_rpc_client_call():
    """Test PooledRPCClient call method."""
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.proxy.call.return_value = 42
    mock_pool.get_connection.return_value = mock_conn

    with patch(
        "tp.libs.rpc.core.connection_pool.get_connection_pool",
        return_value=mock_pool,
    ):
        client = PooledRPCClient("PYRO:test@localhost:9999")

        with client:
            result = client.call("test_function", 1, 2, key="value")

            mock_conn.proxy.call.assert_called_once_with(
                "test_function", 1, 2, key="value"
            )
            assert result == 42


def test_pooled_rpc_client_call_without_context():
    """Test PooledRPCClient call method without context manager."""
    with patch("tp.libs.rpc.core.connection_pool.get_connection_pool"):
        client = PooledRPCClient("PYRO:test@localhost:9999")

        with pytest.raises(RuntimeError, match="No active connection"):
            client.call("test_function")


def test_pooled_rpc_client_list_methods():
    """Test PooledRPCClient list_methods method."""
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.proxy.list_methods.return_value = ["func1", "func2"]
    mock_pool.get_connection.return_value = mock_conn

    with patch(
        "tp.libs.rpc.core.connection_pool.get_connection_pool",
        return_value=mock_pool,
    ):
        client = PooledRPCClient("PYRO:test@localhost:9999")

        with client:
            result = client.list_methods()

            mock_conn.proxy.list_methods.assert_called_once()
            assert result == ["func1", "func2"]
