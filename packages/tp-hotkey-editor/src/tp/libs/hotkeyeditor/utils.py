from __future__ import annotations

import os
import time
import glob
import shutil

from tp.bootstrap.core import manager


def copy_file(
    destination_path: str, original_path: str, extension: str | None = None
) -> bool:
    """Copy a file from the original path to the destination path.

    Args:
        destination_path: The destination path.
        original_path: The original path.
        extension: Optional extension to add to the destination path.

    Returns:
        bool: True if the file was copied, False otherwise.
    """

    if extension is not None:
        destination_path += extension
        original_path += extension

    if not os.path.isfile(destination_path):
        if not os.path.exists(os.path.dirname(destination_path)):
            os.makedirs(os.path.dirname(destination_path))
        shutil.copyfile(original_path, destination_path)
        return True

    return False


def backup_file(
    file_path: str,
    backup_dir: str = "backup",
    timestamp: bool = True,
    maximum_count: int = 10,
):
    """Create a backup of a file by copying it to a backup directory with an
    optional timestamp.

    Args:
        file_path: The path of the file to back up.
        backup_dir: The name of the backup directory.
        timestamp: Whether to include a timestamp in the backup file name.
        maximum_count: The maximum number of backup files to keep.
    """

    path = os.path.dirname(file_path)

    if timestamp:
        timestamp = time.strftime("_%Y-%m-%d_%H%M%S")

    backup_directory = os.path.join(path, backup_dir)
    if not os.path.exists(backup_directory):
        os.makedirs(backup_directory)

    dst = os.path.join(
        path, backup_directory, get_file_name(file_path), f"{timestamp}.back"
    )
    if os.path.isfile(file_path) and not os.path.isfile(dst):
        shutil.copyfile(file_path, dst)

    files = glob.glob(
        "{}/{}/{}_*.bak".format(path, backup_directory, get_file_name(file_path))
    )
    if len(files) > maximum_count:
        for f in files[maximum_count:]:
            os.remove(f)


def get_file_name(file_path: str, extension: bool = False) -> str:
    """Get the file name from a file path.

    Args:
        file_path: The file path.
        extension: Whether to include the file extension or not.

    Returns:
        The file name.
    """

    if extension:
        return os.path.basename(file_path)

    return os.path.splitext(os.path.basename(file_path))[0]


def remove_prefix(prefix: str, string_to_clean: str) -> str:
    """Remove a prefix from a string if it exists.

    Args:
        prefix: The prefix to remove.
        string_to_clean: The string to clean.

    Returns:
        The cleaned string.
    """

    if string_to_clean.startswith(prefix):
        return string_to_clean[len(prefix) :]

    return string_to_clean


def remove_brackets(string_to_clean: str) -> str:
    """Remove brackets from a string.

    Args:
        string_to_clean: The string to clean.

    Returns:
        The cleaned string.
    """

    if not string_to_clean:
        return string_to_clean

    if string_to_clean[0] == "(" and string_to_clean[-2:] == ");":
        string_to_clean = string_to_clean[1:-2]
    elif string_to_clean[0] == "(" and string_to_clean[-1] == ")":
        string_to_clean = string_to_clean[1:-1]

    return string_to_clean


def is_admin_mode() -> bool:
    """Check if the current user has admin privileges.

    Returns:
        `True` if the user has admin privileges; `False` otherwise.
    """

    return manager.PackagesManager.current().is_admin()
