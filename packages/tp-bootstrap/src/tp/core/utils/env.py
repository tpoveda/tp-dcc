from __future__ import annotations

import os
import ctypes
import platform
from pathlib import Path
from collections.abc import Sequence

try:
    from ctypes.wintypes import MAX_PATH
except (ImportError, ValueError):
    MAX_PATH = 260


def add_paths_to_env(env_var: str, paths: Sequence[str]):
    """Adds the given paths to the environment variable.

    Args:
        env_var: The name of the environment variable to add the paths to.
        paths: Paths to add to the environment variable
    """

    existing_paths = {
        str(Path(p.strip()).resolve())
        for p in os.getenv(env_var, "").split(os.pathsep)
        if p.strip()
    }

    for new_path in paths:
        normalized = str(Path(new_path.strip()).resolve())
        existing_paths.add(normalized)

    os.environ[env_var] = os.pathsep.join(existing_paths)


def is_windows() -> bool:
    """Checks if the current platform is Windows.

    Returns:
        True if the current platform is Windows; False otherwise.
    """

    return platform.system().lower().startswith("win")


def is_linux() -> bool:
    """Checks if the current platform is Linux.

    Returns:
        True if the current platform is Linux; False otherwise.
    """

    return platform.system().lower().startswith("lin")


def is_mac() -> bool:
    """Checks if the current platform is macOS.

    Returns:
        True if the current platform is macOS; False otherwise.
    """

    plat = platform.system().lower()
    return plat.startswith("mac") or plat.startswith("os") or plat.startswith("darwin")


def is_unix() -> bool:
    """Checks if the current platform is Unix-based (Linux or macOS).

    Returns:
        True if the current platform is Unix-based; False otherwise.
    """

    return is_mac() or is_linux()


def patch_windows_user_home(root_path: str) -> str:
    """Patch Windows '~' paths to use 'My Documents' instead of the home
    directory.

    Args:
        root_path: The original root path, potentially starting with '~'.

    Returns:
        str: The patched absolute path if needed, or the original expanded
            path.
    """

    if is_windows() and root_path.startswith("~"):
        parts = os.path.normpath(root_path).split(os.path.sep)
        dll = ctypes.windll.shell32
        buf = ctypes.create_unicode_buffer(MAX_PATH + 1)
        if dll.SHGetSpecialFolderPathW(None, buf, 0x0005, False):
            return str(os.path.join(buf.value, *parts[1:]))

    return os.path.expanduser(root_path)
