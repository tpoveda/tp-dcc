from __future__ import annotations

import json
import threading
from typing import Any
from datetime import datetime, timezone

import Pyro5.api
import Pyro5.errors
from loguru import logger

from .paths import get_registry_path

_registry_lock = threading.Lock()
_registry_path = get_registry_path()


def register_instance(dcc_type: str, uri: str, instance_name: str | None = None) -> str:
    """Register a DCC instance with a unique name and URI.

    Args:
        dcc_type: DCC type (e.g., "maya", "unreal").
        uri: URI of the Pyro5 server for this instance.
        instance_name: Name of this instance (e.g., "maya_left").

    Returns:
        The name of the instance used in the registry.
    """

    instance_data = {
        "uri": uri,
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
    }

    with _registry_lock:
        registry = _load_registry()
        instances = registry.setdefault(dcc_type, {})

        # Generate a unique name if one isn't provided
        if instance_name is None:
            index = 1
            while f"{dcc_type}-{index}" in instances:
                index += 1
            instance_name = f"{dcc_type}-{index}"

        instances[instance_name] = instance_data

        _save_registry(registry)

    return instance_name


def unregister_instance(dcc_type: str, instance_name: str) -> None:
    """Remove a single DCC instance from the registry.

    Args:
        dcc_type: Type of DCC (e.g., "maya").
        instance_name: Unique name of the instance to remove.
    """

    with _registry_lock:
        registry = _load_registry()
        if dcc_type in registry and instance_name in registry[dcc_type]:
            del registry[dcc_type][instance_name]
            if not registry[dcc_type]:  # Remove the DCC type if empty.
                del registry[dcc_type]
            _save_registry(registry)


def update_heartbeat(dcc_type: str, instance_name: str):
    """Update the heartbeat timestamp for a given DCC instance.

    Args:
        dcc_type: Type of DCC (e.g., "maya").
        instance_name: Unique name of the instance (e.g., "maya-1").
    """

    with _registry_lock:
        registry = _load_registry()
        entry = registry.get(dcc_type, {}).get(instance_name)
        if entry:
            entry["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
            _save_registry(registry)


def get_uri(dcc_type: str, instance_name) -> str | None:
    """Fetch the URI of a DCC instance.

    Args:
        dcc_type: Type of DCC.
        instance_name: Specific instance name, or first if None.

    Returns:
        URI if found, else None.
    """

    with _registry_lock:
        registry = _load_registry()
        dcc_map = registry.get(dcc_type, {})
        if instance_name is None or instance_name == "default":
            for entry in dcc_map.values():
                if isinstance(entry, dict) and "uri" in entry:
                    return entry["uri"]
            return None  # No valid instances found
        else:
            return dcc_map.get(instance_name, {}).get("uri")


def list_instances(
    dcc_type: str | None = None,
) -> dict[str, dict[str, str]]:
    """List all registered instances, optionally by DCC type.

    Args:
        dcc_type (Optional[str]): Type to filter on.

    Returns:
        Mapping of DCCs to their instances.
    """

    cleanup_registry()

    with _registry_lock:
        registry = _load_registry()
        if dcc_type:
            return {dcc_type: registry.get(dcc_type, {})}
        return registry


def generate_and_register_instance_name(dcc_type: str, uri: str) -> str:
    """Atomic function that generates a unique instance name for a given DCC
    type based on existing entries.

    Args:
        dcc_type: DCC type (e.g., "maya").
        uri: URI of the Pyro5 server for this instance.

    Returns:
        New instance name (e.g., "maya-1", "maya-2").
    """

    with _registry_lock:
        registry = _load_registry()
        instances = registry.setdefault(dcc_type, {})
        index = 1
        while f"{dcc_type}-{index}" in instances:
            index += 1
        instance_name = f"{dcc_type}-{index}"
        instances[instance_name] = {
            "uri": uri,
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        }

        _save_registry(registry)

        return instance_name


def clear_dcc_instances(dcc_type: str) -> None:
    """Completely remove all registered instances for a given DCC type.

    Args:
        dcc_type: The DCC type to clear (e.g., "maya").
    """

    with _registry_lock:
        registry = _load_registry()
        if dcc_type in registry:
            del registry[dcc_type]
            _save_registry(registry)


def cleanup_registry(timeout: float = 1.5) -> list[str]:
    """Remove unreachable DCC instances from the registry.

    Args:
        timeout: Seconds to wait before considering a server unreachable.

    Returns:
        A list of instance paths that were removed (e.g., 'maya/maya-2').
    """

    removed: list[str] = []

    with _registry_lock:
        registry = _load_registry()
        for dcc_type, instances in list(registry.items()):
            for instance_name, entry in list(instances.items()):
                uri = entry.get("uri")
                if not uri:
                    continue
                try:
                    proxy = Pyro5.api.Proxy(uri)
                    proxy._pyroTimeout = timeout
                    # noinspection PyProtectedMember
                    proxy._pyroBind()
                except (
                    Pyro5.errors.CommunicationError,
                    Pyro5.errors.TimeoutError,
                ):
                    logger.warning(
                        f"[tp-rpc][cleanup] Removing unreachable: "
                        f"{dcc_type}/{instance_name}"
                    )
                    del registry[dcc_type][instance_name]
                    removed.append(f"{dcc_type}/{instance_name}")

            # Clean up empty groups.
            if not registry[dcc_type]:
                del registry[dcc_type]

        _save_registry(registry)

    return removed


def _load_registry() -> dict[str, dict[str, Any]]:
    """Load the registry from disk.

    Returns:
        The current DCC instance registry.
    """

    if _registry_path.exists():
        with _registry_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    return {}


def _save_registry(registry: dict[str, dict[str, Any]]) -> None:
    """Internal function that saves the current registry state to disk.

    Args:
        registry: The current DCC instance registry.
    """

    _registry_path.parent.mkdir(parents=True, exist_ok=True)
    with _registry_path.open("w", encoding="utf-8") as f:
        # noinspection PyTypeChecker
        json.dump(registry, f, indent=2)
