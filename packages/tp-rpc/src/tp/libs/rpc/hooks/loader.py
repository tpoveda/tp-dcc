from __future__ import annotations

import os
import sys
import inspect
import pkgutil
import importlib
import importlib.util
from pathlib import Path
from types import ModuleType

from loguru import logger

from . import plugins

# Cache of loaded modules.
_loaded_modules: dict[str, ModuleType] = {}


def load_and_initialize(
    dcc_type: str,
    host: str = "localhost",
    port: int = 0,
    instance_name: str = "default",
):
    """Load and initialize the plugin for a given DCC.

    Args:
        dcc_type: Name of the DCC plugin (e.g., 'maya').
        host: Server host.
        port: Port number.
        instance_name: Unique instance name.

    Raises:
        RuntimeError: If the plugin is not found or fails to initialize.
    """

    found_plugins = discover_plugins()
    plugin = found_plugins.get(dcc_type)
    if not plugin:
        raise RuntimeError(f"DCC hook '{dcc_type}' not found")

    module_name = (
        f"tp.libs.rpc.hooks.plugins.{dcc_type}_plugin"
        if plugin["source"] == "builtin"
        else dcc_type
    )
    mod = importlib.import_module(module_name)
    _loaded_modules[dcc_type] = mod

    mod.initialize(host=host, port=port, instance_name=instance_name)


def discover_plugins() -> dict[str, dict]:
    """Discover all available DCC hook plugins.

    Returns:
        Mapping from dcc type to plugin metadata.
    """

    found_plugins: dict[str, dict] = {}

    # Discover internal plugins
    for _, name, _ in pkgutil.iter_modules(plugins.__path__):
        # noinspection PyBroadException
        try:
            mod = importlib.import_module(
                f"tp.libs.rpc.hooks.plugins.{name}_plugin"
            )
            if hasattr(mod, "initialize") and callable(mod.initialize):
                found_plugins[name] = {
                    "name": name,
                    "doc": inspect.getdoc(mod.initialize) or "",
                    "headless": getattr(mod, "HEADLESS", False),
                    "source": "builtin",
                }
        except Exception:
            continue

    # Discover external plugins
    extra_paths = os.environ.get("TP_DCC_RPC_PLUGIN_PATHS", "")
    for dir_path in extra_paths.split(os.pathsep):
        if not dir_path or not os.path.isdir(dir_path):
            continue

        sys.path.insert(0, dir_path)  # allow import

        for py_file in Path(dir_path).glob("*.py"):
            name = py_file.stem
            if name in found_plugins:
                continue  # skip duplicates

            # noinspection PyBroadException
            try:
                spec = importlib.util.spec_from_file_location(
                    name, str(py_file)
                )
                mod = importlib.util.module_from_spec(spec)
                loader = spec.loader
                if isinstance(loader, importlib.abc.Loader):
                    loader.exec_module(mod)
                    if hasattr(mod, "initialize") and callable(mod.initialize):
                        found_plugins[name] = {
                            "name": name,
                            "doc": inspect.getdoc(mod.initialize) or "",
                            "headless": getattr(mod, "HEADLESS", False),
                            "source": dir_path,
                        }
            except Exception:
                continue

    return found_plugins


def reload_plugin(
    dcc_type: str,
    host: str = "localhost",
    port: int = 0,
    instance_name: str = "default",
):
    """Reload the plugin module and re-initialize.

    Args:
        dcc_type: Plugin name.
        host: Host to connect to.
        port: Port to connect to.
        instance_name: Instance name to connect to.
    """

    mod = _loaded_modules.get(dcc_type)
    if not mod:
        load_and_initialize(dcc_type, host, port, instance_name)
        return

    if hasattr(mod, "shutdown") and callable(mod.shutdown):
        try:
            mod.shutdown()
        except Exception as e:
            logger.warning(f"Plugin {dcc_type} shutdown failed: {e}")

    importlib.reload(mod)
    mod.initialize(host=host, port=port, instance_name=instance_name)
