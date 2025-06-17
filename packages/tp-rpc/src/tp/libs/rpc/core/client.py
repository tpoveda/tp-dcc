from __future__ import annotations

import time
from typing import Any

import Pyro5.api
import Pyro5.client
import Pyro5.errors
from loguru import logger

from .retry import with_retry
from .connection_pool import PooledRPCClient, get_connection_pool


class RPCClient:
    """A simple RPC client that connects to a Pyro5 server and invokes
    registered functions.

    This class acts as a wrapper around the Pyro5 Proxy, allowing the user to
    easily call remote functions by name with arguments.

    Attributes:
        _uri: The full URI of the remote Pyro5 service.
        _proxy: The Pyro5 proxy used to make remote calls.
        _timeout: Connection timeout in seconds.
        _retry_enabled: Whether to retry failed calls.
        _max_attempts: Maximum number of retry attempts.
        _use_pooling: Whether to use connection pooling.

    Examples:
        >>> from tp.libs.rpc.core.client import RPCClient
        >>> client = RPCClient("PYRO:rpc.service@localhost:9090")
        >>> print(client.list_methods())
        >>> result = client.call("my_function", 1, 2, foo="bar")
        >>> print("Result:", result)
        >>> client.close()
    """

    def __init__(
        self,
        uri: str,
        timeout: float = 5.0,
        retry_enabled: bool = True,
        max_attempts: int = 3,
        use_pooling: bool = True,
    ) -> None:
        """Initialize the RPC client and connect to the given Pyro5
        service URI.

        Args:
            uri: The URI of the remote Pyro5 object,
                e.g., 'PYRO:rpc.service@localhost:9090'.
            timeout: Connection timeout in seconds.
            retry_enabled: Whether to retry failed calls.
            max_attempts: Maximum number of retry attempts.

        Raises:
            ValueError: If the URI format is invalid, or the proxy cannot be
                created.
        """

        self._uri: str = uri
        self._timeout = timeout
        self._retry_enabled = retry_enabled
        self._max_attempts = max_attempts
        self._use_pooling = use_pooling

        if use_pooling:
            self._pooled_client = PooledRPCClient(
                uri=uri,
                timeout=timeout,
                retry_enabled=retry_enabled,
                max_attempts=max_attempts,
            )
            self._proxy = None
        else:
            self._pooled_client = None
            self._proxy: Pyro5.client.Proxy = Pyro5.api.Proxy(uri)
            self._proxy._pyroTimeout = timeout

        logger.debug(
            f"[tp-rpc][client] Created client for {uri} (timeout={timeout}s,"
            f" retry={retry_enabled}, pooling={use_pooling})"
        )

    @with_retry(max_attempts=3)
    def call(self, function_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call a remote function registered on the server.

        Args:
            function_name: The name of the registered function to invoke.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Any: The return value from the remote function call.

        Raises:
            Exception: Propagates any error raised by the server.
        """

        if self._use_pooling:
            with self._pooled_client as client:
                return client.call(function_name, *args, **kwargs)
        else:
            try:
                start_time = time.time()
                result = self._proxy.call(function_name, *args, **kwargs)
                elapsed = time.time() - start_time

                logger.debug(
                    f"[tp-rpc][client] Call to '{function_name}' completed "
                    f"in {elapsed:.3f}s"
                )
                return result

            except Exception as e:
                logger.error(
                    f"[tp-rpc][client] Error calling '{function_name}': {e}"
                )
                raise

    def batch_call(self, calls: list[dict]) -> list:
        """Execute multiple function calls in a single network request.

        Args:
            calls: List of call specifications, each containing:
                - 'function': Name of the function to call
                - 'args': List of positional arguments (optional)
                - 'kwargs': Dictionary of keyword arguments (optional)

        Returns:
            List of results in the same order as the calls.

        Raises:
            Exception: If the batch call itself fails.
        """

        if self._use_pooling:
            with self._pooled_client as client:
                start_time = time.time()
                results = client._connection.proxy.batch_call(calls)
                elapsed = time.time() - start_time

                logger.debug(
                    f"[tp-rpc][client] Batch call with {len(calls)} operations "
                    f"completed in {elapsed:.3f}s"
                )
                return results
        else:
            try:
                start_time = time.time()
                results = self._proxy.batch_call(calls)
                elapsed = time.time() - start_time

                logger.debug(
                    f"[tp-rpc][client] Batch call with {len(calls)} operations "
                    f"completed in {elapsed:.3f}s"
                )
                return results
            except Exception as e:
                logger.error(f"[tp-rpc][client] Error in batch call: {e}")
                raise

    @with_retry(max_attempts=3)
    def list_methods(self) -> list[str]:
        """Retrieve the list of functions available on the server.

        Returns:
            A list of available function names.
        """

        if self._use_pooling:
            with self._pooled_client as client:
                return client.list_methods()
        else:
            try:
                return self._proxy.list_methods()
            except Exception as e:
                logger.error(f"[tp-rpc][client] Error listing methods: {e}")
                raise

    def close(self) -> None:
        """Cleanly closes the connection to the remote server."""

        if not self._use_pooling and self._proxy:
            try:
                # noinspection PyProtectedMember
                self._proxy._pyroRelease()
                logger.debug(
                    f"[tp-rpc][client] Connection to {self._uri} closed"
                )
            except Exception as e:
                logger.warning(
                    f"[tp-rpc][client] Error closing connection: {e}"
                )
