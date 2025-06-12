from __future__ import annotations

import re
from pathlib import Path
from functools import partial
from typing import Callable, Any

from loguru import logger
from maya import mel, cmds
from maya.api import OpenMaya

SAFE_NAME_REGEX = re.compile(r"^[a-zA-Z_|]\w*$")


def maya_version() -> int:
    """Returns version of the executed Maya, or 0 if not Maya version is found.

    Returns:
        Version of Maya.
    """

    return int(cmds.about(version=True))


def api_version() -> int:
    """Return the Maya API version.

    Returns:
        Version of Maya API.
    """

    return int(cmds.about(apiVersion=True))


def float_version() -> float:
    """Return the Maya version as a float value.

    Returns:
        Version of Maya as a float value.
    """

    return mel.eval("getApplicationVersionAsFloat")


def maya_up_vector() -> OpenMaya.MVector:
    """Return the up vector of the current Maya scene.

    Returns:
        Up vector of the current Maya scene.
    """

    return OpenMaya.MGlobal.upAxis()


def is_safe_name(name: str) -> bool:
    """Return whether the given name is safe or not to be used as a node name.

    Args:
        name: Name to check.

    Returns:
        Whether the given name is safe or not.
    """

    return bool(SAFE_NAME_REGEX.match(name))


def is_plugin_loaded(plugin_name: str) -> bool:
    """Return whether the given plugin is loaded or not.

    Args:
        Plugin name.

    Returns:
        True if the plugin is loaded; False otherwise.
    """

    return cmds.pluginInfo(plugin_name, query=True, loaded=True)


def load_plugin(plugin_name: str, quiet: bool = True) -> bool:
    """Load a plugin with the given name (full path).

    Args:
        plugin_name: Name or path of the plugin to load.
        quiet: Whether to show info if the plugin has been loaded.

    Returns:
        True if the plugin was loaded successfully; False otherwise.
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
    """Unload the given plugin if it is loaded.

    Args:
        plugin_name: Name or path of the plugin to unload.

    Returns:
        True if the plugin was unloaded successfully; False otherwise.
    """

    if not is_plugin_loaded(plugin_name):
        return False

    return bool(cmds.unloadPlugin(plugin_name))


def add_trusted_plugin_location_path(allowed_path: str) -> bool:
    """Add the given path to the list of trusted plugin locations.

    Args:
        allowed_path: Path to add to the trusted plugin locations list.

    Returns:
        True if the operation was successful; False otherwise.
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
    """Remove the given path from the list of trusted plugin locations.

    Args:
        allowed_path: Path to remove from the trusted plugin locations list.

    Returns:
        True if the operation was successful; False otherwise.
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


def create_repeat_command_for_function(function: Callable, *args, **kwargs):
    """Update Maya's repeat-last command with the given function.
    Only functions/static methods/class methods are supported.

    Args:
        function: The function to call when the repeat last command is called.
        args: Arguments to pass to the repeat function.
        kwargs: Keyword arguments to pass to the repeat function.
    """

    _CommandRepeatContainer.set_repeat_command(function, args, kwargs)

    # Create the MEL command to call the repeat function.
    command = f'python("import {__name__};{__name__}._CommandRepeatContainer.run_current_repeat_command()");'
    cmds.repeatLast(addCommand=command, addCommandLabel=function.__name__)


def create_repeat_last_command_decorator(function: Callable) -> Any:
    """Decorator function that updates Maya's repeat-last command with the
    given function.

    Notes:
        Only functions/static methods/class methods are supported.

    Args:
        function: The function to call when the repeat last command is called.

    Returns:
        A wrapper function that calls the original function and updates the
        repeat-last command.
    """

    def inner(*args, **kwargs):
        result = function(*args, **kwargs)
        create_repeat_command_for_function(function, *args, **kwargs)
        return result

    return inner


class _CommandRepeatContainer:
    """Internal class that holds the function to call when the repeat last
    command is called.
    """

    _function_to_repeat: Callable | None = None

    @staticmethod
    def set_repeat_command(function: Callable, args, kwargs):
        """Set the function to call when the repeat last command is called.

        Args:
            function: The function to call when the repeat last command is
                called.
            args: Arguments to pass to the repeat function.
            kwargs: Keyword arguments to pass to the repeat function.
        """

        _CommandRepeatContainer._function_to_repeat = partial(function, *args, **kwargs)

    @staticmethod
    def run_current_repeat_command():
        """Runs the current repeat command function."""

        if _CommandRepeatContainer._function_to_repeat is not None:
            _CommandRepeatContainer._function_to_repeat()

    @staticmethod
    def flush():
        """Flushes the current repeat command function."""

        _CommandRepeatContainer._function_to_repeat = None
