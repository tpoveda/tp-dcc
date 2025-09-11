from __future__ import annotations

import logging
from typing import Type, Any
from collections.abc import Generator

from . import dpi

# noinspection PyUnresolvedReferences
from Qt import QtCompat, __binding__
from Qt.QtCore import Qt, QObject, QPoint, QRect
from Qt.QtWidgets import (
    QApplication,
    QSizePolicy,
    QMainWindow,
    QWidget,
    QMenu,
    QGraphicsDropShadowEffect,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
)
from Qt.QtGui import (
    QCursor,
    QColor,
    QGuiApplication,
    QScreen,
    QImageReader,
    QImageWriter,
)


_QT_TEST_AVAILABLE = True
try:
    # noinspection PyUnresolvedReferences
    from Qt import QtTest
except ImportError:
    _QT_TEST_AVAILABLE = False

_QT_SUPPORTED_EXTENSIONS: list[str] | None = None

logger = logging.getLogger(__name__)


def is_pyqt() -> bool:
    """Return whether the current Qt binding is PyQt.

    Returns:
        `True` if the current Qt binding is PyQt; `False` otherwise.
    """

    return "PyQt" in __binding__


def is_pyqt4() -> bool:
    """Return whether the current Qt binding is PyQt4.

    Returns:
        `True` if the current Qt binding is PyQt4; `False` otherwise.
    """

    return __binding__ == "PyQt4"


def is_pyqt5() -> bool:
    """Return whether the current Qt binding is PyQt5.

    Returns:
        `True` if the current Qt binding is PyQt5; `False` otherwise.
    """

    return __binding__ == "PyQt5"


def is_pyside() -> bool:
    """Return whether the current Qt binding is PySide.

    Returns:
        `True` if the current Qt binding is PySide; `False` otherwise.
    """

    return __binding__ == "PySide"


def is_pyside2() -> bool:
    """Return whether the current Qt binding is PySide2.

    Returns:
        `True` if the current Qt binding is PySide2; `False` otherwise.
    """

    return __binding__ == "PySide2"


def is_pyside6() -> bool:
    """Return whether the current Qt binding is PySide6.


    Returns:
        `True` if the current Qt binding is PySide6; `False` otherwise.
    """

    return __binding__ == "PySide6"


def get_supported_image_extensions() -> list[str]:
    """Get a list of supported image file extensions from Qt.

    Returns:
        List of supported image file extensions.
    """

    global _QT_SUPPORTED_EXTENSIONS
    if _QT_SUPPORTED_EXTENSIONS is None:
        read_formats = QImageReader.supportedImageFormats()
        write_formats = QImageWriter.supportedImageFormats()
        extensions: set[str] = set()
        for format_bytes in read_formats:
            format_str = format_bytes.data().decode("utf-8").lower()
            extensions.add(format_str)
        for format_bytes in write_formats:
            format_str = format_bytes.data().decode("utf-8").lower()
            extensions.add(format_str)

        _QT_SUPPORTED_EXTENSIONS = sorted(list(extensions))

    return _QT_SUPPORTED_EXTENSIONS


# noinspection SpellCheckingInspection
def wrapinstance(ptr: int, base: Type[QObject] | None = None) -> QObject | None:
    """Wrap a pointer pointing to a Maya UI element to a Qt class instance.

    Args:
        ptr: Pointer to the Maya UI element.
        base: Base class to wrap the pointer to.

    Returns:
        Wrapped Qt class instance.
    """

    return QtCompat.wrapInstance(int(ptr), base)


# noinspection SpellCheckingInspection
def unwrapinstance(qobj: QObject) -> int:
    """Unwraps objects with PySide.

    Args:
        qobj: QObject to unwrap.

    Returns:
        Pointer to the `QObject`.
    """

    return int(QtCompat.getCppPointer(qobj)[0])


def window_offset(window: QMainWindow | QWidget) -> QPoint:
    """Return the window offset relative to the screen.

    Args:
        window: Window to get the offset of.

    Returns:
        Window offset.
    """

    return window.pos() - window.mapToGlobal(QPoint(0, 0))


def widget_center(widget: QWidget) -> QPoint:
    """Return the center of the given widget.

    Args:
        widget: Widget to get the center of.

    Returns:
        The center point of the widget.
    """

    return QPoint(int(widget.width() * 0.5), int(widget.height() * 0.5))


def current_screen(global_pos: QPoint | None = None) -> QScreen:
    """Return the current screen instance.

    Args:
        global_pos: global position to check the screen at. If `None`, uses
            the current cursor position.

    Returns:
        The current screen instance.
    """

    global_pos = global_pos if global_pos is not None else QCursor.pos()
    return QGuiApplication.screenAt(global_pos)


def current_screen_geometry() -> QRect:
    """Return the current screen geometry.

    Returns:
        Screen geometry.
    """

    screen = current_screen()
    return screen.geometry()


def contain_widget_in_screen(widget: QWidget, pos: QPoint | None = None) -> QPoint:
    """Return a position that contains the given widget within the current
    screen.

    Notes:
        The position is adjusted so that the widget is fully visible within the
        screen boundaries.

    Args:
        widget: widget to contain within the screen.
        pos: position to check containment at. If `None`, uses the widget's
            current global position.

    Returns:
        A position that contains the widget within the current screen.
    """

    if not pos:
        pos = widget.mapToGlobal(QPoint(0, 0))
    else:
        pos = QPoint(pos)
    geo = current_screen_geometry()
    pos.setX(min(max(geo.x(), pos.x()), geo.right() - widget.width()))
    pos.setY(min(max(geo.y(), pos.y()), geo.bottom() - widget.height()))

    return pos


