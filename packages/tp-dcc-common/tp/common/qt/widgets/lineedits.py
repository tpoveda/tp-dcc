#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to create different kind of line edits
"""

from functools import partial

from Qt.QtCore import Qt, Signal, QObject, Property, QTimer
from Qt.QtWidgets import QApplication, QLineEdit, QTextEdit, QTextBrowser
from Qt.QtGui import QDoubleValidator, QIntValidator

# from tp.common.resources import theme
from tp.common.qt import contexts as qt_contexts
from tp.common.qt.widgets import layouts, buttons, browser


def line_edit(text='', read_only=False, placeholder_text='', parent=None):
    """
    Creates a basic line edit widget.

    :param str text: default line edit text.
    :param bool read_only: whether line edit is read only.
    :param str placeholder_text: line edit placeholder text.
    :param QWidget parent: parent widget.
    :return: newly created combo box.
    :rtype: BaseComboBox
    """

    new_line_edit = BaseLineEdit(text=text, parent=parent)
    new_line_edit.setReadOnly(read_only)
    new_line_edit.setPlaceholderText(str(placeholder_text))

    return new_line_edit


def text_browser(parent=None):
    """
    Creates a text browser widget.

    :param QWidget parent: parent widget.
    :return: newly created text browser.
    :rtype: QTextBrowser
    """

    new_text_browser = QTextBrowser(parent=parent)

    return new_text_browser


# @theme.mixin
class BaseLineEdit(QLineEdit, object):
    """
     Basic line edit
     """

    delayTextChanged = Signal(str)

    def __init__(self, text='', input_mode=None, parent=None):
        super(BaseLineEdit, self).__init__(text, parent)

        self._prefix_widget = None
        self._suffix_widget = None
        self._size = self.theme_default_size()

        self._main_layout = layouts.HorizontalLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.addStretch()
        self.setLayout(self._main_layout)

        self.setProperty('history', self.property('text'))
        self.setTextMargins(2, 0, 2, 0)

        if input_mode == 'float':
            self.setValidator(QDoubleValidator())
        elif input_mode == 'int':
            self.setValidator(QIntValidator())

        self._delay_timer = QTimer()
        self._delay_timer.setInterval(500)
        self._delay_timer.setSingleShot(True)
        self._delay_timer.timeout.connect(self._on_delay_text_changed)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_text(self):
        return self.text()

    def _set_text(self, value):
        with qt_contexts.block_signals(self):
            self.setText(value)

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
        if hasattr(self._prefix_widget, 'theme_size'):
            self._prefix_widget.theme_size = self._size
        if hasattr(self._suffix_widget, 'theme_size'):
            self._suffix_widget.theme_size = self._size
        self.style().polish(self)

    theme_size = Property(int, _get_size, _set_size)
    line_text = Property(str, _get_text, _set_text)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def setText(self, text):
        """
        Overrides base QLineEdit setText base function.
        Save history
        :param text: str
        """

        self.setProperty('history', '{}\n{}'.format(self.property('history'), text))
        return super(BaseLineEdit, self).setText(text)

    def clear(self):
        """
        Overrides base QLineEdit clear function
        :return:
        """

        self.setProperty('history', '')
        return super(BaseLineEdit, self).clear()

    def keyPressEvent(self, event):
        """
        Overrides base QLineEdit keyPressEvent function
        :param event: QKeyEvent
        """

        if event.key() not in [Qt.Key_Enter, Qt.Key_Tab]:
            if self._delay_timer.isActive():
                self._delay_timer.stop()
            self._delay_timer.start()
        super(BaseLineEdit, self).keyPressEvent(event)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_delay_duration(self, ms):
        """
        Sets the delay timer duration
        :param ms: float
        """

        self._delay_timer.setInterval(ms)

    def get_prefix_widget(self):
        """
        Returns prefix widget for user to edit
        :return: QWidget
        """

        return self._prefix_widget

    def set_prefix_widget(self, widget):
        """
        Sets the edit line left start widget
        :param widget: QWidget
        :return: QWidget
        """

        if self._prefix_widget:
            index = self._main_layout.indexOf(self._prefix_widget)
            self._main_layout.takeAt(index)
            self._prefix_widget.setVisible(False)
            self._prefix_widget.deleteLater()

        widget.setProperty('combine', 'horizontal')
        widget.setProperty('position', 'left')
        if hasattr(widget, 'theme_size'):
            widget.them_size = self.theme_size

        margin = self.textMargins()
        margin.setLeft(margin.left() + widget.width())
        self.setTextMargins(margin)

        self._main_layout.insertWidget(0, widget)
        self._prefix_widget = widget

        return widget

    def get_suffix_widget(self):
        """
        Returns suffix widget for user to edit
        :return: QWidget
        """

        return self._suffix_widget

    def set_suffix_widget(self, widget):
        """
        Sets the edit line right start widget
        :param widget: QWidget
        :return: QWidget
        """

        if self._suffix_widget:
            index = self._main_layout.indexOf(self._suffix_widget)
            self._main_layout.takeAt(index)
            self._suffix_widget.setVisible(False)
            self._suffix_widget.deleteLater()

        widget.setProperty('combine', 'horizontal')
        widget.setProperty('position', 'right')
        if hasattr(widget, 'theme_size'):
            widget.them_size = self.theme_size

        margin = self.textMargins()
        margin.setRight(margin.right() + widget.width())
        self.setTextMargins(margin)

        self._main_layout.addWidget(widget)
        self._prefix_widget = widget

        return widget

    def search(self):
        """
        Adds a search icon button for line edit
        :return: self
        """

        prefix_btn = buttons.BaseToolButton().image('search').icon_only()
        suffix_btn = buttons.BaseToolButton().image('close').icon_only()
        suffix_btn.clicked.connect(self.clear)
        self.set_prefix_widget(prefix_btn)
        self.set_suffix_widget(suffix_btn)
        self.setPlaceholderText('Enter keyword to search ...')

        return self

    def search_engine(self, text='Search'):
        """
        Adds a search push button to line edit
        :param text: str
        :return: self
        """

        _suffix_btn = buttons.BaseButton(text).primary()
        _suffix_btn.clicked.connect(self.returnPressed)
        _suffix_btn.setFixedWidth(100)
        self.set_suffix_widget(_suffix_btn)
        self.setPlaceholderText('Enter keyword to search ...')

        return self

    def file(self, filters=None):
        """
        Adds a ClickBrowserFileToolButton to line edit
        :param filters:
        :return: self
        """

        _suffix_btn = browser.ClickBrowserFileToolButton()
        _suffix_btn.fileChanged.connect(self.setText)
        _suffix_btn.filters = filters
        self.textChanged.connect(_suffix_btn.set_path)
        self.set_suffix_widget(_suffix_btn)
        self.setPlaceholderText('Click button to browse files')

        return self

    def save_file(self, filters=None):
        """
        Adds a ClickSaveFileToolButton to line edit
        :param filters:
        :return: self
        """

        _suffix_button = browser.ClickSaveFileToolButton()
        _suffix_button.fileChanged.connect(self.setText)
        _suffix_button.filters = filters or list()
        self.textChanged.connect(_suffix_button.set_path)
        self.set_suffix_widget(_suffix_button)
        self.setPlaceholderText('Click button to set save file')

        return self

    def folder(self):
        """
        Adds a ClickBrowserFileToolButton to line edit
        :return: self
        """

        _suffix_btn = browser.ClickBrowserFolderToolButton()
        _suffix_btn.folderChanged.connect(self.setText)
        self.textChanged.connect(_suffix_btn.set_path)
        self.set_suffix_widget(_suffix_btn)
        self.setPlaceholderText('Click button to browse folder')

        return self

    def error(self):
        """
        Shows error in line edit with red style
        :return: self
        """

        def _on_show_detail(self):
            dlg = QTextEdit(self)
            dlg.setReadOnly(True)
            geo = QApplication.desktop().screenGeometry()
            dlg.setGeometry(geo.width() / 2, geo.height() / 2, geo.width() / 4, geo.height() / 4)
            dlg.setWindowTitle('Error Detail Information')
            dlg.setText(self.property('history'))
            dlg.setWindowFlags(Qt.Dialog)
            dlg.show()

        self.setProperty('theme_type', 'error')
        self.setReadOnly(True)
        _suffix_btn = buttons.BaseToolButton().image('delete_message').icon_only()
        _suffix_btn.clicked.connect(partial(_on_show_detail, self))
        self.set_suffix_widget(_suffix_btn)
        self.setPlaceholderText('Error information will be here ...')

        return self

    def tiny(self):
        """
        Sets line edit to tiny size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.tiny if widget_theme else theme.Theme.Sizes.TINY

        return self

    def small(self):
        """
        Sets line edit to small size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.small if widget_theme else theme.Theme.Sizes.SMALL

        return self

    def medium(self):
        """
        Sets line edit to medium size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.medium if widget_theme else theme.Theme.Sizes.MEDIUM

        return self

    def large(self):
        """
        Sets line edit to large size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.large if widget_theme else theme.Theme.Sizes.LARGE

        return self

    def huge(self):
        """
        Sets line edit to huge size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.huge if widget_theme else theme.Theme.Sizes.HUGE

        return self

    def password(self):
        """
        Sets line edit password mode
        """

        self.setEchoMode(QLineEdit.Password)

        return self

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_delay_text_changed(self):
        """
        Internal callback function that is called when delay timer is completed
        """

        self.delayTextChanged.emit(self.text())


