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


def write_to_file(data, filename, **kwargs):

    """
    Writes data to JSON file
    """

    # if '.json' not in filename:
    #     filename += '.json'

    indent = kwargs.pop('indent', 2)

    try:
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=indent, **kwargs)
    except IOError:
        logger.error('Data not saved to file {}'.format(filename))
        return None

    logger.info('File correctly saved to: {}'.format(filename))

    return filename


def read_file(filename, as_ordered_dict=False):

    """
    Get data from JSON file
    """

    if os.stat(filename).st_size == 0:
        return None
    else:
        try:
            with open(filename, 'r') as json_file:
                if as_ordered_dict:
                    data = json.load(json_file, object_pairs_hook=OrderedDict)
                else:
                    data = json.load(json_file)
        except Exception as err:
            logger.warning('Could not read {0}'.format(filename))
            raise err

    return data
