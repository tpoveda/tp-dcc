from __future__ import annotations

import os
import inspect
import platform


def normalized(path: str) -> str:
    """
    Reformat a path to have no backwards slashes or double forward slashes.

    :param path: path to reformat.
    :return: normalized path.
    """

    if platform.system().lower() == 'windows':
        # Strip leading slashes on windows (IE /C:path/ -> C:/path/)
        path = path.lstrip('\\/')

    # normpath will collapse redundant path separators, convert slashes to platform efault then manually swap 
    # to forward slashes, ignoring the platform default
    return os.path.normpath(path).replace('\\', '/')  # Forward slashes only


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
    ignore_members.append('canonical_path')

    # get the current frame and inspect the stack and loop through the inspect stack and break when not a function
    # to ignore.
    frame = inspect.currentframe()
    inspect_stack = inspect.stack()[1:]

    for (frame, filename, lineno, function, context, index) in inspect_stack:
        if function not in ignore_members:
            break

    base_path = os.path.dirname(inspect.getfile(frame))
    full_path = os.path.join(base_path, normalized(path))

    return normalized_absolute(os.path.realpath(full_path))