class StyledLineEdit(QLineEdit, object):
    """
    Styled line edit that takes a different color if it's empty
    """

    def __init__(self, default='', off_color=(125, 125, 125), on_color=(255, 255, 255), parent=None):
        super(StyledLineEdit, self).__init__(parent=parent)

        self._value = ''
        self._default = ''
        self._off_color = off_color
        self._on_color = on_color

        self.set_default(default)
        self.textChanged.connect(self._on_change)

    def get_value(self):
        if self.text() == self._default:
            return ''
        else:
            return self._value

    def set_value(self, value):
        self._value = value

    value = property(get_value, set_value)

    def focusInEvent(self, event):
        if self.text() == self._default:
            self.setText('')
            self.setStyleSheet(self._get_on_style())

    def focusOutEvent(self, event):
        if self.text() == '':
            self.setText(self._default)
            self.setStyleSheet(self._get_off_style())

    def set_default(self, text):
        self.setText(text)
        self._default = text
        self.setStyleSheet(self._get_off_style())

    def _get_on_style(self):
        return 'QLineEdit{color:rgb(%s, %s, %s);}' % (self._on_color[0], self._on_color[1], self._on_color[2])

    def _get_off_style(self):
        return 'QLineEdit{color:rgb(%s, %s, %s);}' % (self._off_color[0], self._off_color[1], self._off_color[2])

    def _on_change(self, text):
        if text != self._default:
            self.setStyleSheet(self._get_on_style())
            self._value = text
        else:
            self.setStyleSheet(self._get_off_style())


