#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpDcc.dccs.houdini
"""

from __future__ import print_function, division, absolute_import

import os
import logging
from tpDcc.core import dcc

from tpDcc.managers import resources

# =================================================================================

PACKAGE = 'tpDcc.dccs.houdini'

# =================================================================================


def create_logger(dev=False):
    """
    Returns logger of current module
    """

    logger_directory = os.path.normpath(os.path.join(os.path.expanduser('~'), 'tpDcc', 'logs'))
    if not os.path.isdir(logger_directory):
        os.makedirs(logger_directory)

    logging_config = os.path.normpath(os.path.join(os.path.dirname(__file__), '__logging__.ini'))

    logging.config.fileConfig(logging_config, disable_existing_loggers=False)
    logger = logging.getLogger(PACKAGE.replace('.', '-'))
    dev = os.getenv('TPDCC_DEV', dev)
    if dev:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    return logger


def init_dcc(dev=False):
    """
    Initializes module
    :param dev: bool, Whether to launch code in dev mode or not
    """

    register_resources()

    create_logger(dev=dev)


def register_resources():
    """
    Registers tpDcc.libs.houdini resources path
    """

    resources_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
    resources.register_resource(resources_path, key=dcc.Dccs.Houdini)
