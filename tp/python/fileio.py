from __future__ import annotations

import os
import time
import glob
import shutil
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


def backup_file(
    file_path: str,
    backup_directory_name: str = "backup",
    timestamp: bool = True,
    maximum_backups: int = 10,
):
    """
    Backup a file to a given directory.

    :param file_path: absolute path to the file to back up.
    :param backup_directory_name: directory where to back up the file.
    :param timestamp: whether to add a timestamp to the backup file name or not.
    :param maximum_backups: maximum number of backups to keep.
    """

    directory = os.path.dirname(file_path)
    timestamp = time.strftime("_%Y-%m-%d_%H%M%S") if timestamp else ""

    _backup_directory = os.path.join(directory, backup_directory_name)
    if not os.path.isdir(_backup_directory):
        os.makedirs(_backup_directory)

    # Copy original file to back up directory if it exists and no backup exists.
    backup_file = os.path.join(
        directory, backup_directory_name, f"{file_path}{timestamp}.back"
    )
    if os.path.isfile(file_path) and not os.path.isfile(backup_file):
        shutil.copyfile(file_path, backup_file)

    # Remove old backups if maximum number of backups is reached.
    files = glob.glob(
        f"{directory}/{backup_directory_name}/{os.path.splitext(os.path.basename(file_path))[0]}_*.bak"
    )
    if len(files) > maximum_backups:
        for f in files[maximum_backups:]:
            os.remove(f)
