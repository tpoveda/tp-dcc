from __future__ import annotations

import os
import sys
import signal
import pprint
import socket
import platform
from typing import Any

from loguru import logger

from ..api.decorators import register_function
from ..core.events import Event, get_event_bus
from ..core.task_manager import RemoteTaskManager
from ..core.discovery import get_service_discovery
from ..core.server import shutdown_server, current_rpc_service
from ..core.versioning import list_versions, get_latest_version
from ..core.security import env_control_enabled, remote_control_enabled
from ..core.registry import get_function, list_functions, describe_function


# Global task manager instance
_task_manager = RemoteTaskManager()


@register_function()
def register_remote_function(
    name: str,
    source_code: str,
    client_paths: list[str] | None = None,
    client_globals: dict[str, Any] | None = None,
) -> dict:
    """Allows a remote client to register a Python function on this server.

    Warnings:
        This executes arbitrary code using `exec` and should only be
        enabled in secure, trusted environments. It is useful for dynamic,
        runtime extension of the server's capabilities — e.g., development
        or prototyping workflows.

    Args:
        name: The name to register the function under.
        source_code: Full Python source code of a function that defines
            a callable named `name`.
        client_paths: Optional list of paths to add to the Python path
            for the client. This is useful for importing modules or
            dependencies that are not already available in the server's
            environment. If provided, these paths will be added to the
            `sys.path` list, allowing the registered function to access
            modules located in those directories.
        client_globals: Optional dictionary of global variables to
            provide to the function's execution context. This allows
            the registered function to access specific variables or
            objects from the client's environment.

    Returns:
        A dictionary containing the result of the registration process.
            If successful, it will contain a success message.
            If there was an error, it will contain an error message.

    Raises:
        PermissionError: If remote function registration is disabled.
        ValueError: If the source code does not define a callable with
            the specified name.
        Exception: If there is an error during execution or registration.
    """

    if not remote_control_enabled():
        raise PermissionError("Remote function registration is disabled.")

    # Safely patch server sys.path with valid client paths.
    client_paths = client_paths or []
    client_globals = client_globals or {}

    injected = []
    skipped = []
    for path in client_paths:
        if os.path.exists(path) and path not in sys.path:
            sys.path.append(path)
            logger.info(f"[register_remote_function] Injected path: {path}")
            injected.append(path)
        else:
            logger.debug(f"[register_remote_function] Skipped path: {path}")
            skipped.append(path)

    exec_env: dict = {}

    # Merge injected server globals first (e.g., cmds, maya, etc.).
    if current_rpc_service and current_rpc_service.injected_globals:
        exec_env.update(current_rpc_service.injected_globals)

    # Then merge client-provided globals (they can override if needed).
    exec_env.update(client_globals)

    try:
        exec(source_code, exec_env)
        func = exec_env.get(name)
        if not callable(func):
            raise ValueError(f"Source does not define a callable named '{name}'.")

        register_function(name)(func)

        logger.info(
            f"[tp-rpc] Function '{name}' registered with {len(injected)} paths."
        )

        response = {
            "status": "success",
            "function": name,
            "paths_added": injected,
            "paths_skipped": skipped,
            "message": f"Function '{name}' registered with {len(injected)} "
            f"injected paths.",
        }
        logger.info("[tp-rpc] Registration result:\n%s", pprint.pformat(response))
        return response

    except Exception as e:
        response = {
            "status": "error",
            "function": name,
            "paths_added": injected,
            "paths_skipped": skipped,
            "message": str(e),
        }
        logger.error("[tp-rpc] Registration failed:\n%s", pprint.pformat(response))
        return response


@register_function()
def ping():
    """A simple ping function to check if the server is alive."""

    return {
        "dcc_type": globals().get("dcc_type"),
        "instance_name": globals().get("instance_name"),
        "hostname": socket.gethostname(),
        "platform": platform.system(),
    }


@register_function()
def stop_rpc_server() -> str:
    """Stop the RPC server.

    Returns:
        Success message.

    Raises:
        PermissionError: If remote shutdown is disabled.
    """

    if not remote_control_enabled():
        raise PermissionError("Remote shutdown is disabled.")

    shutdown_server()

    return "[tp-rpc] Shutdown signal sent."


@register_function()
def kill_process():
    """Kills the current process.

    Raises:
        PermissionError: If remote kill is disabled.
    """

    if not remote_control_enabled():
        raise PermissionError("Remote kill is disabled.")

    os.kill(os.getpid(), signal.SIGTERM)


@register_function()
def list_registered_functions(verbose: bool = False) -> list[dict] | list[str]:
    """Return all currently registered remote functions.

    Args:
        verbose: If True, include signature and docstring.

    Returns:
        List of function names (if verbose=False) or dicts with name,
            signature, and doc (if verbose=True).

    Raises:
        PermissionError: If remote function listing is disabled.
    """

    if not remote_control_enabled():
        raise PermissionError("Remote function listing is disabled.")

    return list_functions(verbose=verbose)


@register_function()
def describe_remote_function(name: str) -> dict:
    """Return signature and full docstring for a specific registered function.

    Args:
        name: The registered function name.

    Returns:
        Includes 'found', 'signature', and 'doc' keys.

    Raises:
        PermissionError: If remote function introspection is disabled.
    """

    if not remote_control_enabled():
        raise PermissionError("Remote function introspection is disabled.")

    return describe_function(name)


