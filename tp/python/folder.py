from __future__ import annotations

import os
from typing import Iterator


def walk_level(root_directory: str, level: int | None = None) -> Iterator[str]:
    """
    Generator function recursively yields all files within given root directory.

    :param root_directory: root directory.
    :param level: optional level to filter by.
    :return: iterated file paths.
    :rtype: Iterator[str]
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
