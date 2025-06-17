from __future__ import annotations

import time
import threading
from typing import Dict, List, Any

import Pyro5.api
import Pyro5.client
import Pyro5.errors
from loguru import logger

from .retry import with_retry


class PooledConnection:
    """A connection in the connection pool."""

    def __init__(self, uri: str, timeout: float = 5.0):
        """Initialize a new pooled connection.

        Args:
            uri: Pyro5 URI.
            timeout: Connection timeout in seconds.
        """

        self.uri = uri
        self.proxy = Pyro5.api.Proxy(uri)
        self.proxy._pyroTimeout = timeout
        self.last_used = time.time()
        self.in_use = False

    def acquire(self):
        """Mark the connection as in use."""

        self.in_use = True
        self.last_used = time.time()

    def release(self):
        """Release the connection back to the pool."""

        self.in_use = False
        self.last_used = time.time()

    def close(self):
        """Close the underlying Pyro5 proxy."""

        try:
            # noinspection PyProtectedMember
            self.proxy._pyroRelease()
        except Exception as e:
            logger.warning(f"[tp-rpc][pool] Error closing connection: {e}")


class ConnectionPool:
    """A pool of reusable Pyro5 connections."""

    def __init__(
        self,
        max_connections: int = 10,
        connection_timeout: float = 5.0,
        idle_timeout: float = 60.0,
        cleanup_interval: float = 30.0,
    ):
        """Initialize the connection pool.

        Args:
            max_connections: Maximum number of connections per URI.
            connection_timeout: Connection timeout in seconds.
            idle_timeout: Time in seconds after which idle connections are
                closed.
            cleanup_interval: Interval in seconds for running the cleanup task.
        """

        self._pools: Dict[str, List[PooledConnection]] = {}
        self._lock = threading.RLock()
        self._max_connections = max_connections
        self._connection_timeout = connection_timeout
        self._idle_timeout = idle_timeout

        # Start cleanup thread
        self._running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            args=(cleanup_interval,),
            daemon=True,
            name="ConnectionPoolCleanup",
        )
        self._cleanup_thread.start()

        logger.info(
            f"[tp-rpc][pool] Connection pool initialized "
            f"(max={max_connections}, timeout={connection_timeout}s, "
            f"idle_timeout={idle_timeout}s)"
        )

    def get_connection(self, uri: str) -> PooledConnection:
        """Get a connection from the pool or create a new one.

        Args:
            uri: The URI to connect to.

        Returns:
            A pooled connection.
        """

        with self._lock:
            # Create a pool for this URI if it doesn't exist.
            if uri not in self._pools:
                self._pools[uri] = []

            pool = self._pools[uri]

            # Try to find an available connection.
            for conn in pool:
                if not conn.in_use:
                    conn.acquire()
                    return conn

            # If we've reached max connections, wait for one to become
            # available.
            if len(pool) >= self._max_connections:
                logger.debug(f"[tp-rpc][pool] Pool for {uri} at capacity, waiting...")
                # Return the oldest connection (will be released by the caller)
                oldest_conn = min(pool, key=lambda c: c.last_used)
                oldest_conn.acquire()
                return oldest_conn

            # Create a new connection.
            conn = PooledConnection(uri, self._connection_timeout)
            conn.acquire()
            pool.append(conn)
            logger.debug(f"[tp-rpc][pool] Created new connection for {uri}")
            return conn

    def release_connection(self, connection: PooledConnection):
        """Release a connection back to the pool.

        Args:
            connection: The connection to release.
        """

        with self._lock:
            if (
                connection.uri in self._pools
                and connection in self._pools[connection.uri]
            ):
                connection.release()
                logger.debug(
                    f"[tp-rpc][pool] Released connection for {connection.uri}"
                )

    def _cleanup_loop(self, interval: float):
        """Background thread that periodically cleans up idle connections.

        Args:
            interval: Time between cleanup runs in seconds.
        """

        while self._running:
            time.sleep(interval)
            try:
                self._cleanup_idle_connections()
            except Exception as e:
                logger.error(f"[tp-rpc][pool] Error in cleanup: {e}")

    def _cleanup_idle_connections(self):
        """Remove idle connections that have exceeded the idle timeout."""

        now = time.time()
        with self._lock:
            for uri, pool in list(self._pools.items()):
                # Find idle connections to remove.
                to_remove = [
                    conn
                    for conn in pool
                    if not conn.in_use and now - conn.last_used > self._idle_timeout
                ]

                # Close and remove them.
                for conn in to_remove:
                    conn.close()
                    pool.remove(conn)

                if to_remove:
                    logger.debug(
                        f"[tp-rpc][pool] Closed {len(to_remove)} idle "
                        f"connections for {uri}"
                    )

                # Remove empty pools.
                if not pool:
                    del self._pools[uri]

    def shutdown(self):
        """Shutdown the connection pool and close all connections."""

        self._running = False
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5.0)

        with self._lock:
            for uri, pool in self._pools.items():
                for conn in pool:
                    try:
                        conn.close()
                    except Exception as e:
                        logger.warning(f"[tp-rpc][pool] Error closing connection: {e}")
            self._pools.clear()

        logger.info("[tp-rpc][pool] Connection pool shutdown complete")


# Global connection pool instance
_connection_pool = ConnectionPool()


def get_connection_pool() -> ConnectionPool:
    """Get the global connection pool instance.

    Returns:
        The singleton ConnectionPool instance.
    """

    return _connection_pool


class PooledRPCClient:
    """An RPC client that uses connection pooling for better performance."""

    def __init__(
        self,
        uri: str,
        timeout: float = 5.0,
        retry_enabled: bool = True,
        max_attempts: int = 3,
    ):
        """Initialize a pooled RPC client.

        Args:
            uri: The URI of the remote Pyro5 object.
            timeout: Connection timeout in seconds.
            retry_enabled: Whether to retry failed calls.
            max_attempts: Maximum number of retry attempts.
        """

        self._uri = uri
        self._timeout = timeout
        self._retry_enabled = retry_enabled
        self._max_attempts = max_attempts
        self._pool = get_connection_pool()
        self._connection = None

        logger.debug(
            f"[tp-rpc][client] Created pooled client for {uri} "
            f"(timeout={timeout}s, retry={retry_enabled})"
        )

    def __enter__(self):
        """Context manager entry that acquires a connection from the pool."""

        self._connection = self._pool.get_connection(self._uri)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit that releases the connection back to the
        pool.
        """

        if self._connection:
            self._pool.release_connection(self._connection)
            self._connection = None

    @with_retry(max_attempts=3)
    def call(self, function_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call a remote function using a pooled connection.

        Args:
            function_name: The name of the registered function to invoke.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The return value from the remote function call.
        """

        if not self._connection:
            raise RuntimeError("No active connection. Use with context manager.")

        try:
            start_time = time.time()
            result = self._connection.proxy.call(function_name, *args, **kwargs)
            elapsed = time.time() - start_time

            logger.debug(
                f"[tp-rpc][client] Call to '{function_name}' completed "
                f"in {elapsed:.3f}s"
            )
            return result

        except Exception as e:
            logger.error(f"[tp-rpc][client] Error calling '{function_name}': {e}")
            raise

    @with_retry(max_attempts=3)
    def list_methods(self) -> list[str]:
        """Retrieve the list of functions available on the server.

        Returns:
            A list of available function names.
        """
        if not self._connection:
            raise RuntimeError("No active connection. Use with context manager.")

        try:
            return self._connection.proxy.list_methods()
        except Exception as e:
            logger.error(f"[tp-rpc][client] Error listing methods: {e}")
            raise
