from __future__ import annotations

import os
import time
import glob
import shutil
import pathlib
import logging

from . import paths, osplatform

logger = logging.getLogger(__name__)


def get_file_text(file_path: str) -> str:
    """
    Returns the text stored in a file in a unique string (without parsing).

    :param file_path: absolute path where the text file we want to read text from is
        located in disk.
    :return: read text file.
    """

    try:
        with open(file_path, "r") as open_file:
            file_text = open_file.read()
    except Exception as err:
        logger.exception(f"Error reading file: {file_path}. {err}", exc_info=True)
        return ""

    return file_text


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
    _backup_file = os.path.join(
        directory, backup_directory_name, f"{file_path}{timestamp}.back"
    )
    if os.path.isfile(file_path) and not os.path.isfile(_backup_file):
        shutil.copyfile(file_path, _backup_file)

    # Remove old backups if maximum number of backups is reached.
    files = glob.glob(
        f"{directory}/{backup_directory_name}/{os.path.splitext(os.path.basename(file_path))[0]}_*.bak"
    )
    if len(files) > maximum_backups:
        for f in files[maximum_backups:]:
            os.remove(f)


def copy_file(file_path: str, file_path_destination: str) -> str:
    """
    Copies the given file to a new given directory.

    :param file_path: file to copy with full path.
    :param file_path_destination: destination directory where we want to copy the
        file into.
    :return: the new copied path.
    """

    osplatform.get_permission(file_path)

    if os.path.isfile(file_path):
        if os.path.isdir(file_path_destination):
            file_name = os.path.basename(file_path)
            file_path_destination = pathlib.Path(
                file_path_destination, file_name
            ).as_posix()
        shutil.copy2(file_path, file_path_destination)

    return file_path_destination


def move_file(path1: str, path2: str) -> str:
    """
    Moves the file pointed by path1 under the directory path2.

    :param path1: file with full path.
    :param path2: path where path1 should be moved into.
    :return: the new moved path.
    """

    try:
        shutil.move(path1, path2)
    except Exception as err:
        logger.exception(f"Failed to move {path1} to {path2}: {err}", exc_info=True)
        return ""

    return path2


def delete_file(
    name: str, directory: str | None = None, show_warning: bool = True
) -> str:
    """
    Delete the file by name in the directory.

    :param name: name of the file to delete
    :param directory: the directory where the file is stored
    :param show_warning: whether show warning message if the deletion of the file was
            not possible.
    :return: file path that was deleted.
    """

    if not directory:
        full_path = name
    else:
        full_path = pathlib.Path(directory, name).as_posix()
    if not os.path.isfile(full_path):
        if show_warning:
            logger.warning(f'File "{full_path}" was not deleted.')
        return full_path

    # noinspection PyBroadException
    try:
        osplatform.get_permission(full_path)
    except Exception:
        pass

    # noinspection PyBroadException
    try:
        os.remove(full_path)
    except Exception:
        pass

    return full_path


def rename_file(name: str, directory: str, new_name: str) -> str:
    """
    Renames the given file in the directory with a new name.

    :param name: name of the file to remove.
    :param directory: directory where the file to rename is located.
    :param new_name: new file name.
    :return: new file name path.
    """

    full_path = pathlib.Path(directory, name).as_posix()
    if not os.path.isfile(full_path):
        return full_path

    new_full_path = pathlib.Path(directory, new_name).as_posix()
    if os.path.isfile(new_full_path):
        logger.warning(
            f"A file named {new_name} already exists in the directory: {directory}"
        )
        return full_path

    os.chmod(full_path, 0o777)
    os.rename(full_path, new_full_path)

    return new_full_path


def write_line(file_path: str, line: str, append: bool = False) -> bool:
    """
    Writes a text line to a file.

    :param file_path: str, absolute file path of the file we want to write files in.
    :param line: text line to write.
    :param append: whether to append the text or replace it.
    :return: True if the write lines operation was successful; False otherwise.
    """

    permission = osplatform.get_permission(file_path)
    if not permission:
        return False

    write_string = "a" if append else "w"

    if append:
        line = "\n" + line

    with open(file_path, write_string) as open_file:
        open_file.write(f"{line}\n")

    return True


def write_lines(file_path: str, lines: list[str], append: bool = False) -> bool:
    """
    Writes a list of text lines to a file. Every entry in the list is a new line.

    :param file_path: absolute file path of the file we want to write files in.
    :param lines: list of text lines in which each entry is a new line.
    :param append: whether to append the text or replace it.
    :return: True if the write lines operation was successful; False otherwise.
    """

    permission = osplatform.get_permission(file_path)
    if not permission:
        return False

    write_string = "a" if append else "w"

    text = "\n".join(map(str, lines))
    if append:
        text = "\n" + text

    with open(file_path, write_string) as open_file:
        open_file.write(text)

    return True
