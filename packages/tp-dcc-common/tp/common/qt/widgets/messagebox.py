#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that includes classes to create different types of message boxes
"""

from Qt.QtCore import Qt, QEvent
from Qt.QtWidgets import QSizePolicy, QFrame, QDialog, QDialogButtonBox

from tp.core import dcc
from tp.common.python import helpers
# from tp.common.resources import theme
from tp.common.qt import qtutils, animation
from tp.common.qt.widgets import layouts, labels, checkboxes, lineedits


def create_message_box(parent, title, text, width=None, height=None, buttons=None, header_pixmap=None,
                       header_color=None, enable_input_edit=False, enable_dont_show_checkbox=False,
                       theme_to_apply=None):
    """
    Opens a question message box with the given options
    :param parent: QWidget
    :param title: str
    :param text: str
    :param width: int
    :param height: int
    :param buttons: list(QMessageBox.StandardButton)
    :param header_pixmap: QPixmap
    :param header_color: str
    :param enable_input_edit: bool
    :param enable_dont_show_checkbox: bool
    :param theme_to_apply: bool
    :return: MessageBox
    """

    mb = MessageBox(parent=parent, width=width, height=height, enable_input_edit=enable_input_edit,
                    enable_dont_show_checkbox=enable_dont_show_checkbox)
    mb.set_text(text)
    buttons = buttons or QDialogButtonBox.Ok
    mb.set_buttons(buttons)
    if header_pixmap:
        mb.setPixmap(header_pixmap)

    theme_to_apply = theme_to_apply
    if not theme_to_apply:
        if hasattr(parent, 'theme'):
            theme_to_apply = parent.theme()
        else:
            theme_to_apply = theme.Theme()

    mb.setStyleSheet(theme_to_apply.stylesheet())

    header_color = header_color or theme_to_apply.window_dragger_color or "rgb(50, 150, 225)"
    mb.set_header_color(header_color)
    mb.setWindowTitle(title)
    mb.set_title_text(title)

    return mb


def show_message_box(parent, title, text, width=None, height=None, buttons=None, header_pixmap=None,
                     header_color=None, enable_dont_show_checkbox=False, force=False, theme_to_apply=None):
    """
    Opens a question message box with the given options
    :param parent: QWidget
    :param title: str
    :param text: str
    :param width: int
    :param height: int
    :param buttons: list(QMessageBox.StandardButton)
    :param header_pixmap: QPixmap
    :param header_color: str
    :param enable_dont_show_checkbox: bool
    :param force: bool
    :param theme_to_apply: Theme
    :return: MessageBox
    """

    if helpers.is_string(enable_dont_show_checkbox):
        enable_dont_show_checkbox = enable_dont_show_checkbox == 'true'

    clicked_btn = None

    if qtutils.is_control_modifier() or qtutils.is_alt_modifier():
        force = True

    if force or not enable_dont_show_checkbox or not enable_dont_show_checkbox:
        mb = create_message_box(parent=parent, title=title, text=text, width=width, height=height,
                                buttons=buttons, header_pixmap=header_pixmap, header_color=header_color,
                                enable_dont_show_checkbox=enable_dont_show_checkbox, theme_to_apply=theme_to_apply)
        mb.exec_()
        mb.close()

        clicked_btn = mb.clicked_standard_button()
        dont_show_again = mb.is_dont_show_checkbox_checked()

    return clicked_btn


class MessageBox(QDialog, object):

    MAX_WIDTH = 320
    MAX_HEIGHT = 220

    @staticmethod
    def input(parent, title, text, input_text='', width=None, height=None, buttons=None,
              header_pixmap=None, header_color=None, theme_to_apply=None):
        """
        Helper dialog function to get a single text value from the user
        :param parent: QWidget
        :param title: str
        :param text: str
        :param input_text: str
        :param width: int
        :param height: int
        :param buttons: list(QDialogButtonBox.StandardButton)
        :param header_pixmap: QPixmap
        :param header_color: str
        :param theme_to_apply: Theme
        :return: QMessageBox.StandardButton
        """

        buttons = buttons or QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        dialog = create_message_box(parent=parent, title=title, text=text, width=width, height=height,
                                    buttons=buttons, header_pixmap=header_pixmap, header_color=header_color,
                                    enable_input_edit=True, theme_to_apply=theme_to_apply)
        dialog.set_input_text(input_text)
        dialog.exec_()
        clicked_btn = dialog.clicked_standard_button()

        return dialog.input_text(), clicked_btn

    @staticmethod
    def question(parent, title, text, width=None, height=None, buttons=None, header_pixmap=None,
                 header_color=None, enable_dont_show_checkbox=False, theme_to_apply=None):
        """
        Helper dialog function to get a single text value from the user
        :param parent: QWidget
        :param title: str
        :param text: str
        :param width: int
        :param height: int
        :param buttons: list(QDialogButtonBox.StandardButton)
        :param header_pixmap: QPixmap
        :param header_color: str
        :param enable_dont_show_checkbox: bool
        :param theme_to_apply: Theme
        :return: QDialogButtonBox.StandardButton
        """

        buttons = buttons or QDialogButtonBox.Yes | QDialogButtonBox.No | QDialogButtonBox.Cancel
        clicked_btn = show_message_box(parent=parent, title=title, text=text, width=width, height=height,
                                       buttons=buttons, header_pixmap=header_pixmap, header_color=header_color,
                                       enable_dont_show_checkbox=enable_dont_show_checkbox,
                                       theme_to_apply=theme_to_apply)
        return clicked_btn

    @staticmethod
    def warning(parent, title, text, width=None, height=None, buttons=None, header_pixmap=None,
                header_color='rgb(250, 160, 0)', enable_dont_show_checkbox=False, force=False):
        """
        Helper dialog function to open a warning message box with the given options
        :param parent: QWidget
        :param title: str
        :param text: str
        :param width: int
        :param height: int
        :param buttons: list(QDialogButtonBox.StandardButton)
        :param header_pixmap: QPixmap
        :param header_color: str
        :param enable_dont_show_checkbox: bool
        :param force: bool
        :return: QDialogButtonBox.StandardButton
        """

        buttons = buttons or QDialogButtonBox.Yes | QDialogButtonBox.No
        clicked_btn = show_message_box(parent=parent, title=title, text=text, width=width, height=height,
                                       buttons=buttons, header_pixmap=header_pixmap, header_color=header_color,
                                       enable_dont_show_checkbox=enable_dont_show_checkbox, force=force)
        return clicked_btn

    @staticmethod
    def critical(parent, title, text, width=None, height=None, buttons=None, header_pixmap=None,
                 header_color='rgb(230, 80, 80)'):
        """
        Helper dialog function to open a critical/error message box with the given options
        :param parent: QWidget
        :param title: str
        :param text: str
        :param width: int
        :param height: int
        :param buttons: list(QDialogButtonBox.StandardButton)
        :param header_pixmap: QPixmap
        :param header_color: str
        :return: QDialogButtonBox.StandardButton
        """

        buttons = buttons or QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        clicked_btn = show_message_box(parent=parent, title=title, text=text, width=width, height=height,
                                       buttons=buttons, header_pixmap=header_pixmap, header_color=header_color)
        return clicked_btn

    def __init__(self, name='messageBox', width=None, height=None, enable_input_edit=False,
                 enable_dont_show_checkbox=False, parent=None):

        super(MessageBox, self).__init__(parent=parent)

        self._frame = None
        self._animation = None
        self._dont_show_checkbox = False
        self._clicked_button = None
        self._clicked_standard_button = None

        self.setMinimumWidth(width or self.MAX_WIDTH)
        self.setMinimumHeight(height or self.MAX_HEIGHT)
        self.setObjectName(name)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setStyleSheet('background-color: rgb(68, 68, 68, 255);')

        parent = self.parent()
        self._frame = None
        if parent and parent != dcc.main_window():
            parent.installEventFilter(self)
            self._frame = QFrame(parent)
            self._frame.setStyleSheet('background-color: rgba(25, 25, 25, 150);')
            self._frame.setObjectName('messageBoxFrame')
            self._frame.show()
            self.setParent(self._frame)

        self.main_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(self.main_layout)

        self._header = QFrame(self)
        self._header.setFixedHeight(46)
        self._header.setObjectName('messageBoxHeaderFrame')
        self._header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._icon = labels.BaseLabel(parent=self._header)
        self._icon.hide()
        self._icon.setFixedHeight(32)
        self._icon.setFixedHeight(32)
        self._icon.setScaledContents(True)
        self._icon.setAlignment(Qt.AlignTop)
        self._icon.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self._title = labels.BaseLabel(parent=self._header)
        self._title.setObjectName('messageBoxHeaderLabel')
        self._title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        hlayout = layouts.HorizontalLayout(spacing=10, margins=(15, 7, 15, 10))
        hlayout.addWidget(self._icon)
        hlayout.addWidget(self._title)
        self._header.setLayout(hlayout)

        body_layout = layouts.VerticalLayout()
        self._body = QFrame(self)
        self._body.setObjectName('messageBoxBody')
        self._body.setLayout(body_layout)

        self._message = labels.BaseLabel(parent=self._body)
        self._message.setWordWrap(True)
        self._message.setMinimumHeight(15)
        self._message.setAlignment(Qt.AlignLeft)
        self._message.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._message.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        body_layout.addWidget(self._message)
        body_layout.setContentsMargins(15, 15, 15, 15)

        if enable_input_edit:
            self._input_edit = lineedits.BaseLineEdit(parent=self._body)
            self._input_edit.setObjectName('messageBoxInputEdit')
            self._input_edit.setMinimumHeight(32)
            self._input_edit.setFocus()
            body_layout.addStretch(1)
            body_layout.addWidget(self._input_edit)
            body_layout.addStretch(10)

        if enable_dont_show_checkbox:
            msg = 'Do not show this message again'
            self._dont_show_checkbox = checkbox.BaseCheckBox(msg, parent=self._body)
            body_layout.addStretch(10)
            body_layout.addWidget(self._dont_show_checkbox)
            body_layout.addStretch(2)

        self._button_box = QDialogButtonBox(None, Qt.Horizontal, self)
        self._button_box.clicked.connect(self._on_clicked)
        self._button_box.accepted.connect(self._on_accept)
        self._button_box.rejected.connect(self._on_reject)

        self.main_layout.addWidget(self._header)
        self.main_layout.addWidget(self._body)
        body_layout.addWidget(self._button_box)

        self.updateGeometry()

    def eventFilter(self, object, event):
        """
        Overrides base QDialog eventFilter function
        Updates the geometry when the parnet widget changes size
        :param object: QWidget
        :param event: QEvent
        """

        if event.type() == QEvent.Resize:
            self.updateGeometry()
        return super(MessageBox, self).eventFilter(object, event)

    def showEvent(self, event):
        """
        Overrides base QDialog showEvent function
        Fade in hte dialog on show
        :param event: QEvent
        """

        self.updateGeometry()
        self._fade_in()

    def keyPressEvent(self, event):
        if event.key() != Qt.Key_Escape:
            super(MessageBox, self).keyPressEvent(event)

    def updateGeometry(self):
        """
        Overrides base QDialog updateGeometry function
        Updates the geometry to be in the center of it's parent
        """

        frame = self._frame
        if frame:
            frame.setGeometry(self._frame.parent().geometry())
            frame.move(0, 0)
            geometry = self.geometry()
            center_point = frame.geometry().center()
            geometry.moveCenter(center_point)
            geometry.setY(geometry.y() - 50)
            self.move(geometry.topLeft())

    def exec_(self):
        """
        Overrides base QDialog exec_ function
        Shows the dialog as a modal dialog
        :return: variant, int or None
        """

        super(MessageBox, self).exec_()
        return self.clicked_index()

    def button_box(self):
        """
        Returns the button box widget for the dialog
        :return: QDialogButtonBox
        """

        return self._button_box

    def header(self):
        """
        Returns the header frame
        :return: QFrame
        """

        return self._header

    def set_header_color(self, color):
        """
        Sets the header color for the message box
        :param color: str
        """

        self.header().setStyleSheet('background-color: {}'.format(color))

    def set_title_text(self, text):
        """
        Sets the title text to be displayed
        :param text: str
        """

        self._title.setText(text)

    def set_text(self, text):
        """
        Sets the text message to be displayed
        :param text: str
        """

        self._message.setText(str(text))

    def input_text(self):
        """
        Returns the text that the user has given in the input edit
        :return: str
        """

        return self._input_edit.text()

    def set_input_text(self, text):
        """
        Sets the input text
        :param text: str
        """

        self._input_edit.setText(text)
        if text:
            self._input_edit.selectAll()

    def add_button(self, *args):
        """
        Adds a new upsh button with the given text and roled
        """

        self.button_box().addButton(*args)

    def set_buttons(self, buttons):
        """
        Sets the buttons to be displayed in message box
        :param buttons: QMessageBox.StandardButton
        """

        self.button_box().setStandardButtons(buttons)

    def set_pixmap(self, pixmap):
        """
        Sets the pixmap for the message box
        :param pixmap: QPixmap
        """

        self._icon.setPixmap(pixmap)
        self._icon.show()

    def clicked_button(self):
        """
        Returns the button that was clicked
        :return: variant, QPushButton or None
        """

        return self._clicked_button

    def clicked_index(self):
        """
        Returns the button that was clicked by its index
        :return: variant, int or None
        """

        for i, btn in enumerate(self.button_box().buttons()):
            if btn == self.clicked_button():
                return i

    def clicked_standard_button(self):
        """
        Returns the button that was clicked by the user
        :return: variant, QMessageBox.StandardButton or None
        """

        return self._clicked_standard_button

    def is_dont_show_checkbox_checked(self):
        """
        Returns the checked state of the dont show again checkbox
        :return: bool
        """

        if self._dont_show_checkbox:
            return self._dont_show_checkbox.isChecked()
        else:
            return False

    def _fade_in(self, duration=200):
        """
        Internal function that fade in the dialog using opacity effect
        :param duration: int
        :return: QPropertyAnimation
        """
        if self._frame:
            self._animation = animation.fade_in_widget(self._frame, duration=duration)
        return self._animation

    def _fade_out(self, duration=200):
        """
        Internal function that fade out the dialog using opacity effect
        :param duration: int
        :return: QPropertyAnimation
        """
        if self._frame:
            self._animation = animation.fade_out_widget(self._frame, duration=duration)
        return self._animation

    def _on_clicked(self, button):
        """
        Internal callback function triggered when the user clicks a button
        :param button: QPushButton
        """

        self._clicked_button = button
        self._clicked_standard_button = self.button_box().standardButton(button)

    def _on_accept(self):
        """
        Internal callback function triggered when the DialogButtonBox has been accepted
        """

        anim = self._fade_out()
        if anim:
            anim.finished.connect(self._on_accept_animation_finished)
        else:
            self._on_accept_animation_finished()

    def _on_reject(self):
        """
        Internal callback function triggered when the DialogButtonBox has been rejected
        """

        anim = self._fade_out()
        if anim:
            anim.finished.connect(self._on_reject_animation_finished)
        else:
            self._on_reject_animation_finished()

    def _on_accept_animation_finished(self):
        """
        Internal callback function triggered when the animation has finished on accepted
        """

        parent = self._frame or self
        parent.close()
        self.accept()

    def _on_reject_animation_finished(self):
        parent = self._frame or self
        parent.close()
        self.reject()
