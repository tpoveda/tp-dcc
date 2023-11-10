#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tp-dcc-maya startup functionality
"""

from __future__ import annotations

import os
import sys
import typing
import inspect
import logging

import maya.cmds as cmds
from maya.api import OpenMaya

from tp.core import dcc
from tp.bootstrap import log
from tp.bootstrap.utils import env, profile
from tp.bootstrap.core import manager, exceptions as bootstrap_exceptions
from tp.common.python import path
from tp.common.resources import api as resources
from tp.maya.meta import base
# from tp.maya.managers import scene
from tp.maya.plugins import loader
from tp.maya.libs.triggers import markingmenuoverride, triggercallbacks

if typing.TYPE_CHECKING:
    from tp.bootstrap.core.package import Package

ORIGINAL_FORMAT_EXCEPTION = None


@profile.profile
def startup(_: Package):
    """
    This function is automatically called by tpDcc packages Manager when environment setup is initialized.
    """

    root_file_path = path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    package = manager.package_from_path(root_file_path)
    if not package:
        raise bootstrap_exceptions.MissingPackage(package)

    logger = setup_logging()

    logger.info('Loading tp-dcc DCC Package: Maya')

    resources_path = path.join_path(os.path.dirname(root_file_path), 'resources')
    resources.register_resource(resources_path)
    dcc.register_resource_path(resources_path)

    try:
        if env.is_mayapy() or env.is_maya_batch():
            logger.debug('Not in maya.exe, skipping tp-dcc-tools menu loading...')
        else:
            from tp.core.managers import tools
            tools.ToolsManager.load(application_name='maya')
            logger.debug('Finished loading tp-dcc-tools framework Maya tools!')
    except Exception:
        logger.error('Failed to load tp-dcc-tools framework Maya tools due to unknown error', exc_info=True)

    # load tp-dcc-maya plugins
    loader.load_all_plugins()

    # initialize metadata manager
    base.MetaRegistry()

    # setup custom marking menu and callbacks
    markingmenuoverride.setup()
    triggercallbacks.create_selection_callback()

    # # setup scene manager
    # scene.SceneManager()


def shutdown(package: Package):
    """
    Shutdown function that is called during tpDcc framework shutdown.
    This function is called at the end of tpDcc framework shutdown.

    :param Package package: package instance.
    """

    if not package:
        raise bootstrap_exceptions.MissingPackage(package)

    logger = log.tpLogger

    logger.info('Shutting down tp-dcc-maya Package...')

    # # unload scene manager
    # scene.SceneManager().stop_all_jobs()

    # reset custom marking menu
    triggercallbacks.remove_selection_callback()
    markingmenuoverride.reset()

    # unload tp-dcc-maya plugins
    loader.unload_all_plugins()

    if env.is_maya():
        from tp.core.managers import tools
        try:
            tools.ToolsManager.close()
        except Exception:
            logger.error('Failed to shutdown currently loaded tools', exc_info=True)

    cmds.flushUndo()


def setup_logging():
    """
    Setup custom Maya logging
    """

    handler = MayaLogHandler()
    handler.setFormatter(logging.Formatter(log.LogsManager().shell_formatter))
    log.tpLogger.addHandler(handler)
    log.rigLogger.addHandler(handler)
    log.animLogger.addHandler(handler)
    log.modelLogger.addHandler(handler)

    return log.tpLogger


class MayaLogHandler(logging.Handler):
    """
    Custom logging handler that displays errors and warnings records with the appropriate color within Maya GUI
    """

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        if record.levelno > logging.WARNING:
            OpenMaya.MGlobal.displayWarning(msg)
        elif record.levelno in (logging.CRITICAL, logging.ERROR):
            OpenMaya.MGlobal.displayError(msg)
        else:
            # Write all messages to sys.__stdout__, which goes to the output window. Only write debug messages here.
            # The script editor is incredibly slow and can easily hang Maya if we have a lot of debug logging on,
            # but the output window is reasonably fast.
            sys.__stdout__.write(f'{msg}\n')
