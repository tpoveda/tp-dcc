#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with playblasts
"""

import os
import glob

import maya.cmds
import maya.mel

from tp.core import log
from tp.common.python import osplatform

logger = log.tpLogger


class PlayblastRenderers(object):
    VIEWPORT2 = 'vp2Renderer'
    OPENGL = 'base_OpenGL_Renderer'
    HW_OPENGL = 'hwRender_OpenGL_Renderer'
    STUB = 'stub_Renderer'


class PlayblastError(Exception):
    """
    Class to raise playblast related exceptions
    """

    pass


def get_playblast_formats():
    """
    Returns all formats available for Maya playblast
    :return: list<str>
    """

    maya.cmds.currentTime(maya.cmds.currentTime(query=True))
    return maya.cmds.playblast(query=True, format=True)


def get_playblast_compressions(format='avi'):
    """
    Returns playblast compression for the given format
    :param format: str, format to check compressions for
    :return: list<str>
    """

    maya.cmds.currentTime(maya.cmds.currentTime(query=True))
    return maya.mel.eval('playblast -format "{0}" -query -compression'.format(format))


def fix_playblast_output_path(file_path):
    """
    Workaround a bug in maya.maya.cmds.playblast to return a correct playblast
    When the `viewer` argument is set to False and maya.maya.cmds.playblast does not
    automatically open the playblasted file the returned filepath does not have
    the file's extension added correctly.
    To workaround this we just glob.glob() for any file extensions and assume
    the latest modified file is the correct file and return it.
    :param file_path: str
    :return: str
    """

    if file_path is None:
        logger.warning('Playblast did not result in output path. Maybe it was interrupted!')
        return

    if not os.path.exists(file_path):
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        parts = filename.split('.')
        if len(parts) == 3:
            query = os.path.join(directory, '{}.*.{}'.format(parts[0], parts[-1]))
            files = glob.glob(query)
        else:
            files = glob.glob('{}.*'.format(file_path))

        if not files:
            raise RuntimeError('Could not find playblast from "{}"'.format(file_path))

        file_path = max(files, key=os.path.getmtime)

    return file_path


def playblast(filename, model_panel, start_frame, end_frame, width, height, step=1, renderer=None, off_screen=False):
    """
    Do a playblast with given parameters
    :param filename: str
    :param model_panel: str
    :param start_frame: int
    :param end_frame: int
    :param width: int
    :param height: int
    :param step: int
    :param renderer: PlayblastRenderers
    :param off_screen: bool
    :return: str
    """

    from tpDcc.dccs.maya.core import gui

    if osplatform.is_linux():
        off_screen = True

    logger.info('Playblasting "{}"'.format(filename))
    if start_frame == end_frame and os.path.exists(filename):
        os.remove(filename)

    frame = [i for i in range(start_frame, end_frame + 1, step)]

    model_panel = model_panel or gui.current_model_panel()
    if maya.cmds.modelPanel(model_panel, query=True, exists=True):
        maya.cmds.setFocus(model_panel)
        if renderer:
            maya.cmds.modelEditor(model_panel, edit=True, rendererName=renderer)

    name, compression = os.path.splitext(filename)
    filename = filename.replace(compression, '')
    compression = compression.replace('.', '')

    path = maya.cmds.playblast(
        format='image', viewer=False, percent=100, quality=100,
        frame=frame, width=width, height=height, filename=filename,
        endTime=end_frame, startTime=start_frame, offScreen=off_screen,
        forceOverwrite=True, showOrnaments=False, compression=compression
    )
    if not path:
        raise PlayblastError('Playblast was cancelled by user!')

    source = path.replace('####', str(int(0)).rjust(4, '0'))
    if start_frame == end_frame:
        target = source.replace('.0000.', '.')
        logger.debug('Renaming "{}" > "{}"'.format(source, target))
        os.rename(source, target)
        source = target

    logger.info('Playblasted "{}"'.format(source))

    return source
