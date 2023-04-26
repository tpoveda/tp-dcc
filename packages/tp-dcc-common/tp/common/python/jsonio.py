#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to write/read json files
"""

import os
import json
from collections import OrderedDict

from tp.core import log

logger = log.tpLogger


def validate_json(dict):
    """
    Validates whether the given dictionary can be dumped into a JSON file.

    :param dict dict: dictionary to store.
    :return: True if the dictionary is valid; False otherwise.
    :rtype: bool
    """

    try:
        json.dumps(dict)
        return True
    except Exception:
        return False


def convert_dict_to_string(input_dict):
    """
    Returns a dictionary as a string.

    :param dict input_dict: a dictionary.
    :return: Returns a dictionary as a string.
    :rtype: str
    """

    if not validate_json(input_dict):
        logger.error('The dictionary is not able to convert to a string.')
        return
    return json.dumps(input_dict)


def write_to_file(data, filename, **kwargs):
    """
    Writes data to JSON file.

    :param dict, data: data to store into JSON file.
    :param str filename: name of the JSON file we want to store data into.
    :param dict, kwargs:
    :return: file name of the stored file.
    :rtype: str
    """

    indent = kwargs.pop('indent', 2)

    try:
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=indent, **kwargs)
    except IOError:
        logger.error('Data not saved to file {}'.format(filename))
        return None

    logger.debug('File correctly saved to: {}'.format(filename))

    return filename


def read_file(filename, maintain_order=False):
    """
    Returns data from JSON file.

    :param str filename: name of JSON file we want to read data from.
    :param bool maintain_order: whether to maintain the order of the returned dictionary or not.
    :return: data readed from JSON file as dictionary.
    :return: dict
    """

    if os.stat(filename).st_size == 0:
        return None
    else:
        try:
            with open(filename, 'r') as json_file:
                if maintain_order:
                    data = json.load(json_file, object_pairs_hook=OrderedDict)
                else:
                    data = json.load(json_file)
        except Exception as err:
            logger.warning('Could not read {0}'.format(filename))
            raise err

    return data
