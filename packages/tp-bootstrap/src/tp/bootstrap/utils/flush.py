from __future__ import annotations

import os
import gc
import sys

from loguru import logger


def flush_under(dir_path: str) -> list[tuple[str, str]]:
    """Flushes (removes) all modules that live under the given directory.

    Args:
        dir_path: The absolute path to the top-most directory to search under.

    Returns:
        A list of tuples (module name, module file path) for flushed modules.

    Note:
        You should call `gc.collect()` after calling this function to ensure
        proper garbage collection.
    """

    dir_path = os.path.realpath(dir_path)
    module_paths: list[tuple[str, str]] = []

    for name, module in list(sys.modules.items()):
        if module is None:
            sys.modules.pop(name, None)
            continue

        module_file = getattr(module, "__file__", None)
        if not module_file:
            continue

        module_dir = os.path.dirname(module_file)
        if module_dir.startswith(dir_path):
            module_paths.append((name, module_file))
            sys.modules.pop(name, None)

    logger.debug(f"Flushed {len(module_paths)} modules under {dir_path}")
    return module_paths


def reload_tp(force: bool = False) -> None:
    """Reloads all TP modules listed in the "TP_DCC_BASE_PATHS" environment
    variable.

    This function flushes and reloads all TP DCC modules, which is useful for
    making runtime changes to plugins that may have complex reload
    dependencies.

    Args:
        force: If True, forces the reload of TP DCC modules, even if they
            are not under the specified base paths.

    Example:
        >>> from tp.bootstrap.utils import flush
        >>> flush.reload_tp()
        ```

    Note:
        This will reload all modules under paths specified in the
        "TP_DCC_BASE_PATHS" environment variable.
    """

    base_paths = os.environ.get("TP_DCC_BASE_PATHS", "").split(os.pathsep)

    for base in base_paths:
        if os.path.exists(base):
            flush_under(os.path.realpath(base))

    if force:
        reload_modules(("tp",))

    gc.collect()


def reload_modules(namespaces: tuple[str, ...]):
    """Forcefully reloads all modules that match the given namespaces.

    Args:
        namespaces: A tuple of module name prefixes to reload.
    """

    match_prefixes = tuple(f"{ns}." for ns in namespaces)
    for name in list(sys.modules.keys()):
        if name in namespaces or name.startswith(match_prefixes):
            logger.debug(f"Unloading module: {name}")
            del sys.modules[name]