@register_function()
def get_env(name: str) -> str | None:
    """Get the value of an environment variable on the remote server.

    Args:
        name: Environment variable name.

    Returns:
        str | None: The value, or None if not set.

    Raises:
        PermissionError: If environment variable control is disabled.
    """

    if not env_control_enabled():
        raise PermissionError("get_env() is disabled on this server.")

    return os.environ.get(name)


@register_function()
def set_env(name: str, value: str) -> None:
    """Set an environment variable on the remote server.

    Args:
        name: Name of the environment variable.
        value: Value to assign.

    Raises:
        PermissionError: If environment variable control is disabled.
        ValueError: If the name or value is invalid.
    """

    if not env_control_enabled():
        raise PermissionError("set_env() is disabled on this server.")

    os.environ[name] = str(value)


@register_function()
def list_env(prefix: str | None = None) -> dict[str, str]:
    """Return all environment variables on the remote server.

    Args:
        prefix: If provided, filters to vars starting with this prefix.

    Returns:
        Dictionary of env vars and their values.

    Raises:
        PermissionError: If environment variable control is disabled.
    """

    if not env_control_enabled():
        raise PermissionError("list_env() is disabled on this server.")

    env = dict(os.environ)
    if prefix:
        env = {k: v for k, v in env.items() if k.startswith(prefix)}

    return env


@register_function()
def submit_task(function_name: str, *args, **kwargs) -> str:
    """Submit a registered function for asynchronous background execution.

    Args:
        function_name: Name of the registered function.
        *args: Positional arguments.
        **kwargs: Keyword arguments.

    Returns:
        Task ID.
    """

    func = get_function(function_name)
    if not func:
        raise ValueError(f"Function '{function_name}' is not registered")

    return _task_manager.submit(func, *args, **kwargs)


@register_function()
def get_task_status(task_id: str) -> str:
    """Get the status of a task by ID.

    Args:
        task_id: Task ID.

    Returns:
        Status string (pending, running, done, failed, etc.).
    """

    return _task_manager.get_status(task_id)


@register_function()
def get_task_result(task_id: str) -> object:
    """Retrieve the result of a completed task.

    Args:
        task_id: Task ID.

    Returns:
        Result value if task completed successfully.

    Raises:
        Exception: If the task failed or hasn't completed yet.
    """

    return _task_manager.get_result(task_id)


@register_function()
def cancel_task(task_id: str) -> bool:
    """Cancel a pending task.

    Args:
        task_id: Task ID.

    Returns:
        True if cancelled, False otherwise.
    """

    return _task_manager.cancel(task_id)


@register_function()
def list_tasks() -> list[dict]:
    """List all tasks with their current statuses.

    Returns:
        Task metadata including ID, function name, and status.
    """

    return _task_manager.list_tasks()


@register_function()
def publish_event(event_type: str, data: Any, source: str = None) -> str:
    """Publish an event to the event bus.

    Args:
        event_type: The type of event
        data: The event data
        source: The source of the event

    Returns:
        The event ID
    """
    event = Event(event_type, data, source)
    get_event_bus().publish(event)
    return event.id


@register_function()
def subscribe_to_events(event_type: str, callback_function: str) -> bool:
    """Subscribe to events using a callback function.

    This registers a remote function to be called when events occur.

    Args:
        event_type: The event type to subscribe to
        callback_function: The name of a registered function to call

    Returns:
        True if subscription was successful
    """

    callback = get_function(callback_function)
    if not callback:
        raise ValueError(f"Callback function '{callback_function}' not found")

    def event_handler(event: Event):
        try:
            callback(event.type, event.data, event.source, event.id, event.timestamp)
        except Exception as e:
            logger.error(f"[tp-rpc][events] Error in event callback: {e}")

    get_event_bus().subscribe(event_type, event_handler)
    return True


@register_function()
def get_recent_events(event_type: str = None, limit: int = 10) -> list:
    """Get recent events from the event history.

    Args:
        event_type: Optional filter for event type
        limit: Maximum number of events to return

    Returns:
        List of event dictionaries
    """

    events = get_event_bus().get_history(event_type, limit)
    return [
        {
            "id": e.id,
            "type": e.type,
            "data": e.data,
            "source": e.source,
            "timestamp": e.timestamp,
        }
        for e in events
    ]


@register_function()
def get_function_versions(function_name: str) -> dict:
    """Get version information for a function.

    Args:
        function_name: Name of the function

    Returns:
        Dictionary with versions and latest version
    """
    versions = list_versions(function_name)
    latest = get_latest_version(function_name)

    return {"function": function_name, "versions": versions, "latest": latest}


@register_function()
def discover_services(dcc_type: str = None) -> list:
    """Discover available services.

    Args:
        dcc_type: Optional filter by DCC type

    Returns:
        List of service dictionaries
    """
    discovery = get_service_discovery()
    return discovery.get_services(dcc_type)


@register_function()
def start_discovery_listener() -> bool:
    """Start the service discovery listener.

    Returns:
        True if started successfully
    """
    discovery = get_service_discovery()
    discovery.start_listener()
    return True
