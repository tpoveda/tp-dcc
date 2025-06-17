from __future__ import annotations

import os
import sys
import ast
import inspect
import importlib.util
from typing import overload, Literal, Any
from types import FunctionType, ModuleType

from loguru import logger

from ..core.client import RPCClient
from ..core.instances import get_uri
from ..core.server import start_server, shutdown_server


def launch_server(
    host: str = "localhost",
    port: int = 0,
    dcc_type: str | None = None,
    instance_name: str | None = None,
    additional_globals: dict[str, ModuleType] | None = None,
) -> str:
    """Launch an RPC server on the specified host and port.

    Args:
        host: Host to bind to (default: "localhost").
        port: Port to bind to (0 = auto-assign a free port).
        dcc_type: Type of DCC to use (default: None).
            If None, the server will be launched without a specific DCC.
        instance_name: Name of the DCC instance (default: None).
            If None, the server will be launched without a specific instance.
        additional_globals: Optional dictionary of additional global
            variables to inject into the server's globals.

    Returns:
        The final registered instance name (explicit or auto-generated).
    """

    return start_server(
        host=host,
        port=port,
        dcc_type=dcc_type,
        instance_name=instance_name,
        additional_globals=additional_globals,
    )


def stop_server() -> None:
    """Stop the currently running RPC server (if active).

    This should be called from within the
    DCC (e.g., via atexit or shutdown hook).
    """
    try:
        shutdown_server()
    except Exception as e:
        logger.error(f"Stop_server failed: {e}")


