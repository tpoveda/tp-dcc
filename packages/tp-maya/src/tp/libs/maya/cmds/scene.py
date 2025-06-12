from __future__ import annotations

import os

from maya import cmds


def is_new_scene() -> bool:
    """Return whether the current scene is a new scene or not.

    Returns:
        True if the current scene is a new scene; False otherwise.
    """

    return len(cmds.file(query=True, sceneName=True)) == 0


def new_scene():
    """Create a new scene."""

    # noinspection PyArgumentList
    cmds.file(new=True, force=True)


def is_save_required() -> bool:
    """Return whether the current scene needs to be saved or not.

    Returns:
        True if the current scene needs to be saved; False otherwise.
    """

    return cmds.file(query=True, modified=True)


def save_scene():
    """Saves the current scene."""

    if is_new_scene():
        return

    extension = current_extension(include_dot=False)
    file_type = "mayaAscii" if extension == "ma" else "mayaBinary"
    cmds.file(save=True, prompt=False, type=file_type)


def rename_scene(file_path: str):
    """Rename the current scene with the given file path.

    Args:
        file_path: New file path to rename the current scene.
    """

    cmds.file(rename=file_path)


def save_scene_as(file_path: str):
    """Save the current scene with the given file path.

    Args:
        file_path: New file path to save the current scene.
    """

    rename_scene(file_path)
    save_scene()


def is_batch_mode() -> bool:
    """Return whether the current DCC is in batch mode or not.

    Returns:
        True if the current DCC is in batch mode; False otherwise.
    """

    # noinspection PyTypeChecker,PyArgumentList
    return cmds.about(query=True, batch=True)


def current_directory() -> str:
    """Return the current scene directory.

    Returns:
        Current scene directory.
    """

    return os.path.dirname(current_file_path())


def current_file_path() -> str:
    """Return the current scene file path.

    Returns:
        Current scene file path.
    """

    return (
        os.path.normpath(cmds.file(query=True, sceneName=True))
        if not is_new_scene()
        else ""
    )


def current_file_name(include_name: bool = True, include_extension: bool = True) -> str:
    """Return the current scene file name.

    Args:
        include_name: Whether to include the file name without extension.
        include_extension: Whether to include the file extension.

    Returns:
        Current scene file name.
    """

    name, ext = os.path.splitext(os.path.basename(current_file_path()))
    return (name if include_name else "") + (ext if include_extension else "") or ""


def current_extension(include_dot: bool = False) -> str:
    """Return the current scene extension.

    Args:
        include_dot: Whether to include the dot in the extension.

    Returns:
        Current scene extension.
    """

    ext = os.path.splitext(os.path.basename(current_file_path()))[1]
    return ext if include_dot else ext.lstrip(".")
