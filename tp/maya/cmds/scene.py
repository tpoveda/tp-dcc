from __future__ import annotations

import os

from maya import cmds


def is_new_scene() -> bool:
    """
    Returns whether the current scene is a new scene or not.

    :return: True if the current scene is a new scene; False otherwise.
    """

    return len(cmds.file(query=True, sceneName=True)) == 0


def new_scene():
    """
    Creates a new scene.
    """

    cmds.file(new=True, force=True)


def is_save_required() -> bool:
    """
    Returns whether the current scene needs to be saved or not.

    :return: True if the current scene needs to be saved; False otherwise.
    """

    return cmds.file(query=True, modified=True)


def save_scene():
    """
    Saves the current scene.
    """

    if is_new_scene():
        return

    extension = current_extension(include_dot=False)
    file_type = "mayaAscii" if extension == "ma" else "mayaBinary"
    cmds.file(save=True, prompt=False, type=file_type)


def rename_scene(file_path: str):
    """
    Renames the current scene with the given file path.

    :param file_path: new file path to rename the current scene.
    """

    cmds.file(rename=file_path)


def save_scene_as(file_path: str):
    """
    Saves the current scene with the given file path.

    :param file_path: new file path to save the current scene.
    """

    rename_scene(file_path)
    save_scene()

def is_batch_mode() -> bool:
    """
    Returns whether the current DCC is in batch mode or not.

    :return: True if the current DCC is in batch mode; False otherwise.
    """

    return cmds.about(query=True, batch=True)


def current_directory() -> str:
    """
    Returns the current scene directory.

    :return: current scene directory.
    """

    return os.path.dirname(current_file_path())


def current_file_path() -> str:
    """
    Returns the current scene file path.

    :return: current scene file path.
    """

    return (
        os.path.normpath(cmds.file(query=True, sceneName=True))
        if not is_new_scene()
        else ""
    )


def current_file_name(include_name: bool = True, include_extension: bool = True) -> str:
    """
    Returns the current scene file name.

    :param include_name: whether to include the file name.
    :param include_extension: whether to include the file extension.
    :return: current scene file name.
    """

    name, ext = os.path.splitext(os.path.basename(current_file_path()))
    return (name if include_name else "") + (ext if include_extension else "") or ""


def current_extension(include_dot: bool = False) -> str:
    """
    Returns the current scene extension.

    :param include_dot: whether to include the dot in the extension.
    :return: current scene extension.
    """

    ext = os.path.splitext(os.path.basename(current_file_path()))[1]
    return ext if include_dot else ext.lstrip(".")