def call_remote_function(
    function_name: str,
    uri: str | None = None,
    dcc_type: str | None = None,
    instance_name: str | None = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Execute a registered function on the remote server and return the
    result.

    Args:
        uri: URI of the Pyro5 RPC service.
            e.g., 'PYRO:rpc.service@localhost:9090'.
        function_name: Name of the registered function to call.
        dcc_type: Type of DCC to use (default: None).
            If None, the function will be called without a specific DCC.
        instance_name: Name of the DCC instance (default: None).
        *args: Positional arguments to pass.
        **kwargs: Keyword arguments to pass.

    Returns:
        Any: Result of the remote function.

    Raises:
        ValueError: If no URI or DCC type is provided.
        ValueError: If no registered instance is found for the given DCC type
            and instance name.
        ValueError: If the function name is not provided.
    """

    if not uri:
        if not dcc_type:
            raise ValueError("You must provide either a URI or a DCC type.")
        uri = get_uri(dcc_type, instance_name)
        if not uri:
            raise ValueError(
                f"No registered instance found for"
                f" {dcc_type} / {instance_name or '[default]'}"
            )

    if not function_name:
        raise ValueError("Function name is required.")

    client = RPCClient(uri)
    try:
        return client.call(function_name, *args, **kwargs)
    finally:
        client.close()


def remote_call(func, dcc_type: str, instance_name: str | None = None, *args, **kwargs):
    """Registers a function remotely and immediately calls it.

    Args:
        func: The function to register and call.
        dcc_type: The DCC type (e.g., "maya", "unreal").
        instance_name: Optional instance name.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
    """

    register_function_remotely(
        func=func, dcc_type=dcc_type, instance_name=instance_name
    )
    return call_remote_function(
        dcc_type=dcc_type,
        instance_name=instance_name,
        function_name=func.__name__,
        *args,
        **kwargs,
    )


def extract_dependency_paths(func: FunctionType) -> list[str]:
    """Extract sys.path entries needed for modules imported inside the
    function.

    Args:
        func: The function whose source will be analyzed.

    Returns:
        Valid filesystem paths to add to the server's sys.path.
    """

    source = inspect.getsource(func)
    module = getattr(func, "__module__", None)
    tree = ast.parse(source)
    module_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                # Absolute import
                module_names.add(node.module)
            elif node.level > 0 and module:
                # Relative import resolution
                parts = module.split(".")
                if len(parts) >= node.level:
                    abs_base = ".".join(parts[: -node.level])
                    if node.module:
                        module_names.add(f"{abs_base}.{node.module}")
                    else:
                        module_names.add(abs_base)

    paths = set()
    for mod_name in module_names:
        # noinspection PyBroadException
        try:
            spec = importlib.util.find_spec(mod_name)
            if spec and spec.origin and "site-packages" not in spec.origin:
                mod_path = os.path.dirname(spec.origin)
                paths.add(mod_path)
        except Exception:
            continue

    return list(paths)


def register_function_remotely(
    func: FunctionType,
    dcc_type: str,
    instance_name: str | None = None,
    inject_sys_path: bool = True,
    inject_globals: dict[str, Any] | None = None,
    detect_import_paths: bool = True,
) -> dict:
    """Send a Python function to a remote DCC server and register it there.

    Args:
        func: A local Python function object.
        dcc_type: The DCC name ("maya", "unreal", etc.).
        instance_name: Optional instance name.
        inject_sys_path: If True, inject the current sys.path into the
            remote server's sys.path.
        inject_globals: Optional dictionary of global variables to inject
            into the remote server's globals.
        detect_import_paths: If True, detect and inject the paths of
            imported modules in the function's source code.

    Returns:
        Server's response dictionary.
    """

    if not callable(func):
        raise TypeError("Provided object is not a function.")

    try:
        source = inspect.getsource(func)
    except (OSError, TypeError) as e:
        raise ValueError(f"Could not retrieve source for {func.__name__}: {e}")

    paths = sys.path if inject_sys_path else []
    deps = extract_dependency_paths(func) if detect_import_paths else []
    all_paths = list(set(paths + deps))
    globals_payload = inject_globals or {}

    logger.debug(f"Registering '{func.__name__}' to {dcc_type}...")
    logger.debug(f"Injected sys.path entries ({len(all_paths)}):")
    for path in all_paths:
        logger.debug(f"  - {path}")

    return call_remote_function(
        dcc_type=dcc_type,
        instance_name=instance_name,
        function_name="register_remote_function",
        name=func.__name__,
        source_code=source,
        client_paths=all_paths,
        client_globals=globals_payload,
    )


def ping_instance(dcc_type: str, instance_name: str | None = None) -> dict:
    """Ping a remote instance and return basic info.

    Args:
        dcc_type: Target DCC.
        instance_name: Specific instance.

    Returns:
        Dictionary with keys: 'uri', 'instance_name', 'dcc_type'.
    """

    return call_remote_function(
        dcc_type=dcc_type,
        function_name="ping",
        instance_name=instance_name,
    )


def describe_remote_function(
    name: str, dcc_type: str, instance_name: str | None = None
) -> dict:
    """Return full signature and docstring of a remote function.

    Args:
        name: Function name to describe.
        dcc_type: Target DCC.
        instance_name: Specific instance.

    Returns:
        Contains keys: 'found', 'signature', 'doc'
    """

    return call_remote_function(
        dcc_type=dcc_type,
        instance_name=instance_name,
        function_name="describe_remote_function",
        name=name,
    )


@overload
def list_remote_functions(
    dcc_type: str,
    instance_name: str | None = None,
    verbose: Literal[False] = False,
) -> list[str]: ...


@overload
def list_remote_functions(
    dcc_type: str,
    instance_name: str | None = None,
    verbose: Literal[True] = True,
) -> list[dict]: ...


def list_remote_functions(
    dcc_type: str,
    instance_name: str | None = None,
    verbose: bool = False,
) -> list[str] | list[dict]:
    """Query a remote DCC instance for registered functions.

    Args:
        dcc_type (str): DCC to target (e.g., "maya").
        instance_name (str | None): Optional specific instance name.
        verbose (bool): If True, includes function signature and docstring.

    Returns:
        List of function names or detailed metadata.
    """
    return call_remote_function(
        dcc_type=dcc_type,
        instance_name=instance_name,
        function_name="list_registered_functions",
        verbose=verbose,
    )


# def list_remote_functions(
#     uri: str, dcc_type: str | None = None, instance_name: str | None = None
# ) -> list[str]:
#     """Retrieve the list of all functions registered on the remote server.
#
#     Args:
#         uri: URI of the remote Pyro5 server.
#             e.g., 'PYRO:rpc.service@localhost:9090'.
#         dcc_type: Type of DCC to use (default: None).
#             If None, the functions will be listed without a specific DCC.
#         instance_name: Name of the DCC instance (default: None).
#             If None, the functions will be listed without a specific instance.
#
#     Returns:
#         List of function names available for calling.
#     """
#
#     if not uri:
#         if not dcc_type:
#             raise ValueError("You must provide either a URI or DCC type.")
#         uri = get_uri(dcc_type, instance_name)
#         if not uri:
#             raise ValueError(
#                 f"No registered instance found for"
#                 f" {dcc_type} / {instance_name or '[default]'}"
#             )
#
#     client = RPCClient(uri)
#     try:
#         return client.list_methods()
#     finally:
#         client.close()
