#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains functions and classes to handle Maya Camera Sequencer functionality
"""

from Qt.QtWidgets import QApplication

import maya.cmds as cmds

from tp.core import log

logger = log.tpLogger


class ShotsExporter(object):
    def __init__(self):
        self._shots = None
        self._sequence_file = None
        self._shots_dict = dict()


def open_camera_sequencer_window():
    """
    Opens Maya Camera Sequencer tool
    :return:
    """
    cmds.SequenceEditor()


def close_camera_sequencer_window():
    """
    Closes Maya Camera Sequencer window
    """

    camera_sequencer_window = get_camera_sequencer_window()
    if not camera_sequencer_window:
        return

    camera_sequencer_window.close()


def get_camera_sequencer_window(try_to_open=True):
    """
    Returns Maya Camera Sequencer Window as a Qt widget
    :param try_to_open: bool, Whether to force the opening of the window if it is not already opened
    :return:QMainWindow or None
    """

    camera_sequencer_window = None
    widgets = QApplication.topLevelWidgets()
    for widget in widgets:
        widget_title = widget.windowTitle()
        if widget_title == 'Camera Sequencer':
            camera_sequencer_window = widget
            break

    if not camera_sequencer_window:
        open_camera_sequencer_window()
        if try_to_open:
            camera_sequencer_window = get_camera_sequencer_window(False)

    return camera_sequencer_window


def get_camera_sequencer_panel():
    """
    Returns Maya Camera Sequencer Panel as a QtWidget
    :return: QWidget or None
    """
    from tp.maya.cmds import gui
    open_camera_sequencer_window()
    sequencer = cmds.getPanel(scriptType='sequenceEditorPanel')[0]
    qt_obj = gui.to_qt_object(sequencer)

    return qt_obj


def get_all_scene_shots():
    """
    Returns all shot nodes in current Maya scene
    :return: list(str)
    """

    return cmds.ls(type='shot') or list()


def get_shot_is_muted(shot_node):
    """
    Returns whether given shot node is muted
    :param shot_node: str
    :return: bool
    """

    return cmds.shot(str(shot_node), query=True, mute=True)


def get_shot_track_number(shot_node):
    """
    Returns track where given shot node is located
    :param shot_node: str
    :return: int
    """

    return cmds.getAttr('{}.track'.format(shot_node))


def get_shot_start_frame_in_sequencer(shot_node):
    """
    Returns the start frame of the given shot in sequencer time
    :param shot_node: str
    :return: int
    """

    return int(cmds.shot(shot_node, query=True, sequenceStartTime=True))


def get_shot_end_frame_in_sequencer(shot_node):
    """
    Returns the end frame of the given shot in sequencer time
    :param shot_node: str
    :return: int
    """

    return int(cmds.shot(shot_node, query=True, sequenceEndTime=True))


def get_shot_pre_hold(shot_node):
    """
    Returns shot prehold value
    :param shot_node: str
    :return: int
    """

    return cmds.getAttr('{}.preHold'.format(shot_node))


def get_shot_post_hold(shot_node):
    """
    Returns shot posthold value
    :param shot_node: str
    :return: int
    """

    return cmds.getAttr('{}.postHold'.format(shot_node))


def get_shot_scale(shot_node):
    """
    Returns the scale of the given shot
    :param shot_node: str
    :return: int
    """

    return cmds.getAttr('{}.scale'.format(shot_node))


def get_shot_start_frame(shot_node):
    """
    Returns the start frame of the given shot
    :param shot_node: str
    :return: int
    """

    return cmds.getAttr('{}.startFrame'.format(shot_node))


def get_shot_end_frame(shot_node):
    """
    Returns the end frame of the given shot
    :param shot_node: str
    :return: int
    """

    return cmds.getAttr('{}.endFrame'.format(shot_node))


def get_shot_camera(shot_node):
    """
    Returns camera associated given node
    :param shot_node: str
    :return: str
    """

    camera_connections = cmds.listConnections('{}.currentCamera'.format(shot_node), source=True)
    if not camera_connections:
        return None

    return camera_connections[0]
