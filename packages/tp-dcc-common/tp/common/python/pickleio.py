from __future__ import annotations

import os
import pickle
from typing import Any

from tp.core import log

logger = log.tpLogger


def write_to_file(data: Any, filename: str) -> str | None:
    """
    Writes data to Pickle file.

    :param Any data: data to store into Pickle file.
    :param str filename: name of the Picle file we want to store data into.
    :return: file name of the stored file.
    :rtype: str or None
    """

    try:
        with open(filename, 'wb') as pickle_file:
            pickle.dump(data, pickle_file)
    except IOError:
        return None

    logger.debug('File correctly saved to: {}'.format(filename))

    return filename


def read_file(filename: str) -> dict | None:
    """
    Returns data from Pickle file.

    :param str filename: name of Pickle file we want to read data from.
    :return: data read from Pickle file as dictionary.
    :return: dict or None
    """

    if os.stat(filename).st_size == 0:
        return None

    try:
        with open(filename, 'rb') as pickle_file:
            data = pickle.load(pickle_file)
    except IOError as err:
        logger.exception(f'Could not read {filename}', exc_info=True)
        raise err
    except Exception as err:
        logger.exception(f'Could not read {filename}', exc_info=True)
        raise err

    return data
