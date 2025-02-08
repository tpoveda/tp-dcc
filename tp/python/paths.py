from __future__ import annotations

import os
import stat
import pathlib
import inspect
import platform

from .names import FindUniqueString


def normalized(path: str) -> str:
    """
    Reformat a path to have no backwards slashes or double forward slashes.

    :param path: path to reformat.
    :return: normalized path.
    """

    if platform.system().lower() == "windows":
        # Strip leading slashes on windows (IE /C:path/ -> C:/path/)
        path = path.lstrip("\\/")

    # normpath will collapse redundant path separators, convert slashes to platform efault then manually swap
    # to forward slashes, ignoring the platform default
    return os.path.normpath(path).replace("\\", "/")  # Forward slashes only


def normalized_absolute(path: str) -> str:
    """
    Return the normalized, absolute path for the supplied path.

    :param path: path to reformat.
    :return: normalized, absolute path.
    """

    return normalized(os.path.abspath(path))


def canonical_path(path: str, ignore_members: list[str] | None = None) -> str:
    """
    Determines the absolute path from the given relative path based on the caller's location.

    :param path: relative path to a file/folder.
    :param ignore_members: members to ignore in the stack.
    :return: absolute path to the original callers root path.
    """

    if os.path.isabs(path):
        return normalized_absolute(path)

    # determine the members to ignore in the stack including this one
    ignore_members = ignore_members or []
    if not isinstance(ignore_members, list):
        ignore_members = [ignore_members]
    ignore_members.append("canonical_path")

    # get the current frame and inspect the stack and loop through the inspect stack and break when not a function
    # to ignore.
    frame = inspect.currentframe()
    inspect_stack = inspect.stack()[1:]

    for frame, filename, lineno, function, context, index in inspect_stack:
        if function not in ignore_members:
            break

    base_path = os.path.dirname(inspect.getfile(frame))
    full_path = os.path.join(base_path, normalized(path))

    return normalized_absolute(os.path.realpath(full_path))


def unique_path_name(directory: str, padding: int = 0) -> str:
    """
    Returns a unique path by adding a padding to the given path name if it is not unique.

    :param directory: directory name including path.
    :param padding: where the padding should start.
    :return: new unique directory with path.
    """

    unique_path = FindUniquePath(directory)
    unique_path.padding = padding
    return unique_path.get()


def is_read_only(file_path: str) -> bool:
    """
    Determines if the file is read only.

    :param file_path: path to the file.
    :return: True if the file is read only.
    """

    return (
        not os.access(file_path, os.R_OK | os.W_OK)
        if os.path.isfile(file_path)
        else False
    )


def ensure_file_is_writable(file_path: str):
    """
    Ensures that the file is writable.

    :param file_path: path to the file.
    """

    return os.chmod(file_path, stat.S_IWRITE) if is_read_only(file_path) else None


class FindUniquePath(FindUniqueString):
    """
    Class to find a unique path in a given directory.
    """

    def __init__(self, directory: str):
        directory = directory or os.getcwd()
        self.parent_path = os.path.dirname(directory)
        base_name = os.path.basename(directory)
        super(FindUniquePath, self).__init__(base_name)

    def _get_scope_list(self):
        """
        Returns a list of files and folders in the parent path.

        :return: list of files and folders.
        """

        # noinspection PyBroadException
        try:
            files = os.listdir(self.parent_path)
        except Exception:
            files = []

        return files

    def _search(self):
        """
        Internal function that generates the unique string.

        :return: unique string.
        """

        name = super(FindUniquePath, self)._search()
        return pathlib.Path(self.parent_path, name).as_posix()
