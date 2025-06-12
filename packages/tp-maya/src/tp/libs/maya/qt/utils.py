from __future__ import annotations

from typing import Type

from Qt import QtCompat
from Qt.QtCore import QObject
from Qt.QtWidgets import QWidget, QMainWindow
from maya import OpenMayaUI


def maya_window() -> QMainWindow | None:
    """
    Returns the main Maya Qt window.

    :return: main Maya Qt window.
    """

    ptr = OpenMayaUI.MQtUtil.mainWindow()
    return QtCompat.wrapInstance(int(ptr), QMainWindow) if ptr is not None else None


def maya_window_name() -> str:
    """
    Returns the name of the main Maya window.

    :return: name of the main Maya window.
    """

    return maya_window().objectName() if maya_window() is not None else ""


def maya_viewport() -> QWidget | None:
    """
    Returns the main Maya viewport.

    :return: main Maya viewport.
    """

    ptr = OpenMayaUI.M3dView.active3dView().widget()
    return QtCompat.wrapInstance(int(ptr), QWidget) if ptr is not None else None


def to_qt_object(
    maya_object_name: str, widget_type: Type[QObject] = QWidget
) -> QObject | None:
    """
    Converts the given Maya object name into a Qt object.

    :param maya_object_name: name of the Maya UI element to convert to Qt object.
    :param widget_type: type of the Qt object to convert to.
    :return: Qt object.
    """

    ptr = OpenMayaUI.MQtUtil.findControl(maya_object_name)
    if ptr is None:
        ptr = OpenMayaUI.MQtUtil.findLayout(maya_object_name)
    if ptr is None:
        ptr = OpenMayaUI.MQtUtil.findMenuItem(maya_object_name)
    if ptr is None:
        ptr = OpenMayaUI.MQtUtil.findWindow(maya_object_name)

    return QtCompat.wrapInstance(int(ptr), widget_type) if ptr is not None else None


def to_maya_name(qt_object: QObject) -> str:
    """
    Converts the given Qt object into a Maya object name.

    :param qt_object: Qt object to convert to Maya object name.
    :return: Maya object name.
    """

    return OpenMayaUI.MQtUtil.fullName(qt_object)
