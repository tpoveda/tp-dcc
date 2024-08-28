from __future__ import annotations

import os
import pathlib

from . import paths, osplatform


def create_file(
    file_name: str,
    directory: str | None = None,
    make_unique: bool = False,
    data: str = "",
) -> str | bool:
    """
    Creates a new file in given directory.

    :param file_name: name of the file to create.
    :param directory: directory where to create the file. If None, file is created in current directory.
    :param make_unique: whether to make the file name unique or not.
    :param data: data to write in the file.
    :return: full path of the created file.
    """

    if directory is None:
        directory = os.path.dirname(file_name)
        file_name = os.path.basename(file_name)

    file_name = "_" if file_name == "/" else file_name.replace("\\", "_")
    full_path = pathlib.Path(directory, file_name).as_posix()

    full_path = paths.unique_path_name(full_path) if make_unique else full_path
    if os.path.isfile(full_path):
        return full_path

    # noinspection PyBroadException
    try:
        open_file = open(full_path, "a")
        open_file.close()
    except Exception:
        return False

    if data:
        with open(full_path, "w") as f:
            f.write(data)

    osplatform.get_permission(full_path)

    return full_path
