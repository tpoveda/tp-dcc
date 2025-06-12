from __future__ import annotations

import os
import sys
import stat
import ctypes
import logging
import platform
from pathlib import Path
from collections.abc import Sequence

try:
    from ctypes.wintypes import MAX_PATH
except (ImportError, ValueError):
    MAX_PATH = 260


logger = logging.getLogger(__name__)


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


# noinspection PyBroadException
def get_permission(filepath: str) -> bool:
    """Get permission on a given file path.

    :param filepath: file path to get permission.
    :return: whether the permission was granted or not.
    """

    if os.access(filepath, os.R_OK | os.W_OK | os.X_OK):
        return True

    if filepath.endswith(".pyc"):
        return False

    permission = False
    try:
        permission = oct(os.stat(filepath)[stat.ST_MODE])[-3:]
    except Exception:
        pass
    if not permission:
        return False

    permission = int(permission)
    if permission < 775:
        try:
            os.chmod(filepath, 0o777)
        except Exception:
            logger.warning(
                'Was not possible to gran permission on: "{}"'.format(filepath)
            )
            return False
        return True
    if permission >= 775:
        return True

    try:
        os.chmod(filepath, 0o777)
    except Exception:
        return False

    return True


# noinspection SpellCheckingInspection
def machine_info() -> dict:
    """Returns dictionary with information about the current machine"""

    machine_dict = {
        "pythonVersion": sys.version,
        "node": platform.node(),
        "OSRelease": platform.release(),
        "OSVersion": platform.platform(),
        "processor": platform.processor(),
        "machineType": platform.machine(),
        "env": os.environ,
        "syspaths": sys.path,
        "executable": sys.executable,
    }

    return machine_dict


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
