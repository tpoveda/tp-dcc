from __future__ import annotations

import logging
from pathlib import Path

from maya import mel, cmds

logger = logging.getLogger(__name__)


def maya_version() -> int:
    """
    Returns version of the executed Maya, or 0 if not Maya version is found.

    :return: version of Maya.
    """

    return int(cmds.about(version=True))


def api_version() -> int:
    """
    Returns the Maya API version.

    :return: version of Maya API.
    """

    return int(cmds.about(api=True))


def float_version() -> float:
    """
    Returns the Maya version as a float value.

    :return: version of Maya as float value.
    """

    return mel.eval("getApplicationVersionAsFloat")


def is_plugin_loaded(plugin_name):
    """
    Return whether given plugin is loaded or not
    :param plugin_name: str
    :return: bool
    """

    return cmds.pluginInfo(plugin_name, query=True, loaded=True)


def load_plugin(plugin_name: str, quiet: bool = True) -> bool:
    """
    Loads plugin with the given name (full path).

    :param plugin_name: name or path of the plugin to load.
    :param quiet: whether to show info to user that plugin has been loaded.
    """

    if is_plugin_loaded(plugin_name):
        return True

    try:
        cmds.loadPlugin(plugin_name, quiet=quiet)
    except Exception as exc:
        if not quiet:
            logger.error(f"Impossible to load plugin: {plugin_name} | {exc}")
        return False

    return True


def unload_plugin(plugin_name: str) -> bool:
    """
    Unloads the given plugin if it is loaded.

    :param plugin_name: name or path of the plugin to unload.
    """

    if not is_plugin_loaded(plugin_name):
        return False

    return cmds.unloadPlugin(plugin_name)


def add_trusted_plugin_location_path(allowed_path: str) -> bool:
    """
    Adds the given path to the list of trusted plugin locations.

    :param str allowed_path: path to add do trusted plugin locations list.
    :return: True if the operation was successful; False otherwise.
    """

    if float_version() < 2022:
        return False

    allowed_path = Path(allowed_path).as_posix()
    allowed_paths = cmds.optionVar(query="SafeModeAllowedlistPaths")
    if allowed_path in allowed_paths:
        return False

    cmds.optionVar(stringValueAppend=("SafeModeAllowedlistPaths", allowed_path))

    return True


def remove_trusted_plugin_location_path(allowed_path: str) -> bool:
    """
    Removes the given path from the list of trusted plugin locations.

    :param str allowed_path: path to remove from trusted plugin locations list.
    :return: True if the operation was successful; False otherwise.
    """

    if float_version() < 2022:
        return False

    allowed_path = Path(allowed_path).as_posix()
    allowed_paths = cmds.optionVar(query="SafeModeAllowedlistPaths")
    if allowed_path not in allowed_paths:
        return False

    path_index = allowed_paths.index(allowed_path)
    cmds.optionVar(removeFromArray=("SafeModeAllowedlistPaths", path_index))

    return True