class ClickLineEdit(QLineEdit, object):
    """
    Custom QLineEdit that becomes editable on click or double click
    """

    def __init__(self, text, single=False, double=False, pass_through_click=True):
        super(ClickLineEdit, self).__init__(text)

        self.setReadOnly(True)
        self._editing_style = self.styleSheet()
        self._default_style = "QLineEdit {border: 0;}"
        self.setStyleSheet(self._default_style)
        self.setContextMenuPolicy(Qt.NoContextMenu)

        if single:
            self.mousePressEvent = self.editEvent
        else:
            if pass_through_click:
                self.mousePressEvent = self._mouse_click_pass_through
        if double:
            self.mouseDoubleClickEvent = self.editEvent
        else:
            if pass_through_click:
                self.mousePressEvent = self._mouse_click_pass_through

        self.editingFinished.connect(self._on_edit_finished)

    def focusOutEvent(self, event):
        super(ClickLineEdit, self).focusOutEvent(event)
        self._on_edit_finished()

    def mousePressEvent(self, event):
        event.ignore()

    def mouseReleaseEvent(self, event):
        event.ignore()

    def editEvent(self, event):
        self.setStyleSheet(self._editing_style)
        self.selectAll()
        self.setReadOnly(False)
        self.setFocus()
        event.accept()

    def _mouse_click_pass_through(self, event):
        event.ignore()

    def _on_edit_finished(self):
        self.setReadOnly(True)
        self.setStyleSheet(self._default_style)
        self.deselect()


class FolderLineEdit(BaseLineEdit):
    """
    Custom QLineEdit with drag and drop behaviour for files and folders
    """

    def __init__(self, parent=None):
        super(FolderLineEdit, self).__init__(parent=parent)

        self.setDragEnabled(True)

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def dragEnterEvent(self, event):
        """
        Oerrides base dragEnterEvent function to enable drag behaviour with files and folders
        :param QDragEnterEvent event: Qt drag enter event.
        """

        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """
        Oerrides base dragMoveEvent function to enable drag behaviour with files and folders
        :param QDragMoveEvent event: Qt drag move event.
        """

        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    def dropEvent(self, event):
        """
        Overrides base dropEvent function to enable drag behaviour with files and folders
        :param QDropEvent event: Qt drop event.
        """

        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            self.setText(urls[0].toLocalFile())


class BaseAttrLineEdit(QLineEdit, object):
    attr_type = None
    valueChanged = Signal()

    def __init__(self, parent=None):
        super(BaseAttrLineEdit, self).__init__(parent=parent)

        self.returnPressed.connect(self.update)
        self.editingFinished.connect(self.update)

    def get_value(self):
        return None

    value = property(get_value)


class FloatLineEdit(BaseAttrLineEdit, object):
    attr_type = 'float'
    valueChanged = Signal(float)

    def __init__(self, parent=None):
        super(FloatLineEdit, self).__init__(parent=parent)

    # region Override Properties
    def get_value(self):
        if not self.text():
            return 0.0
        return float(self.text())

    value = property(get_value)

    def setText(self, text):
        super(FloatLineEdit, self).setText('%.2f' % float(text))

    def update(self):
        if self.text():
            self.setText(self.text())
        super(FloatLineEdit, self).update()
        self.valueChanged.emit(float(self.text()))


