from __future__ import annotations

import logging
from typing import Type, Iterator

from . import dpi

# noinspection PyUnresolvedReferences
from Qt import __binding__
from Qt.QtCore import Qt, QObject, QPoint, QRect
from Qt.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QMenu,
    QGraphicsDropShadowEffect,
)
from Qt.QtGui import QCursor, QColor, QGuiApplication, QScreen


_QT_TEST_AVAILABLE = True
try:
    # noinspection PyUnresolvedReferences
    from Qt import QtTest
except ImportError:
    _QT_TEST_AVAILABLE = False

logger = logging.getLogger(__name__)


def is_pyqt() -> bool:
    """
    Returns True if the current Qt binding is PyQt
    """

    return "PyQt" in __binding__


def is_pyqt4() -> bool:
    """
    Returns True if the current Qt binding is PyQt4
    """

    return __binding__ == "PyQt4"


def is_pyqt5() -> bool:
    """
    Returns True if the current Qt binding is PyQt5
    """

    return __binding__ == "PyQt5"


def is_pyside() -> bool:
    """
    Returns True if the current Qt binding is PySide
    """

    return __binding__ == "PySide"


def is_pyside2() -> bool:
    """
    Returns True if the current Qt binding is PySide2
    """

    return __binding__ == "PySide2"


def is_pyside6() -> bool:
    """
    Returns True if the current Qt binding is PySide6
    """

    return __binding__ == "PySide6"


def window_offset(window: QMainWindow | QWidget):
    """
    Returns the window offset.

    :param window: window widget.
    :return: window offset.
    """

    return window.pos() - window.mapToGlobal(QPoint(0, 0))


def widget_center(widget: QWidget) -> QPoint:
    """
    Returns the center of the given widget.

    :param widget: widget whose center we want to retrieve.
    :return: widget center.
    """

    return QPoint(int(widget.width() * 0.5), int(widget.height() * 0.5))


def current_screen(global_pos: QPoint | None = None) -> QScreen:
    """
    Returns current screen instance.

    :return: current screen.
    """

    global_pos = global_pos if global_pos is not None else QCursor.pos()
    return QGuiApplication.screenAt(global_pos)


def current_screen_geometry() -> QRect:
    """
    Returns the current screen geometry.

    :return: screen geometry.
    """

    screen = current_screen()
    return screen.geometry()


def contain_widget_in_screen(widget: QWidget, pos: QPoint | None = None) -> QPoint:
    """
    Contains the position of the widget within the current screen.

    :param widget: widget to check.
    :param pos: point to check.
    :return: widget position within widget.
    """

    if not pos:
        pos = widget.mapToGlobal(QPoint(0, 0))
    else:
        pos = QPoint(pos)
    geo = current_screen_geometry()
    pos.setX(min(max(geo.x(), pos.x()), geo.right() - widget.width()))
    pos.setY(min(max(geo.y(), pos.y()), geo.bottom() - widget.height()))

    return pos


def update_widget_style(widget: QWidget):
    """
    Updates object widget style. Should be called for example when a style name changes.

    :param widget: widget to update style of.
    """

    widget.setStyle(widget.style())


def update_widget_sizes(widget: QWidget):
    """
    Updates the given widget sizes.

    :param widget: widget to update sizes of.
    """

    if not widget:
        return
    widget_layout = widget.layout()
    if widget_layout:
        widget_layout.update()
        widget_layout.activate()


def set_stylesheet_object_name(widget: QWidget, name: str, update: bool = True):
    """
    Sets the widget to have a specific object name used by one the stylesheets.

    :param widget: widget we want to set object name.
    :param name: stylesheet name for the widget.
    :param update: whether to force the update the style of the widget after setting up the stylesheet object name.
    """

    widget.setObjectName(name)
    if update:
        update_widget_style(widget)


def recursively_set_menu_actions_visibility(menu: QMenu, state: bool):
    """
    Recursively sets the visible state of all actions of the given menu.

    :param menu: menu to edit actions visibility of.
    :param state: new visibility status.
    """

    for action in menu.actions():
        sub_menu = action.menu()
        if sub_menu:
            recursively_set_menu_actions_visibility(sub_menu, state)
        elif action.isSeparator():
            continue
        if action.isVisible() != state:
            action.setVisible(state)

    if (
        any(action.isVisible() for action in menu.actions())
        and menu.isVisible() != state
    ):
        menu.menuAction().setVisible(state)


def set_shadow_effect_enabled(
    widget: QWidget, flag: bool
) -> QGraphicsDropShadowEffect | None:
    """
    Sets shadow effect for given widget.

    :param widget: widget to set shadow effect for.
    :param flag: whether to enable shadow effect.
    """

    shadow_effect = None
    if flag:
        shadow_effect = widget.property("shadowEffect")
        if shadow_effect is None:
            shadow_effect = QGraphicsDropShadowEffect(widget)
            widget.setProperty("shadowEffect", shadow_effect)
            shadow_effect.setBlurRadius(dpi.dpi_scale(8))
            shadow_effect.setColor(QColor(0, 0, 0, 150))
            shadow_effect.setOffset(dpi.dpi_scale(2))
        widget.setGraphicsEffect(shadow_effect)
    else:
        # noinspection PyTypeChecker
        widget.setGraphicsEffect(None)

    return shadow_effect


def widget_at(pos: QPoint) -> list[tuple[QWidget, QPoint]]:
    """
    Returns all widgets underneath the given mouse position.

    :param pos: mouse cursor position.
    :return: list of all widgets under given mouse position.
    """

    found_widgets: list[tuple[QWidget, QPoint]] = []
    _widget_at = QApplication.widgetAt(pos)

    widgets_statuses: list[tuple[QWidget, bool]] = []
    while _widget_at:
        found_widgets.append((_widget_at, _widget_at.mapFromGlobal(pos)))
        # make widget invisible to further enquiries
        widgets_statuses.append(
            (_widget_at, _widget_at.testAttribute(Qt.WA_TransparentForMouseEvents))
        )
        _widget_at.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        _widget_at = QApplication.widgetAt(pos)

    # restore attribute
    for widget in widgets_statuses:
        widget[0].setAttribute(Qt.WA_TransparentForMouseEvents, widget[1])

    return found_widgets


def iterate_children(
    widget: QObject, skip: str | None = None, obj_class: Type | None = None
) -> Iterator[QWidget]:
    """
    Iterates over the children of the given widget.

    This function iterates over the children of the given widget, optionally skipping children
    with a specific object name or belonging to a specific class.

    :param widget: The widget whose children to iterate over.
    :param skip: Optional. The object name of children to skip. Defaults to None.
    :param obj_class: Optional. The class of children to include. Defaults to None.
    :return: An iterator of QWidget instances representing the children.
    """

    for child in widget.children():
        yield child
        if skip is not None and child.property(skip):
            continue
        if obj_class is not None and not isinstance(child, obj_class):
            continue
        # noinspection PyTypeChecker
        for grand_child in iterate_children(widget=child, skip=skip):
            yield grand_child


def click_under(
    pos: QPoint,
    under: int = 1,
    button: Qt.MouseButton = Qt.LeftButton,
    modifier: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
):
    """
    Clicks under the widget.

    :param pos: cursor position.
    :param under: number of iterations under.
    :param button: button to simulate click with.
    :param modifier: modifier to simulate click with.
    """

    if not _QT_TEST_AVAILABLE:
        logger.warning("QtTest module is not available in current Qt version!")
        return

    widgets = widget_at(pos)
    QtTest.QTest.mouseClick(widgets[under][0], button, modifier, widgets[under][1])
