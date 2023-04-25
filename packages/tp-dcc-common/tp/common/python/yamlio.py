#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to write/read YAML files
"""

import os
import yaml

from tp.core import log
from tp.common.python import yamlordereddictloader

logger = log.tpLogger


def write_to_file(data, filename, **kwargs):

    """
    Writes data to JSON file
    """

    # if '.yml' not in filename:
    #     filename += '.yml'

    indent = kwargs.pop('indent', 2)
    safe = kwargs.pop('safe', False)

    try:
        with open(filename, 'w') as yaml_file:
            if safe:
                yaml.safe_dump(data, yaml_file, indent=indent, **kwargs)
            else:
                yaml.dump(data, yaml_file, indent=indent, **kwargs)
    except IOError:
        logger.error('Data not saved to file {}'.format(filename))
        return None

    logger.debug('File correctly saved to: {}'.format(filename))

    return filename


def read_file(filename, maintain_order=False):

    """
    Get data from JSON file
    """

    if os.stat(filename).st_size == 0:
        return None
    else:
        try:
            with open(filename, 'r') as yaml_file:
                if maintain_order:
                    data = yaml.load(yaml_file, Loader=yamlordereddictloader.Loader)
                else:
                    data = yaml.safe_load(yaml_file)
        except Exception as err:
            logger.warning('Could not read {0}'.format(filename))
            raise err

    return data
