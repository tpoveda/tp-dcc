from __future__ import annotations

import os
import time
import errno
import shutil
import pathlib
import fnmatch
import subprocess
from pathlib import Path
from typing import Iterator
from distutils import dir_util

from loguru import logger

from . import osplatform, fileio, paths


def create_folder(
    name: str, directory: str | None = None, make_unique: bool = False
) -> str:
    """Creates a new folder on the given path and with the given name.

    :param name: name of the new directory.
    :param directory: path to the new directory.
    :param make_unique: whether to pad the name with a number to make it unique if the
        folder is not unique.
    :return: Folder name with path. If creation failed, empty strings will be returned.
    """

    full_path: bool = False
    if directory is None:
        full_path = name
    if not name:
        full_path = directory
    if name and directory:
        full_path = pathlib.Path(directory, name).as_posix()
    if make_unique:
        full_path = paths.unique_path_name(directory=full_path)
    if not full_path:
        return ""

    if os.path.isdir(full_path):
        return full_path

    try:
        os.makedirs(full_path)
    except Exception as err:
        logger.warning(f"Could not create folder {full_path} | {err}", exc_info=True)
        return ""

    osplatform.get_permission(full_path)

    return full_path


def walk_level(root_directory: str, level: int | None = None) -> Iterator[str]:
    """Generator function recursively yields all files within given root directory.

    :param root_directory: root directory.
    :param level: optional level to filter by.
    :return: iterated file paths.
    """

    root_directory = root_directory.rstrip(os.path.sep)
    assert os.path.isdir(root_directory)

    if level is None:
        for root, dirs, files in os.walk(root_directory):
            yield root, dirs, files
    else:
        num_sep = root_directory.count(os.path.sep)
        for root, dirs, files in os.walk(root_directory):
            yield root, dirs, files
            num_sep_this = root.count(os.path.sep)
            if num_sep + level <= num_sep_this:
                del dirs[:]


def get_files(
    root_directory: str,
    full_path: bool = True,
    recursive: bool = False,
    pattern: str = "*",
) -> list[str]:
    """Returns files found in the given folder.

    :param root_directory: folder we want to search files on.
    :param full_path: whether full path to the files will be returned otherwise file
        names will be returned.
    :param recursive: whether files should be retrieved recursively.
    :param pattern: specific pattern to filter files to retrieve by name.
    :return: list of files found in the given root folder and sub folders (if recursively is True).
    """

    assert os.path.isdir(root_directory)

    found_files: list[str] = []
    if recursive:
        for dir_path, dir_names, file_names in os.walk(root_directory):
            for file_name in fnmatch.filter(file_names, pattern):
                if full_path:
                    found_files.append(pathlib.Path(dir_path, file_name).as_posix())
                else:
                    found_files.append(file_name)
    else:
        file_names = os.listdir(root_directory)
        for file_name in fnmatch.filter(file_names, pattern):
            file_path = pathlib.Path(root_directory, file_name).as_posix()
            if os.path.isfile(file_path):
                if full_path:
                    found_files.append(file_path)
                else:
                    found_files.append(file_name)

    return found_files


def ensure_folder_exists(
    directory: str, permissions: int | None = None, placeholder: bool = False
) -> bool:
    """Ensure that a given folder exists, optionally setting permissions and
    creating a placeholder file.

    This function checks whether the specified directory exists. If it does
    not, it creates the directory, applies the given permissions (if any),
    and optionally adds a placeholder file to allow detection by version
    control systems that do not track empty folders.

    Args:
        directory: Absolute path of the folder to ensure exists.
        permissions: Unix-style permission bits to set on the created
            directory. Defaults to 0o775 if not provided.
        placeholder: If True, creates a 'placeholder' file in the new
            directory. Useful for ensuring version control systems detect
            the directory.

    Returns:
        True if the directory was created; False if it already existed.

    Raises:
        OSError: If directory creation fails for reasons other than it
        already existing.
    """

    path = Path(directory)
    if path.exists():
        return False

    permissions = permissions or 0o775

    try:
        path.mkdir(parents=True, mode=permissions)
        logger.debug(f"Created directory: {path} with permissions: {oct(permissions)}")

        if placeholder:
            placeholder_path = path / "placeholder"
            if not placeholder_path.exists():
                placeholder_path.write_text(
                    "Automatically generated placeholder file.\n"
                    "This file exists to allow source control systems to "
                    "track this directory.",
                    encoding="utf-8",
                )
                logger.debug(f"Created placeholder file at: {placeholder_path}")
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            logger.error(f"Failed to create directory '{path}': {exc}", exc_info=True)
            raise

    return True


def rename_folder(directory: str, name: str, make_unique: bool = False) -> str | None:
    """Renames given with a new name.

    :param directory: full path to the directory we want to rename
    :param name: new name of the folder we want to rename
    :param make_unique: whether to add a number to the folder name to make it unique
    :return: path of the renamed folder
    """

    base_name = os.path.basename(directory)
    if base_name == name:
        return

    parent_path = os.path.dirname(directory)
    rename_path = pathlib.Path(parent_path, name).as_posix()

    if make_unique:
        rename_path = paths.unique_path_name(directory=rename_path)
    if os.path.exists(rename_path):
        return False

    # noinspection PyBroadException
    try:
        osplatform.get_permission(directory)
        logger.debug(f"rename: {directory} >> {rename_path}")
        os.rename(directory, rename_path)
    except Exception:
        time.sleep(0.1)
        try:
            os.rename(directory, rename_path)
        except Exception as err:
            logger.exception(
                f"Could not rename folder {directory} to {rename_path} | {err}",
                exc_info=True,
            )
            return False

    return rename_path


