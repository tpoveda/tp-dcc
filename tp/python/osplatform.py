from __future__ import annotations

import os
import sys
import stat
import enum
import logging
import platform

logger = logging.getLogger(__name__)


class Platform(enum.StrEnum):
    """Enum that defines the different platforms."""

    Windows = "Windows"
    Linux = "Linux"
    Mac = "MacOS"


def get_sys_platform() -> str:
    """
    Returns the OS system platform current Python session runs on.

    :return: OS platform.
    """

    if sys.platform.startswith("java"):
        os_name = platform.java_ver()[3][0]
        # "Windows XP", "Windows 7", etc.
        if os_name.startswith("Windows"):
            system = "win32"
        # "Mac OS X", etc.
        elif os.name.startswith("Mac"):
            system = "darwin"
        # "Linux", "SunOS", "FreeBSD", etc.
        else:
            system = "linux2"
    else:
        system = sys.platform

    return system


def get_platform() -> Platform:
    """
    Returns the Platform current Python session runs on.

    :return: OS platform.
    :rtype: Platform
    """

    system_platform = get_sys_platform()

    pl = Platform.Windows
    if "linux" in system_platform:
        pl = Platform.Linux
    elif system_platform == "darwin":
        pl = Platform.Mac

    return pl


def is_linux() -> bool:
    """
    Check to see if current platform is Linux.

    :return: True if the current platform is Linux; False otherwise.
    """

    current_platform = get_platform()
    return current_platform == Platform.Linux


def is_mac() -> bool:
    """
    Check to see if current platform is Mac.

    :return: True if the current platform is macOS; False otherwise.
    """

    current_platform = get_platform()
    return current_platform == Platform.Mac


def is_windows() -> bool:
    """
    Check to see if current platform is Windows.

    :return: True if the current platform is Windows; False otherwise.
    """

    current_platform = get_platform()
    return current_platform == Platform.Windows


# noinspection PyBroadException
def get_permission(filepath: str) -> bool:
    """
    Get permission on a given file path.

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
    """
    Returns dictionary with information about the current machine
    """

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
