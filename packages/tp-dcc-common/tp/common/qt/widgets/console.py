#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains console widgets
"""

import logging
from io import StringIO

from Qt.QtCore import Qt, QSize, QStringListModel
from Qt.QtWidgets import QSizePolicy, QLineEdit, QTextEdit, QCompleter, QAction
from Qt.QtGui import QFont, QTextCursor

from tp.common.python import helpers


class ConsoleInput(QLineEdit, object):
    def __init__(self, commands=[], parent=None):
        super(ConsoleInput, self).__init__(parent=parent)

        self._commands = commands

        self._model = QStringListModel()
        self._model.setStringList(self._commands)
        self._completer = QCompleter(self)
        self._completer.setModel(self._model)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self._completer)
        self.setFont(QFont('Arial', 9, QFont.Bold, False))


class Console(QTextEdit, object):
    def __init__(self, parent=None):
        super(Console, self).__init__(parent=parent)

        self._buffer = StringIO()

        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(size_policy)

        self.setReadOnly(True)
        self.setMaximumSize(QSize(16777215, 16777215))
        self.setFocusPolicy(Qt.StrongFocus)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._generate_context_menu)

    def __getattr__(self, attr):
        """
        Fall back to the buffer object if an attribute cannot be found
        """

        return getattr(self._buffer, attr)

    def enterEvent(self, event):
        self.setFocus()

    def write(self, msg):
        """
        Add message to the console's output, on a new line
        :param msg: str
        """

        self.insertPlainText(msg + '\n')
        self.moveCursor(QTextCursor.End)
        self._buffer.write(unicode(msg) if helpers.is_python2() else str(msg))

    def write_error(self, msg):
        """
        Adds an error message to the console
        :param msg: str
        """

        msg_html = "<font color=\"Red\">ERROR: " + msg + "\n</font><br>"
        msg = 'ERROR: ' + msg
        self.insertHtml(msg_html)
        self.moveCursor(QTextCursor.End)
        self._buffer.write(unicode(msg) if helpers.is_python2() else str(msg))

    def write_ok(self, msg):
        """
        Adds an ok green message to the console
        :param msg: str
        """

        msg_html = "<font color=\"Lime\"> " + msg + "\n</font><br>"
        self.insertHtml(msg_html)
        self.moveCursor(QTextCursor.End)
        self._buffer.write(unicode(msg) if helpers.is_python2() else str(msg))

    def write_warning(self, msg):
        """
        Adds a warning yellow message to the console
        :param msg: str
        """

        msg_html = "<font color=\"Yellow\"> " + msg + "\n</font><br>"
        self.insertHtml(msg_html)
        self.moveCursor(QTextCursor.End)
        self._buffer.write(unicode(msg) if python.is_python2() else str(msg))

    def flush(self):
        self.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)
        self.moveCursor(QTextCursor.Up, QTextCursor.MoveAnchor)
        self.moveCursor(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
        self.moveCursor(QTextCursor.End, QTextCursor.KeepAnchor)
        self.textCursor().removeSelectedText()

    def output_buffer_to_file(self, filepath):
        pass

    def _generate_context_menu(self, pos):
        """
        Internal function that generates context menu of the console
        :param pos: QPos
        :return: QMneu
        """

        menu = self.createStandardContextMenu()
        clear_action = QAction('Clear', menu)
        clear_action.triggered.connect(self.clear)
        menu.addSeparator()
        menu.addAction(clear_action)
        # menu.addSeparator()
        # undo_action = QAction('Undo', menu)
        # undo_action.setShortcut('Ctrl+Z')
        # menu.addAction(undo_action)
        # redo_action = QAction('Redo', menu)
        # redo_action.setShortcut('Ctrl+Y')
        # menu.addAction(redo_action)
        # undo_action.setEnabled(self.isUndoRedoEnabled())
        # redo_action.setEnabled(self.isUndoRedoEnabled())
        # undo_action.triggered.connect(self._on_undo)
        # redo_action.triggered.connect(self._on_redo)
        menu.popup(self.mapToGlobal(pos))

    def _on_undo(self):
        if self.isUndoRedoEnabled():
            self.undo()

    def _on_redo(self):
        if self.isUndoRedoEnabled():
            self.redo()


class ConsoleLoggerHandler(logging.Handler):
    def __init__(self, parent):
        super(ConsoleLoggerHandler, self).__init__()

        self.widget = Console(parent=parent)
        self.widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        formatter = ConsoleFormatter('%(asctime)s|%(levelname)s|%(message)s|', '%d/%m/%Y %H:%M:%S')
        self.setFormatter(formatter)

    def emit(self, record):
        msg = self.format(record)
        if '|INFO|' in msg:
            self.widget.write_ok(msg)
        elif '|WARNING|' in msg:
            self.widget.write_warning(msg)
        elif '|ERROR|' in msg:
            self.widget.write_error(msg)
        else:
            self.widget.write(msg)


class ConsoleFormatter(logging.Formatter):

    def format(self, record):
        s = super(ConsoleFormatter, self).format(record)
        if record.exc_text:
            s = s.replace('\n', '')

        return s