def copy_folder(
    directory: str,
    directory_destination: str,
    ignore_patterns: str | list[str] | None = None,
) -> str | None:
    """Copies the given directory (and all its contents) into the given destination directory.

    :param directory: absolute path of the directory we want to copy.
    :param directory_destination: absolute path where we want to copy the directory.
    :param ignore_patterns: extensions we want to ignore when copying folder elements.
        For example, if ['txt', 'py'] is given all py and files with those extensions
        will be ignored during the copy operation.
    :return: copy destination directory. If copy operation is not valid, None will be
        returned.
    """

    if not directory or not os.path.isdir(directory):
        return None

    if not ignore_patterns:
        cmd = None
        if osplatform.is_linux():
            cmd = ["rsync", directory, directory_destination, "-azr"]
        elif osplatform.is_windows():
            cmd = [
                "robocopy",
                directory.replace("/", "\\"),
                directory_destination.replace("/", "\\"),
                "/S",
                "/Z",
                "/MIR",
            ]
        if cmd:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            out, err = proc.communicate()
            if err:
                logger.error(err)
        else:
            shutil.copytree(directory, directory_destination)
    else:
        shutil.copytree(
            directory,
            directory_destination,
            ignore=shutil.ignore_patterns(ignore_patterns),
        )

    return directory_destination


def copy_folder_contents(directory, directory_destination, *args, **kwargs):
    """Copies the given directory contents into the given destination directory.

    :param str directory: absolute path of the directory we want to copy.
    :param str directory_destination: absolute path where we want to copy the directory.
    :param list kwargs: list of positional arguments.
    :param dict kwargs: extra keyword arguments.
    :return: True if the copy folder contents operation was succesfull; False otherwise.
    :rtype: bool
    """

    ensure_folder_exists(directory_destination)
    try:
        dir_util.copy_tree(directory, directory_destination, *args, **kwargs)
    except Exception as err:
        logger.exception(
            f"Failed to move contents of {directory} to {directory}: {err}",
            exc_info=True,
        )
        return False

    return True


def move_folder(
    directory: str, directory_destination: str, only_contents: bool = False
) -> bool:
    """Moves the given directory (and all its contents) into the given destination directory.

    :param directory: absolute path of the directory we want to move.
    :param directory_destination: absolute path where we want to move the directory.
    :param only_contents: whether to move the folder or only its contents.
    :return: True if the move folder operation was successfully; False otherwise.
    """

    if not directory or not os.path.isdir(directory):
        return False

    try:
        if only_contents or os.path.isdir(directory_destination):
            file_list = os.listdir(directory)
            for file_name in file_list:
                source = pathlib.Path(directory, file_name).as_posix()
                destination = pathlib.Path(directory_destination, file_name).as_posix()
                if os.path.exists(destination):
                    if os.path.isdir(destination):
                        move_folder(source, destination)
                        continue
                    else:
                        os.remove(destination)
                shutil.move(source, directory_destination)
        else:
            shutil.move(directory, directory_destination)
    except Exception as err:
        logger.exception(
            f"Failed to move {directory} to {directory_destination} | {err}",
            exc_info=True,
        )
        return False

    return True


def delete_folder(folder_name: str, directory: str | None = None) -> str | None:
    """Deletes the folder by name in the given directory.

    :param folder_name: str, name of the folder to delete.
    :param directory: str, the directory path where the folder is stored.
    :return: Full path of the delete folder.
    """

    def delete_read_only_error(action, name, exc):
        """Helper to delete read only files"""

        osplatform.get_permission(name)
        action(name)

    if directory:
        folder_name = folder_name.replace("\\", "_")
        full_path = pathlib.Path(directory, folder_name).as_posix()
    else:
        folder_dir = os.path.dirname(folder_name)
        clean_folder_name = os.path.basename(folder_name).replace("\\", "_")
        full_path = pathlib.Path(folder_dir, clean_folder_name).as_posix()
    if not os.path.isdir(full_path):
        return None

    try:
        shutil.rmtree(full_path, onerror=delete_read_only_error)
    except Exception as exc:
        logger.warning(
            'Could not remove children of path "{}" | {}'.format(full_path, exc)
        )

    return full_path


def clean_folder(directory: str) -> bool:
    """Removes everything in the given directory.

    :param directory: directory we want to clean.
    :return: True if the folder cleanup operation was successfully; False otherwise.
    """

    base_name = os.path.basename(directory)
    dir_name = os.path.dirname(directory)

    if os.path.isdir(directory):
        # noinspection PyBroadException
        try:
            files = get_files(directory)
        except Exception:
            files: list[str] = []
        for f in files:
            fileio.delete_file(f, directory)

        delete_folder(base_name, dir_name)

    if not os.path.isdir(directory):
        create_folder(base_name, dir_name)

    return True
