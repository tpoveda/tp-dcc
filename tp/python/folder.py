from __future__ import annotations

import os
import errno
import logging
from typing import Iterator

logger = logging.getLogger(__name__)


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


def ensure_folder_exists(
    folder_path: str, permissions: int = 0o755, place_holder: bool = False
) -> str:
    """
    Checks that folder given folder exists. If not, folder is created.

    :param folder_path: folder path to check or created.
    :param permissions: folder permission mode.
    :param place_holder: whether to create placeholder text file or not.
    :return: folder path.
    :raise OSError: raise OSError if the creation of the folder fails.
    """

    if os.path.exists(folder_path):
        return folder_path

    try:
        logger.debug("Creating folder {} [{}]".format(folder_path, permissions))
        os.makedirs(folder_path, permissions)
        if place_holder:
            place_path = os.path.join(folder_path, "placeholder")
            if not os.path.exists(place_path):
                with open(place_path, "wt") as fh:
                    fh.write("Automatically generated place holder file")
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise

    return folder_path
