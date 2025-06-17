from __future__ import annotations

from typing import Any
from collections.abc import Callable

from ..core.registry import register_function as core_register_function
from ..core.client import RPCClient


def register_function(
    name: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register a function for remote calling via the RPC server.

    This wraps the `core.registry.register_function` to expose it through the
    API layer.

    Args:
        name: Optional name under which the function should be registered.
            If None, uses the function's own name.

    Returns:
        The same function, registered for remote access.
    """

    return core_register_function(name)


def remote_call(
    uri: str, remote_name: str | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to execute a function remotely instead of locally.

    When called, the function will be executed via a Pyro5 RPC client,
    targeting the given URI and function name.

    Args:
        uri: The URI of the Pyro5 server
            e.g., 'PYRO:rpc.service@localhost:9090'.
        remote_name: The name of the function registered on the server.
            If None, uses the function's `__name__`.

    Returns:
        Callable: A decorated function that executes remotely.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        function_name = remote_name or func.__name__

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            client = RPCClient(uri)
            try:
                return client.call(function_name, *args, **kwargs)
            finally:
                client.close()

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator
