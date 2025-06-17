from __future__ import annotations

import threading
from typing import Any
from types import ModuleType

import Pyro5.api
from loguru import logger

from . import registry
from .discovery import get_service_discovery
from .versioning import get_versioned_function
from .instances import register_instance, generate_and_register_instance_name

current_rpc_service: RPCService | None = None
_daemon: Pyro5.api.Daemon | None = None


@Pyro5.api.expose
class RPCService:
    """A Pyro5-exposed service class for handling remote procedure calls.

    This class defines the methods that are exposed remotely via Pyro5.
    It provides the ability to:
    - Dynamically call registered functions by name.
    - List available remote methods.
    """

    def __init__(self, injected_globals: dict[str, Any] | None = None):
        """Initialize the RPCService.

        Args:
            injected_globals: A dictionary of global variables to inject into
                the remote functions. This allows for dynamic access to global
                variables from the remote context.
        """

        self._injected_globals = injected_globals or {}

    @property
    def injected_globals(self) -> dict[str, Any]:
        """Get the injected globals.

        Returns:
            A dictionary of injected global variables.
        """

        return self._injected_globals

    # noinspection PyMethodMayBeStatic
    def call(self, function_name: str, *args: Any, **kwargs: Any) -> Any:
        """Remotely call a registered function by name.

        Args:
            function_name: The name of the registered function to invoke.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            Any: The result of the function call.

        Raises:
            ValueError: If the function is not registered or cannot be found.
        """

        # Check for version in kwargs and try to get a versioned function
        # first.
        version = kwargs.pop("_version", None)
        func = None
        if version is not None:
            func = get_versioned_function(function_name, version)

        # Fallback to regular function registry.
        if func is None:
            func = registry.get_function(function_name)

        if not func:
            raise ValueError(f"Function '{function_name}' is not registered.")

        # Update the function's globals with injected_globals.
        if hasattr(func, "__globals__"):
            func.__globals__.update(self._injected_globals)

        return func(*args, **kwargs)

    # noinspection PyMethodMayBeStatic
    def list_methods(self) -> list[str]:
        """Retrieve the list of available registered functions.

        Returns:
            A list of function names.
        """

        return registry.list_functions()

    def get_globals(self) -> list[str]:
        """Return names of injected globals available in the server.

        Returns:
            A list of names of injected globals.
        """

        return list(self._injected_globals.keys())

    def batch_call(self, calls: list[dict]) -> list:
        """Execute multiple function calls in a single request.

        Args:
            calls: List of call specifications, each containing:
                - 'function': Name of the function to call
                - 'args': List of positional arguments (optional)
                - 'kwargs': Dictionary of keyword arguments (optional)

        Returns:
            List of results in the same order as the calls.
            Each result is either the actual return value or an error dict.
        """

        results = []

        for call_spec in calls:
            function_name = call_spec.get("function")
            args = call_spec.get("args", [])
            kwargs = call_spec.get("kwargs", {})

            try:
                if not function_name:
                    raise ValueError("Missing function name in batch call")

                result = self.call(function_name, *args, **kwargs)
                results.append({"status": "success", "result": result})
            except Exception as e:
                results.append(
                    {
                        "status": "error",
                        "error": str(e),
                        "type": type(e).__name__,
                    }
                )

        return results


def start_server(
    host: str = "localhost",
    port: int = 0,
    dcc_type: str | None = None,
    instance_name: str | None = None,
    additional_globals: dict[str, ModuleType] | None = None,
    enable_discovery: bool = True,
) -> str | None:
    """Start the Pyro5 daemon and register the RPCService.

    This will print the URI of the registered service, which clients need to
    connect to the server.

    Args:
        host: Host address to bind the server to. Default is 'localhost'.
        port: Port number to bind the server to. If 0, a random free port is
            chosen.
        dcc_type: Type of DCC ('maya', 'unreal', etc.) for registry.
        instance_name: Unique name of this instance (e.g. 'maya_main').
        additional_globals: A dictionary of global variables to inject into
            the remote functions. This allows for dynamic access to global
            variables from the remote context.
        enable_discovery: Whether to enable service discovery

    Returns:
        str | None: The instance name if registered, otherwise None.
    """

    global _daemon
    global current_rpc_service

    _daemon = Pyro5.api.Daemon(host=host, port=port)

    # Use a unique Pyro object ID for each instance.
    temp_instance_name = instance_name or "temp"
    object_id = f"rpc.service.{dcc_type or 'unnamed'}_{temp_instance_name}"

    # Prepare initial globals
    service_globals = additional_globals or {}
    service_globals = dict(service_globals)  # Shallow copy

    # Instance name may not be known yet — inject it later.
    current_rpc_service = RPCService(injected_globals=service_globals)

    uri = _daemon.register(current_rpc_service, objectId=object_id)

    # Resolve the final instance name and register.
    if dcc_type:
        if instance_name:
            register_instance(dcc_type, str(uri), instance_name)
        else:
            instance_name = generate_and_register_instance_name(dcc_type, str(uri))

    logger.info(f"[RPC Server] Ready. URI: {uri}")

    # Inject the final instance name and dcc type to service's globals.
    current_rpc_service.injected_globals["dcc_type"] = dcc_type
    current_rpc_service.injected_globals["instance_name"] = instance_name

    logger.info(
        f"[RPC Server] Injected globals: {current_rpc_service.injected_globals}"
    )

    # Start service discovery if enabled.
    if enable_discovery and dcc_type and instance_name:
        discovery = get_service_discovery()
        discovery.start_listener()
        discovery.start_announcer(str(uri), dcc_type, instance_name)

    # Start the request loop in a background thread
    def _request_loop():
        try:
            _daemon.requestLoop()
        except Exception as e:
            logger.error(f"[RPC Server] Request loop error: {e}")

    thread = threading.Thread(target=_request_loop, name="RPCRequestLoop", daemon=True)
    thread.start()

    return instance_name


def shutdown_server():
    """Shutdown the Pyro5 daemon and unregister the RPCService.

    This will stop the server and clean up any resources.
    """

    global _daemon

    if _daemon:
        logger.info("[tp-rpc] Shutting down RPC server...")
        _daemon.shutdown()
        _daemon = None
        logger.info("[tp-rpc] Shutdown complete.")
    else:
        logger.warning("[tp-rpc] No active server to shutdown.")
