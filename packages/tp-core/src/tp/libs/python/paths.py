from __future__ import annotations

import os
import sys
import stat
import inspect
import platform
from pathlib import Path
from collections.abc import Generator

from .names import FindUniqueString


def normalized(path: str | Path) -> str:
    """Reformat a path to have no backwards slashes or double forward slashes.

    Args:
        path: Path to reformat.

    Returns:
        Normalized path with forward slashes only.
    """

    path_obj = Path(path)

    if platform.system().lower() == "windows":
        # Strip leading slashes on windows (IE /C:path/ -> C:/path/)
        path_str = str(path_obj).lstrip("\\/")
        path_obj = Path(path_str)

    return str(path_obj).replace("\\", "/")


def normalized_absolute(path: str | Path) -> str:
    """Return the normalized, absolute path for the supplied path.

    Args:
        path: Path to reformat.

    Returns:
        Normalized, absolute path.
    """

    return normalized(Path(path).resolve())


def canonical_path(path: str | Path, ignore_members: list[str] | None = None) -> str:
    """Determine the absolute path from the given relative path based on the
    caller's location.

    Args:
        path: Relative path to a file/folder.
        ignore_members: Members to ignore in the stack.

    Returns:
        Absolute path to the original caller's root path.
    """

    path_obj = Path(path)

    if path_obj.is_absolute():
        return normalized_absolute(path)

    # Determine the members to ignore in the stack, including this one.
    ignore_members = ignore_members or []
    if not isinstance(ignore_members, list):
        ignore_members = [ignore_members]
    ignore_members.append("canonical_path")

    # Get the current frame and inspect the stack
    frame = inspect.currentframe()
    inspect_stack = inspect.stack()[1:]

    for frame, filename, lineno, function, context, index in inspect_stack:
        if function not in ignore_members:
            break

    base_path = Path(inspect.getfile(frame)).parent
    full_path = base_path / normalized(path)

    return normalized_absolute(full_path.resolve())


def unique_path_name(directory: str | Path, padding: int = 0) -> str:
    """Returns a unique path by adding padding to the given path name if it
    is not unique.

    Args:
        directory: Directory name including the path.
        padding: Where the padding should start.

    Returns:
        New unique directory with the path.
    """

    unique_path = FindUniquePath(str(directory))
    unique_path.padding = padding
    return unique_path.get()


def is_read_only(file_path: str | Path) -> bool:
    """Determines if the file is read-only.

    Args:
        file_path: Path to the file.

    Returns:
        True if the file is read-only, False otherwise.
    """

    path_obj = Path(file_path)

    if not path_obj.is_file():
        return False

    return not os.access(str(path_obj), os.R_OK | os.W_OK)


def ensure_file_is_writable(file_path: str | Path):
    """Ensures that the file is writable.

    Args:
        file_path: Path to the file.
    """

    path_obj = Path(file_path)
    if is_read_only(path_obj):
        path_obj.chmod(stat.S_IWRITE)


def find_first_in_paths(file_name: str, paths: list[str | Path]) -> str:
    """Given a filename or path fragment, this function returns the first
    occurrence of a file with that name in the given list of search paths.

    Args:
        file_name: Name of the file to find.
        paths: List of paths to search in.

    Returns:
        First occurrence of the file in the given paths.

    Raises:
        FileNotFoundError: If the file cannot be found in any of the given
            paths.
    """

    for path in paths:
        path_obj = Path(path)
        candidate = path_obj / file_name
        if candidate.exists():
            return str(candidate)

    raise FileNotFoundError(f"The file {file_name} cannot be found in the given paths")


def find_first_in_environment_variable(
    file_name: str, environment_variable: str
) -> str:
    """Given a filename or path fragment, this function returns the first
    occurrence of a file with that name in the given environment variable.

    Args:
        file_name: Name of the file to find.
        environment_variable: Environment variable to search in.

    Returns:
        First occurrence of the file in the given environment variable.

    Raises:
        FileNotFoundError: If the file cannot be found in the environment
            variable paths.
    """

    return find_first_in_paths(
        file_name, os.environ.get(environment_variable, "").split(os.pathsep)
    )


def find_in_sys_path(file_name: str):
    """Given a filename or path fragment, this function returns the first
    occurrence of a file with that name in the system path.

    Args:
        file_name: Name of the file to find.

    Returns:
        First occurrence of the file in the system path.

    Raises:
        FileNotFoundError: If the file cannot be found in the system path.
    """

    return find_first_in_paths(file_name, sys.path)


def up_directory(path: str, depth: int = 1) -> str:
    """Returns the path up to the given depth.

    Args:
        path: Path to go up from.
        depth: Depth to go up.

    Returns:
        Path up to the given depth.
    """

    _current_depth: int = 1
    while _current_depth < depth:
        path = os.path.dirname(path)
        _current_depth += 1

    return path


def iterate_parent_paths(child_path: str) -> Generator[str, None, None]:
    """Generator that yields all parent paths of the given child path.

    Args:
        child_path: Child path to get parent paths from.

    Yields:
        Parent paths of the given child path.
    """

    path = Path(child_path).resolve()
    for parent in path.parents:
        yield str(parent)


class FindUniquePath(FindUniqueString):
    """Class to find a unique path in a given directory.

    Inherits from FindUniqueString to generate unique path names by appending
    incremental numbers when needed.
    """

    def __init__(self, directory: str | Path):
        """Initializes the `FindUniquePath` with the given directory.

        Args:
            directory: Directory path to search for unique paths. If not provided,
                it defaults to the current working directory.
        """

        directory = Path(directory) if directory else Path.cwd()
        self.parent_path = directory.parent
        base_name = directory.name

        super().__init__(base_name)

    def _get_scope_list(self) -> list[str]:
        """Returns a list of files and folders in the parent path.

        Returns:
            List of files and folders in the parent path.
        """

        try:
            return [item.name for item in self.parent_path.iterdir()]
        except (OSError, PermissionError):
            return []

    def _search(self):
        """Internal function that generates the unique string.

        Returns:
            Unique string path as a POSIX-formatted path string.
        """

        name = super()._search()

        return (self.parent_path / name).as_posix()