class IntLineEdit(QLineEdit, object):
    attr_type = 'int'
    valueChanged = Signal(int)

    def __init__(self, parent=None):
        super(IntLineEdit, self).__init__(parent=parent)

    def get_value(self):
        if not self.text():
            return 0
        return int(self.text())

    value = property(get_value)

    def setText(self, text):
        super(IntLineEdit, self).setText('%s' % int(text))

    def update(self):
        if self.text():
            self.setText(self.text())
        super(IntLineEdit, self).update()
        self.valueChanged.emit(int(self.text()))


class MouseSlider(QObject):
    """
    :param StringEdit or BaseLineEdit parent_edit: parent edit to install into.
    :param float or int slide_distance: slide distance.
    :param float or int small_slide_distance: small slide distance.
    :param float or int large_slide_distance: large slide distance.
    :param float or int scroll_distance: distance in pixels to scroll before registering a tick.
    :param bool update_on_tick: whether or not to update on tick.
    """

    tickEvent = Signal(object)
    deltaChanged = Signal(object)
    sliderStarted = Signal()
    sliderFinished = Signal()
    sliderChanged = Signal(object)

    def __init__(self, parent_edit, slide_distance=1, small_slide_distance=0.1, large_slide_distance=5,
                 scroll_distance=1, update_on_tick=False):

        self._edit = parent_edit
        self._update_on_tick = update_on_tick
        self._slide_distance = slide_distance
        self._small_slide_distance = small_slide_distance
        self._large_slide_distance = large_slide_distance
        self._scroll_distance = scroll_distance
        self._press_pos = None
        self._start_value = 0.0
        self._mouse_delta = 0.0
        self._delta_x = 0.0
        self._prev_delta_x = 0.0
        self._enabled = True

        super(MouseSlider, self).__init__()

        self._setup_signals()

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def set_enabled(self, flag):
        """
        Sets whether or not mouse slider is enabled.

        :param bool flag: True to enable mouse slider; False otherwise.
        """

        self._enabled = flag

    def tick(self, delta):
        """
        Run per tick.

        :param float delta: tick delta.
        """

        if not self._enabled:
            return

        value = self._start_value + delta
        self._edit.set_value(value)
        self._edit.update()

        if self._update_on_tick:
            self._edit.textChanged.emit(self._edit.text())
            self._edit.textModified.emit(self._edit.text())
            self.sliderChanged.emit(self._edit.text())

    # ============================================================================================================
    # EVENTS
    # ============================================================================================================

    def mousePressEvent(self, event):
        if not self._enabled:
            return

        if event.button() == Qt.MiddleButton:
            self._press_pos = event.pos()
            self._start_value = self._edit.value()
            self.sliderStarted.emit()

    def mouseMoveEvent(self, event):
        if not self._enabled:
            return

        if self._press_pos is None:
            return

        self._mouse_delta = event.pos().x() - self._press_pos.x()
        if self._mouse_delta % self._scroll_distance == 0:
            self._delta_x = self._mouse_delta / self._scroll_distance
            if self._delta_x != self._prev_delta_x:
                self.deltaChanged.emit(self._delta_x - self._prev_delta_x)
                ctrl = int(event.modifiers() == Qt.KeyboardModifier.ControlModifier)
                shift = int(event.modifiers() == Qt.KeyboardModifier.ShiftModifier)
                if ctrl:
                    self.tickEvent.emit(self._delta_x * self._small_slide_distance)
                elif shift:
                    self.tickEvent.emit(self._delta_x * self._large_slide_distance)
                else:
                    self.tickEvent.emit(self._delta_x * self._slide_distance)

            self._prev_delta_x = self._delta_x

    def mouseReleaseEvent(self, event):
        if not self._enabled:
            return

        if event.button() == Qt.MiddleButton:
            self._press_pos = None
            self._edit.set_value(self._edit.value())
            self._edit.textChanged.emit(self._edit.text())
            self._edit.textModified.emit(self._edit.text())
            self.sliderFinished.emit()

    # ============================================================================================================
    # INTERNAL
    # ============================================================================================================

    def _setup_signals(self):
        """
        Internal function that setup mouse slider signals.
        """

        self._edit.mouseMoved.connect(self.mouseMoveEvent)
        self._edit.mousePressed.connect(self.mousePressEvent)
        self._edit.mouseReleased.connect(self.mouseReleaseEvent)
        self.tickEvent.connect(self.tick)
