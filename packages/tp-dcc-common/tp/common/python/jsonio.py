"""
Utility methods related to write/read json files
"""

from __future__ import annotations

import os
import json

from tp.core import log

logger = log.tpLogger


def validate_json(dictionary_to_validate: dict) -> bool:
    """
    Validates whether the given dictionary can be dumped into a JSON file.

    :param dict dictionary_to_validate: dictionary to store.
    :return: True if the dictionary is valid; False otherwise.
    :rtype: bool
    """

    try:
        json.dumps(dictionary_to_validate)
        return True
    except Exception as err:
        logger.error(err)
        return False


def convert_dict_to_string(input_dict: dict) -> str:
    """
    Returns a dictionary as a string.

    :param dict input_dict: a dictionary.
    :return: Returns a dictionary as a string.
    :rtype: str
    """

    if not validate_json(input_dict):
        logger.error('The dictionary is not able to convert to a string.')
        return ''
    return json.dumps(input_dict)


def write_to_file(data: dict, filename: str, **kwargs) -> str | None:
    """
    Writes data to JSON file.

    :param dict data: data to store into JSON file.
    :param str filename: name of the JSON file we want to store data into.
    :return: file name of the stored file.
    :rtype: str or None
    """

    indent = kwargs.pop('indent', 2)
    validate_data = kwargs.pop('validate_data', False)

    if validate_data:
        if not validate_json(data):
            logger.error('Given data is not JSON serializable')
            return None

    try:
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=indent, **kwargs)
    except IOError:
        logger.error(f'Data not saved to file {filename}')
        return None

    logger.debug(f'File correctly saved to: {filename}')

    return filename


def read_file(filename: str) -> dict | None:
    """
    Returns data from JSON file.

    :param str filename: name of JSON file we want to read data from.
    :return: data read from JSON file as dictionary.
    :return: dict or None
    """

    if os.stat(filename).st_size == 0:
        return None

    try:
        with open(filename, 'r') as json_file:
            data = json.load(json_file)
    except Exception as err:
        logger.exception(f'Could not read {filename}', exc_info=True)
        raise err

    return data
