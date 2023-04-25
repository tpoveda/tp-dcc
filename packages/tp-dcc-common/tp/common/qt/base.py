#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base functionality for Qt widgets
"""

from Qt import QtCore, QtWidgets, QtGui

from tp.common.resources import theme
from tp.common.qt import qtutils, contexts as qt_contexts
from tp.common.qt.widgets import layouts


def widget(layout=None, parent=None):
    """
    Creates a new base widget.
    :param QLayout layout: main layout of the new widget.
    :param QWidget parent: parent widget.
    :return: newly created widget.
    :rtype: BaseWidget
    """

    new_widget = BaseWidget(layout=layout, parent=parent)
    return new_widget


def frame(layout=None, parent=None):
    """
    Creates a new base frame.
    :param QLayout layout: main layout of the new widget.
    :param QWidget parent: parent widget.
    :return: newly created widget.
    :rtype: BaseFrame
    """

    new_frame = BaseFrame(layout=layout, parent=parent)
    return new_frame


@theme.mixin
class BaseWidget(QtWidgets.QWidget):
    """
    Base class for all QWidgets based items
    """

    def_use_scrollbar = False

    def __init__(self, parent=None, **kwargs):
        super(BaseWidget, self).__init__(parent=parent)

        self._size = self.theme_default_size()
        self._use_scrollbar = kwargs.get('use_scrollbar', self.def_use_scrollbar)

        self._setup_ui(layout=kwargs.get('layout', None))

        self.ui()
        self.setup_signals()

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_size(self):
        """
        Returns the spin box height size
        :return: float
        """

        return self._size

    def _set_size(self, value):
        """
        Sets spin box height size
        :param value: float
        """

        self._size = value
        self.style().polish(self)

    theme_size = QtCore.Property(int, _get_size, _set_size)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def keyPressEvent(self, event):
        return

    def mousePressEvent(self, event):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.AltModifier:
            pos = self.mapToGlobal((self.rect().topLeft()))
            QtWidgets.QWhatsThis.showText(pos, self.whatsThis())
        else:
            super(BaseWidget, self).mousePressEvent(event)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def get_main_layout(self):
        """
        Function that generates the main layout used by the widget
        Override if necessary on new widgets
        :return: QLayout
        """

        return layouts.VerticalLayout(spacing=2, margins=(2, 2, 2, 2))

    def ui(self):
        """
        Function that sets up the ui of the widget
        Override it on new widgets (but always call super)
        """

        pass

    def setup_signals(self):
        """
        Function that set up signals of the widget
        """

        pass

    def set_spacing(self, value):
        """
        Set the spacing used by widget's main layout
        :param value: float
        """

        self.main_layout.setSpacing(value)

    def tiny(self):
        """
        Sets spin box to tiny size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.tiny if widget_theme else theme.Theme.Sizes.TINY

        return self

    def small(self):
        """
        Sets spin box to small size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.small if widget_theme else theme.Theme.Sizes.SMALL

        return self

    def medium(self):
        """
        Sets spin box to medium size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.medium if widget_theme else theme.Theme.Sizes.MEDIUM

        return self

    def large(self):
        """
        Sets spin box to large size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.large if widget_theme else theme.Theme.Sizes.LARGE

        return self

    def huge(self):
        """
        Sets spin box to huge size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.huge if widget_theme else theme.Theme.Sizes.HUGE

        return self

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _setup_ui(self, layout=None):
        """
        Internal function that setup basic widget UI

        :param QLayout or None layout: layout to be used by the widget
        :return:
        """

        self.main_layout = layout or self.get_main_layout()
        if self._use_scrollbar:
            layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
            self.setLayout(layout)
            central_widget = QtWidgets.QWidget()
            central_widget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
            scroll = QtWidgets.QScrollArea()
            scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            scroll.setWidgetResizable(True)
            scroll.setFocusPolicy(QtCore.Qt.NoFocus)
            layout.addWidget(scroll)
            scroll.setWidget(central_widget)
            central_widget.setLayout(self.main_layout)
            self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        else:
            self.setLayout(self.main_layout)


@theme.mixin
class BaseFrame(QtWidgets.QFrame):
    mouseReleased = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        super(BaseFrame, self).__init__(*args, **kwargs)

        self._setup_ui(layout=kwargs.get('layout', None))

        self.ui()
        self.setup_signals()

    def mouseReleaseEvent(self, event):
        self.mouseReleased.emit(event)
        return super(BaseFrame, self).mouseReleaseEvent(event)

    def get_main_layout(self):
        """
        Function that generates the main layout used by the widget
        Override if necessary on new widgets
        :return: QLayout
        """

        return layouts.VerticalLayout(spacing=2, margins=(2, 2, 2, 2))

    def ui(self):
        """
        Function that sets up the ui of the widget
        Override it on new widgets (but always call super)
        """

        pass

    def setup_signals(self):
        pass

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _setup_ui(self, layout=None):
        """
        Internal function that setup basic widget UI

        :param QLayout or None layout: layout to be used by the widget
        :return:
        """

        self.main_layout = layout or self.get_main_layout()
        self.setLayout(self.main_layout)


class ContainerWidget(QtWidgets.QWidget):
    """
    Basic widget used a
    """

    def __init__(self, parent=None):
        super(ContainerWidget, self).__init__(parent)

        layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(layout)

        self.containedWidget = None

    def set_contained_widget(self, widget):
        """
        Sets the current contained widget for this container
        :param widget: QWidget
        """

        self.containedWidget = widget
        if widget:
            widget.setParent(self)
            self.layout().addWidget(widget)

    def clone_and_pass_contained_widget(self):
        """
        Returns a clone of this ContainerWidget
        :return: ContainerWidget
        """

        cloned = ContainerWidget(self.parent())
        cloned.set_contained_widget(self.containedWidget)
        self.set_contained_widget(None)
        return cloned


class DirectoryWidget(BaseWidget):
    """
    Widget that contains variables to store current working directory
    """

    directoryChanged = QtCore.Signal(str)

    def __init__(self, parent=None, **kwargs):

        self._directory = None
        self._last_directory = None

        super(DirectoryWidget, self).__init__(parent=parent, **kwargs)

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, value):
        self._last_directory = self._directory
        self._directory = value
        self.directoryChanged.emit(self._directory)


class PlaceholderWidget(QtWidgets.QWidget):
    """
    Basic widget that loads custom UI
    """

    def __init__(self, *args):
        super(PlaceholderWidget, self).__init__(*args)
        qtutils.load_widget_ui(self)


class ScrollWidget(BaseWidget):
    def __init__(self, border=0, parent=None):
        super(ScrollWidget, self).__init__(parent=parent)

        self.setLayout(layouts.VerticalLayout())

        self._content = QtWidgets.QWidget(parent=self)
        self._content_layout = layouts.VerticalLayout(margins=(0, 0, 0, 0))
        self._content.setLayout(self._content_layout)

        self._scroll_area = QtWidgets.QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self._content)

        self.layout().addWidget(self._scroll_area)

        if not border:
            self._scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)

    @property
    def content_layout(self) -> layouts.VerticalLayout:
        return self._content_layout

    def resizeEvent(self, event:QtGui.QResizeEvent):
        self._scroll_area.resizeEvent(event)

    def add_widget(self, widget_to_add: QtWidgets.QWidget):
        self._content_layout.addWidget(widget_to_add)

    def add_layout(self, layout_to_add: QtWidgets.QLayout):
        self._content_layout.addLayout(layout_to_add)