def update_widget_style(widget: QWidget) -> None:
    """Update object widget style.

    Notes:
        - Should be called when a style name changes.

    Args:
        widget: widget to update the style of.
    """

    widget.setStyle(widget.style())


def update_widget_sizes(widget: QWidget) -> None:
    """Update the given widget sizes.

    Args:
        widget: Widget to update sizes of.
    """

    if not widget:
        return
    widget_layout = widget.layout()
    if widget_layout:
        widget_layout.update()
        widget_layout.activate()


def set_stylesheet_object_name(widget: QWidget, name: str, update: bool = True) -> None:
    """Set the widget to have a specific object name used by one the stylesheet.

    Args:
        widget: The widget we want to set object name.
        name: The stylesheet name for the widget.
        update: Whether to force the update the style of the widget after
            setting up the stylesheet object
    """

    widget.setObjectName(name)
    if update:
        update_widget_style(widget)


def clear_focus_widgets():
    """Clears focus if widgets have clearFocus property."""

    focus_widget = QApplication.focusWidget()
    if focus_widget and focus_widget.property("clearFocus"):
        focus_widget.clearFocus()


def recursively_set_menu_actions_visibility(menu: QMenu, state: bool) -> None:
    """Recursively sets the visible state of all actions of the given menu.

    Args:
        menu: Menu to edit actions visibility of.
        state: New visibility status.
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
    """Set shadow effect for given widget.

    Args:
        widget: Widget to set the shadow effect for.
        flag: Whether to enable shadow effect.

    Returns:
        The shadow effect instance if enabled, `None` otherwise.
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
    """Return all widgets underneath the given mouse position.

    Args:
        pos: Mouse cursor position.

    Returns:
        List of all widgets under the given mouse position.
    """

    found_widgets: list[tuple[QWidget, QPoint]] = []
    _widget_at = QApplication.widgetAt(pos)

    widgets_statuses: list[tuple[QWidget, bool]] = []
    while _widget_at:
        found_widgets.append((_widget_at, _widget_at.mapFromGlobal(pos)))
        # Make the widget invisible to further enquiries.
        widgets_statuses.append(
            (_widget_at, _widget_at.testAttribute(Qt.WA_TransparentForMouseEvents))
        )
        _widget_at.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        _widget_at = QApplication.widgetAt(pos)

    # Restore attribute.
    for widget in widgets_statuses:
        widget[0].setAttribute(Qt.WA_TransparentForMouseEvents, widget[1])

    return found_widgets


def iterate_children(
    widget: QObject, skip: str | None = None, obj_class: Type | None = None
) -> Generator[QObject]:
    """Iterate over the children of the given widget.

    This function iterates over the children of the given widget, optionally
    skipping children with a specific object name or belonging to a specific
    class.

    Args:
        widget: The widget whose children are to iterate over.
        skip: Optional. The object name of children to skip. Defaults to None.
        obj_class: Optional. The class of children to include. Defaults to None.

    Yields:
        An iterator of QWidget instances representing the children.
    """

    for child in widget.children():
        yield child
        if skip is not None and child.property(skip):
            continue
        if obj_class is not None and not isinstance(child, obj_class):
            continue
        for grand_child in iterate_children(widget=child, skip=skip):
            yield grand_child


def click_under(
    pos: QPoint,
    under: int = 1,
    button: Qt.MouseButton = Qt.LeftButton,
    modifier: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    """Click under the provided widget.

    Args:
        pos: Global position to click at.
        under: Number of iterations under.
        button: Button to simulate click with.
        modifier: Modifier to simulate click with.
    """

    if not _QT_TEST_AVAILABLE:
        logger.warning("QtTest module is not available in current Qt version!")
        return

    widgets = widget_at(pos)
    QtTest.QTest.mouseClick(widgets[under][0], button, modifier, widgets[under][1])


def set_vertical_size_policy(widget: QWidget, policy: QSizePolicy.Policy) -> None:
    """Set the vertical policy of the given widget.

    Args:
        widget: The widget to set a vertical policy of.
        policy: The new policy to apply to vertical policy.
    """

    size_policy = widget.sizePolicy()
    size_policy.setVerticalPolicy(policy)
    widget.setSizePolicy(size_policy)


def set_horizontal_size_policy(widget: QWidget, policy: QSizePolicy.Policy) -> None:
    """Set the horizontal policy of the given widget.

    Args:
        widget: The widget to set a horizontal policy of.
        policy: The new policy to apply to horizontal policy.
    """

    size_policy = widget.sizePolicy()
    size_policy.setHorizontalPolicy(policy)
    widget.setSizePolicy(size_policy)


def safe_tree_widget_iterator(
    tree_widget: QTreeWidget,
    flags: QTreeWidgetItemIterator.IteratorFlag
    | QTreeWidgetItemIterator.IteratorFlags = QTreeWidgetItemIterator.All,
) -> Generator[QTreeWidgetItem, Any, None]:
    """Return a safe tree widget iterator for the given item.

    Args:
        tree_widget: The tree widget to create an iterator for.
        flags: The iterator flags to use.

    Returns:
        A safe tree widget item iterator.
    """

    iterator = QTreeWidgetItemIterator(tree_widget, flags=flags)
    while iterator.value():
        yield iterator.value()
        iterator += 1
