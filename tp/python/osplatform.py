from __future__ import annotations

import os
import sys
import stat
import logging
import platform

logger = logging.getLogger(__name__)


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
