#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains code/script related widgets
"""

import re
import sys
import string

from Qt.QtCore import Qt, Signal, QRect, QSize, QRegExp, QStringListModel, QFile
from Qt.QtWidgets import QWidget, QCompleter, QTextEdit, QPlainTextEdit, QShortcut
from Qt.QtGui import QFont, QColor, QPainter, QTextCursor, QTextCharFormat, QTextOption, QTextFormat, QSyntaxHighlighter
from Qt.QtGui import QKeySequence

from tp.core import log, dcc
from tp.common.python import helpers, fileio, code, folder as folder_utils, path as path_utils
from tp.common.qt import qtutils

logger = log.tpLogger


class PythonCompleter(QCompleter, object):
    def __init__(self):
        super(PythonCompleter, self).__init__()

        self._info = None
        self._file_path = None
        self._model_strings = list()
        self._reset_list = True
        self._string_model = QStringListModel(self._model_strings, self)

        self._refresh_completer = True
        self._sub_activated = False
        self._last_imports = None
        self._last_lines = None
        self._last_path = None
        self._current_defined_imports = None
        self._last_path_and_part = None
        self._current_sub_functions = None
        self._last_column = 0

        self.setCompletionMode(self.PopupCompletion)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setModel(self._string_model)
        self.setWrapAround(False)

        self.activated.connect(self._on_insert_completion)

    def setWidget(self, widget):
        super(PythonCompleter, self).setWidget(widget)
        self.setParent(widget)

    def keyPressEvent(self):
        return

    def show_info_popup(self, info=None):
        self._info = QTextEdit()
        self._info.setEnabled(False)
        self._info.setWindowFlags(Qt.Popup)
        self._info.show()

    def get_imports(self, paths=None):
        imports = self._get_available_modules(paths=paths)
        imports.sort()

        return imports

    def get_sub_imports(self, path):
        """
        Returns namespace in a module
        :param path: str
        :return: str
        """

        defined = code.get_defined(path)
        defined.sort()

        return defined

    def clear_completer_list(self):
        self._string_model.setStringList([])

    def text_under_cursor(self):
        cursor = self.widget().textCursor()
        cursor.select(cursor.LineUnderCursor)

        return cursor.selectedText()

    def set_filepath(self, file_path):
        if not file_path:
            return

        self._file_path = file_path

    def handle_text(self, text):
        """
        Parses a single line of text
        :param text: str
        :return: bool
        """

        if not text:
            return False

        cursor = self.widget().textCursor()
        column = cursor.columnNumber() - 1
        if column < self._last_column:
            self._last_column = column
            return False
        self._last_column = column

        if column == 1:
            return False
        text = str(text)
        passed = self.handle_from_import(text, column)
        if passed:
            return True
        passed = self.handle_sub_import(text, column)
        if passed:
            return True
        passed = self.handle_import_load(text, cursor)
        if passed:
            return True

        return False

    def handle_import(self, text):
        m = re.search(r'(from|import)(?:\s+?)(\w*)', text)
        if m:
            # TODO: Find available modules in Python path
            pass

    def handle_sub_import(self, text, column):
        m = re.search(r'(from|import)(?:\s+?)(\w*.?\w*)\.(\w*)$', text)
        if m:
            if column < m.end(2):
                return False
            from_module = m.group(2)
            module_path = code.get_package_path_from_name(from_module)
            last_part = m.group(3)
            if module_path:
                defined = self.get_imports(module_path)
                self._string_model.setStringList(defined)
                self.setCompletionPrefix(last_part)
                self.popup().setCurrentIndex(self.completionModel().index(0, 0))
                return True

        return False

    def handle_import_load(self, text, cursor):
        column = cursor.columnNumber() - 1
        text = text[:cursor.columnNumber()]
        m = re.search(r'\s*([a-zA-Z0-9._]+)\.([a-zA-Z0-9_]*)$', text)
        block_number = cursor.blockNumber()
        line_number = block_number + 1
        all_text = self.widget().toPlainText()
        scope_text = all_text[:(cursor.position() - 1)]

        if m and m.group(2):
            scope_text = all_text[:(cursor.position() - len(m.group(2)) + 1)]
        if not m:
            return False

        assignment = m.group(1)
        if column < m.end(1):
            return False

        sub_m = re.search(r'(from|import)\s+(%s)' % assignment, text)
        if sub_m:
            return False

        path = None
        sub_part = None
        target = None

        text = self.widget().toPlainText()
        lines = fileio.get_text_lines(text)

        # Search for assignments
        assign_map = code.get_ast_assignment(scope_text, line_number - 1, assignment)
        if assign_map:
            if assignment in assign_map:
                target = assign_map[assignment]
            else:
                split_assignment = assignment.split('.')
                inc = 1

                while assignment not in assign_map:
                    sub_assignment = string.join(split_assignment[:(inc * -1)], '.')
                    if sub_assignment in assign_map:
                        target = assign_map[sub_assignment]
                        break
                    inc += 1
                    if inc > (len(split_assignment) - 1):
                        break
                sub_part = string.join(split_assignment[inc:], '.')

        module_name = m.group(1)
        if target and len(target) == 2:
            if target[0] == 'import':
                module_name = target[1]
            if not target[0] == 'import':
                module_name = target[0]
                sub_part = target[1]

        # import from module
        if module_name:
            imports = None
            if lines == self.last_lines:
                imports = self.last_imports
            if not imports:
                imports = code.get_line_imports(lines)

            self._last_imports = imports
            self._last_lines = lines

            if module_name in imports:
                path = imports[module_name]
            if module_name not in imports:
                split_assignment = module_name.split('.')
                last_part = split_assignment[-1]
                if last_part in imports:
                    path = imports[last_part]

            if path and not sub_part:
                test_text = ''
                defined = None
                if path == self.last_path:
                    defined = self.current_defined_imports
                if len(m.groups()) > 0:
                    test_text = m.group(2)
                if not defined:
                    defined = self.get_imports(path)
                    if defined:
                        self._current_defined_imports = defined
                    else:
                        defined = self.get_sub_imports(path)

                custom_defined = self.custom_import_load(assign_map, module_name)
                if custom_defined:
                    defined = custom_defined
                if defined:
                    if test_text and test_text[0].islower():
                        defined.sort(key=str.swapcase)
                    self._string_model.setStringList(defined)
                    self.setCompletionPrefix(test_text)
                    self.setCaseSensitivity(Qt.CaseInsensitive)
                    self.popup().setCurrentIndex(self.completionModel().index(0, 0))
                    return True

            # import from a class of a module
            if path and sub_part:

                sub_functions = None
                if self.last_path_and_part:
                    if path == self.last_path_and_part[0] and sub_part == self.last_path_and_part[1]:
                        sub_functions = self.current_sub_functions

                if not sub_functions:
                    sub_functions = code.get_ast_class_sub_functions(path, sub_part)
                    if sub_functions:
                        self._current_sub_functions = sub_functions

                self._last_path_and_part = [path, sub_part]
                if not sub_functions:
                    return False

                test_text = ''
                if len(m.groups()) > 0:
                    test_text = m.group(2)
                if test_text and test_text[0].islower():
                    sub_functions.sort(key=str.swapcase)
                self._string_model.setStringList(sub_functions)
                self.setCompletionPrefix(test_text)
                self.setCaseSensitivity(Qt.CaseInsensitive)
                self.popup().setCurrentIndex(self.completionModel().index(0, 0))
                return True

        module_name = m.group(1)
        if module_name:
            custom_defined = self.custom_import_load(assign_map, module_name)

            test_text = ''
            if len(m.groups()) > 0:
                test_text = m.group(2)

            if test_text and test_text[0].islower():
                custom_defined.sort(key=str.swapcase)
            self._string_model.setStringList(custom_defined)
            self.setCompletionPrefix(test_text)
            self.setCaseSensitivity(Qt.CaseInsensitive)
            self.popup().setCurrentIndex(self.completionModel().index(0, 0))
            return True

        return False

    def handle_from_import(self, text, column):
        m = re.search(r'(from)(?:\s+?)(\w*.?\w*)(?:\s+?)(import)(?:\s+?)(\w+)?$', text)
        if m:
            if column < m.end(3):
                return False
            from_module = m.group(2)
            module_path = code.get_package_path_from_name(from_module)

            last_part = m.group(4)
            if not last_part:
                last_part = ''
            if module_path:
                defined = self.get_imports(module_path)
                self._string_model.setStringList(defined)
                self.setCompletionPrefix(last_part)
                self.popup().setCurrentIndex(self.completionModel().index(0, 0))

                return True

        return False

    def custom_import_load(self, assign_map, moduel_name):
        return

    def _get_available_modules(self, paths=None):
        imports = list()
        if not paths:
            paths = sys.path
        if paths:
            paths = helpers.force_list(paths)

        for path in paths:
            fix_path = path_utils.normalize_path(path)
            stuff_in_folder = folder_utils.get_files_and_folders(fix_path)
            for file_or_folder in stuff_in_folder:
                folder_path = path_utils.join_path(fix_path, file_or_folder)
                files = folder_utils.get_files_with_extension('py', folder_path, full_path=False)
                if '__init__.py' in files:
                    imports.append(str(file_or_folder))

            python_files = folder_utils.get_files_with_extension('py', fix_path, full_path=False)
            for python_file in python_files:
                if python_file.startswith('__'):
                    continue
                python_file_name = python_file.split('.')[0]
                imports.append(str(python_file_name))

        if imports:
            imports = list(set(imports))

        return imports

    def _on_insert_completion(self, completion_string):
        widget = self.widget()
        cursor = widget.textCursor()
        if completion_string == self.completionPrefix():
            return
        extra = len(self.completionPrefix())
        cursor.movePosition(QTextCursor.Left, cursor.KeepAnchor, extra)
        cursor.removeSelectedText()
        cursor.insertText(completion_string)
        widget.setTextCursor(cursor)


def get_syntax_format(color=None, style=''):
    """
    Returns a QTextCharFormat with the given attributes.
    """

    _color = None

    if type(color) == str:
        _color = QColor()
        _color.setNamedColor(color)
    if type(color) == list:
        _color = QColor(*color)

    if color == 'green':
        _color = Qt.green

    _format = QTextCharFormat()

    if _color:
        _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


def syntax_styles(name):
    if name == 'keyword':
        if dcc.is_maya():
            return get_syntax_format('green', 'bold')
        if not dcc.is_maya():
            return get_syntax_format([0, 150, 150], 'bold')
    if name == 'operator':
        if dcc.is_maya():
            return get_syntax_format('gray')
        if not dcc.is_maya():
            return get_syntax_format('darkGray')
    if name == 'brace':
        if dcc.is_maya():
            return get_syntax_format('lightGray')
        if not dcc.is_maya():
            return get_syntax_format('darkGray')
    if name == 'defclass':
        if dcc.is_maya():
            return get_syntax_format(None, 'bold')
        if not dcc.is_maya():
            return get_syntax_format(None, 'bold')
    if name == 'string':
        if dcc.is_maya():
            return get_syntax_format([230, 230, 0])
        if not dcc.is_maya():
            return get_syntax_format('blue')
    if name == 'string2':
        if dcc.is_maya():
            return get_syntax_format([230, 230, 0])
        if not dcc.is_maya():
            return get_syntax_format('lightGreen')
    if name == 'comment':
        if dcc.is_maya():
            return get_syntax_format('red')
        if not dcc.is_maya():
            return get_syntax_format('red')
    if name == 'self':
        if dcc.is_maya():
            return get_syntax_format(None, 'italic')
        if not dcc.is_maya():
            return get_syntax_format('black', 'italic')
    if name == 'bold':
        return get_syntax_format(None, 'bold')
    if name == 'numbers':
        if dcc.is_maya():
            return get_syntax_format('cyan')
        if not dcc.is_maya():
            return get_syntax_format('brown')


class PythonHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for the Python language.
    """

    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False', 'process', 'show'
    ]

    if dcc.is_maya():
        keywords += ['cmds', 'pm', 'mc', 'pymel']

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        r'\+', '-', r'\*', '/', '//', r'\%', r'\*\*',
        # In-place
        r'\+=', '-=', r'\*=', '/=', r'\%=',
        # Bitwise
        r'\^', r'\|', r'\&', r'\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        r'\{', r'\}', r'\(', r'\)', r'\[', r'\]',
    ]

    def __init__(self, document):
        super(PythonHighlighter, self).__init__(document)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, syntax_styles('string2'))
        self.tri_double = (QRegExp('"""'), 2, syntax_styles('string2'))

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, syntax_styles('keyword'))
                  for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, syntax_styles('operator'))
                  for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, syntax_styles('brace'))
                  for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, syntax_styles('self')),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, syntax_styles('string')),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, syntax_styles('string')),

            # 'def' followed by an identifier
            # (r'\bdef\b\s*(\w+)', 0, syntax_styles('defclass')),
            # 'class' followed by an identifier
            # (r'\bclass\b\s*(\w+)', 0, syntax_styles('defclass')),

            # From '#' until a newline
            (r'#[^\n]*', 0, syntax_styles('comment')),
            # ('\\b\.[a-zA-Z_]+\\b(?=\()', 0, syntax_styles('bold')),
            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, syntax_styles('numbers')),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, syntax_styles('numbers')),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, syntax_styles('numbers')),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """
        Apply syntax highlighting to the given block of text.
        """

        # Do other syntax formatting
        for expression, nth, format_value in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format_value)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """
        Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """

        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False


class CodeLineNumber(QWidget, object):
    def __init__(self, code_editor):
        super(CodeLineNumber, self).__init__()

        self.setParent(code_editor)
        self._code_editor = code_editor

    def sizeHint(self):
        return QSize(self._code_editor._line_number_width(), 0)

    def paintEvent(self, event):
        self._code_editor._line_number_paint(event)


class CodeCompleter(PythonCompleter, object):
    def __init__(self):
        super(CodeCompleter, self).__init__()

    def keyPressEvent(self):
        return

    def _on_insert_completion(self, completion_string):
        super(CodeCompleter, self)._on_insert_completion(completion_string)

        # This stops Maya from entering edit mode in the outliner, if something is selected
        if dcc.is_maya():
            dcc.focus('modelPanel1')

    def _format_live_function(self, function_instance):
        function_name = None
        if hasattr(function_instance, 'im_func'):
            args = function_instance.im_func.func_code.co_varnames
            count = function_instance.im_func.func_code.co_argcount
            args_name = ''
            if args:
                args = args[:count]
                if args[0] == 'self':
                    args = args[1:]
                args_name = string.join(args, ',')
            function_name = '{}({})'.format(function_instance.im_func.func.name, args_name)

        return function_name

    def custom_import_load(self, assign_map, module_name):

        found = list()

        if module_name == 'cmds':
            if assign_map:
                if module_name in assign_map:
                    return []
            if dcc.is_maya():
                import maya.cmds as cmds
                functions = dir(cmds)
                return functions

        return found


class CodeTextEdit(QPlainTextEdit, object):

    save = Signal(object)
    saveDone = Signal(object)
    fileSet = Signal()
    findOpened = Signal(object)
    codeTextSizeChanged = Signal(object)
    mousePressed = Signal(object)

    def __init__(self, settings=None, parent=None):

        self._settings = settings
        self._text_edit_globals = dict()
        self._file_path = None
        self._last_modified = None
        self._find_widget = None
        self._completer = None
        self._skip_focus = False

        self._option_object = None

        super(CodeTextEdit, self).__init__(parent=parent)

        self.setFont(QFont('Courier', 9))
        self.setWordWrapMode(QTextOption.NoWrap)

        save_shortcut = QShortcut(QKeySequence(self.tr('Ctlr+s')), self)
        find_shortcut = QShortcut(QKeySequence(self.tr('Ctrl+f')), self)
        goto_line_shortcut = QShortcut(QKeySequence(self.tr('Ctrl+g')), self)
        duplicate_line_shortcut = QShortcut(QKeySequence(self.tr('Ctrl+d')), self)
        zoom_in_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Plus), self)
        zoom_in_other_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Equal), self)
        zoom_out_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Minus), self)

        save_shortcut.activated.connect(self._on_save)
        find_shortcut.activated.connect(self._on_find)
        goto_line_shortcut.activated.connect(self._on_goto_line)
        duplicate_line_shortcut.activated.connect(self._on_duplicate_line)
        zoom_in_shortcut.activated.connect(self._zoom_in_text)
        zoom_in_other_shortcut.activated.connect(self._zoom_in_text)
        zoom_out_shortcut.activated.connect(self._zoom_out_text)

        self._line_numbers = CodeLineNumber(self)

        self._setup_highlighter()
        self._update_number_width(0)
        self._line_number_highlight()

        self.blockCountChanged.connect(self._on_update_number_width)
        self.updateRequest.connect(self._on_update_number_area)
        self.cursorPositionChanged.connect(self._on_cursor_position_changed)
        self.codeTextSizeChanged.connect(self._on_code_text_size_changed)

    def resizeEvent(self, event):
        super(CodeTextEdit, self).resizeEvent(event)
        rect = self.contentsRect()
        new_rect = QRect(rect.left(), rect.top(), self._line_number_width(), rect.height())
        self._line_numbers.setGeometry(new_rect)

    def mousePressEvent(self, event):
        self.mousePressed.emit(event)
        return super(CodeTextEdit, self).mousePressEvent(event)

    def keyPressEvent(self, event):

        pass_on = True
        quit_right_away = False

        if event.key() in (Qt.Key_Right, Qt.Key_Left, Qt.Key_Up, Qt.Key_Down):
            quit_right_away = True
        if quit_right_away:
            super(CodeTextEdit, self).keyPressEvent(event)
            return

        if self._completer:
            self._completer.activated.connect(self._on_activate)

            if self._completer.popup().isVisible():
                if event.key() == Qt.Key_Enter:
                    event.ignore()
                    return
                elif event.key() == Qt.Key_Return:
                    event.ignore()
                    return
                elif event.key() == Qt.Key_Escape:
                    event.ignore()
                    return
                elif event.key() == Qt.Key_Tab:
                    event.ignore()
                    return
                elif event.key() == Qt.Key_Backtab:
                    event.ignore()
                    return
            else:
                if event.key() == Qt.Key_Control or event.key() == Qt.Key_Shift:
                    event.ignore()
                    self._completer.popup().hide()
                    return
            if event.key() == Qt.Key_Control:
                event.ignore()
                self._completer.popup().hide()
                return

        if event.modifiers() and Qt.ControlModifier:
            if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
                self._run()
                return
        if event.key() == Qt.Key_Backtab or event.key() == Qt.Key_Tab:
            self._handle_tab(event)
            pass_on = False
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self._handle_enter(event)
            pass_on = False

        if pass_on:
            super(CodeTextEdit, self).keyPressEvent(event)

        if self._completer:
            text = self._completer.text_under_cursor()
            if text:
                result = self._completer.handle_text(text)
                if result:
                    rect = self.cursorRect()
                    scroll_width = self._completer.popup().verticalScrollBar().sizeHint().width()
                    width = self._completer.popup().sizeHintForColumn(0) + scroll_width
                    if width > 350:
                        width = 350
                    rect.setWidth(width)
                    self._completer.complete(rect)
                if not result:
                    self._completer.popup().hide()
                    self._completer.clear_completer_list()
                    self._completer.refresh_completer = True

    def wheelEvent(self, event):
        delta = event.delta()
        keys = event.modifiers()
        if keys == Qt.CTRL:
            if delta > 0:
                self._zoom_in_text()
            elif delta < 0:
                self._zoom_out_text()

        return super(CodeTextEdit, self).wheelEvent(event)

    def focusInEvent(self, event):
        if self._completer:
            self._completer.setWidget(self)
        super(CodeTextEdit, self).focusInEvent(event)
        if not self._skip_focus:
            self._update_request()

    def get_settings(self):
        return self._settings

    def set_settigns(self, settings):
        self._settings = settings

    def set_option_object(self, option_object):
        self._option_object = option_object

    def set_completer(self, completer):
        self._completer = completer()
        self._completer.setWidget(self)
        self._completer.set_filepath(self._file_path)

    def set_file(self, file_path):
        in_file = QFile(file_path)
        if in_file.open(QFile.ReadOnly | QFile.Text):
            text = in_file.readAll()
            self.setPlainText(text)
        self._file_path = file_path
        self._last_modified = fileio.get_last_modified_date(self._file_path)
        if self._completer:
            self._completer.set_filepath(file_path)
        self.fileSet.emit()

    def set_find_widget(self, widget):
        self._find_widget.set_widget(widget)

    def load_modification_date(self):
        self._last_modified = fileio.get_last_modified_date(self._file_path)

    def is_modified(self):
        return self.document().isModified()

    def _handle_enter(self, event):
        cursor = self.textCursor()
        current_block = cursor.block()
        cursor_position = cursor.positionInBlock()
        current_block_text = str(current_block.text())

        current_found = ''
        if not current_found:
            current_found = re.search('^ +', current_block_text)
            if current_found:
                current_found = current_found.group(0)

        indent = 0
        if current_found:
            indent = len(current_found)

        colon_position = current_block_text.find(':')
        comment_position = current_block_text.find('#')
        if colon_position > -1:
            sub_indent = 4
            if -1 < comment_position < colon_position:
                sub_indent = 0
            indent += sub_indent
        if cursor_position < indent:
            indent = (cursor_position - indent) + indent

        cursor.insertText(('\n' + ' ' * indent))

    def _handle_tab(self, event):
        cursor = self.textCursor()
        document = self.document()

        start_position = cursor.anchor()
        select_position = cursor.selectionStart()
        select_start_block = document.findBlock(select_position)
        start = select_position - select_start_block.position()
        end_position = cursor.position()
        if start_position > end_position:
            temp_position = end_position
            end_position = start_position
            start_position = temp_position

        if event.key() == Qt.Key_Tab:
            if not cursor.hasSelection():
                self.insertPlainText('    ')
                start_position += 4
                end_position = start_position
            else:
                cursor.setPosition(start_position)
                cursor.movePosition(QTextCursor.StartOfLine)
                cursor.setPosition(end_position, QTextCursor.KeepAnchor)
                text = cursor.selection().toPlainText()
                split_text = text.split('\n')
                edited = list()
                index = 0
                for text_split in split_text:
                    edited.append(self._add_tab(text_split))
                    if index == 0:
                        start_position += 4
                    end_position += 4
                    index += 1

                edited_text = string.join(edited, '\n')
                cursor.insertText(edited_text)
                self.setTextCursor(cursor)

        elif event.key() == Qt.Key_Backtab:
            if not cursor.hasSelection():
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.StartOfLine)
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 4)
                text = str(cursor.selection().toPlainText())
                if text and text == '    ':
                    cursor.insertText('')
                    self.setTextCursor(cursor)
                    start_position -= 4
                    end_position = start_position
            else:
                cursor.setPosition(start_position)
                cursor.movePosition(QTextCursor.StartOfLine)
                cursor.setPosition(end_position, QTextCursor.KeepAnchor)
                cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                self.setTextCursor(cursor)
                text = str(cursor.selection().toPlainText())
                split_text = text.split('\n')
                edited = list()
                index = 0
                skip_indent = False
                for text_split in split_text:
                    new_string_value = text_split
                    if not skip_indent:
                        new_string_value = self._remove_tab(text_split)
                    if index == 0 and new_string_value == text_split:
                        skip_indent = True
                    if not skip_indent:
                        if new_string_value != text_split:
                            if index == 0:
                                offset = (start - 4) + 4
                                if offset > 4:
                                    offset = 4
                                start_position -= offset
                            end_position -= 4
                    edited.append(new_string_value)
                    index += 1

                edited_text = string.join(edited, '\n')
                cursor.insertText(edited_text)
                self.setTextCursor(cursor)

        cursor = self.textCursor()
        cursor.setPosition(start_position)
        cursor.setPosition(end_position, QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)

    def _add_tab(self, string_value):
        return '    {}'.format(string_value)

    def _remove_tab(self, string_value):
        string_section = string_value[0:4]
        if string_section == '    ':
            return string_value[4:]

        return string_value

    def _set_text_size(self, value):
        font = self.font()
        font.setPixelSize(value)
        self.setFont(font)

    def _code_text_size_change(self, value):
        self._set_text_size(value)

    def _setup_highlighter(self):
        self._higlighter = PythonHighlighter(document=self.document())

    def _line_number_paint(self, event):
        paint = QPainter(self._line_numbers)
        if not dcc.is_maya():
            paint.fillRect(event.rect(), Qt.lightGray)
        else:
            paint.fillRect(event.rect(), Qt.black)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = int(top + self.blockBoundingGeometry(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = block_number + 1
                if dcc.is_maya():
                    paint.setPen(Qt.lightGray)
                else:
                    paint.setPen(Qt.black)
                paint.drawText(
                    0, top, self._line_numbers.width(), self.fontMetrics().height(), Qt.AlignRight, str(number))
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def _line_number_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 1 + self.fontMetrics().width('1') * digits

        return space

    def _line_number_highlight(self):
        extra_selection = QTextEdit.ExtraSelection()
        selections = [extra_selection]
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            if dcc.is_maya():
                line_color = QColor(Qt.black)
            else:
                line_color = QColor(Qt.lightGray)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)

        self.setExtraSelections(selections)

    def _update_number_width(self, value=0):
        self.setViewportMargins(self._line_number_width(), 0, 0, 0)

    def _update_number_area(self, rect, y_value):
        if y_value:
            self._line_numbers.scroll(0, y_value)
        else:
            self._line_numbers.update(0, rect.y(), self._line_number_width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_number_width()

    def _has_changed(self):
        if self._file_path:
            if path_utils.is_file(self._file_path):
                last_modified = fileio.get_last_modified_date(self._file_path)
                if last_modified != self._last_modified:
                    return True

        return False

    def _update_request(self):
        if not self._has_changed():
            return

        last_modified = fileio.get_last_modified_date(self._file_path)
        self._skip_focus = True
        permission = qtutils.get_permission(
            'File:\n{}\nhas changed, do you want to relaod it?'.format(path_utils.get_basename(self._file_path)), self)
        if permission:
            self.set_file(self._file_path)
        else:
            self._last_modified = last_modified

        self._skip_focus = False

    def _zoom_in_text(self):
        font = self.font()
        size = font.pointSize()
        size += 1
        font.setPointSize(size)
        self.setFont(QFont('Courier', size))

    def _zoom_out_text(self):
        font = self.font()
        size = font.pointSize()
        size -= 1
        font.setPointSize(size)
        self.setFont(QFont('Courier', size))

    def _run(self):
        raise NotImplementedError('run functionality is not implemented!')

    def _on_save(self):
        if not self.document().isModified():
            logger.warning('No changes to save in {}'.format(self._file_path))
            return

        old_last_modified = self._last_modified
        try:
            self.save.emit(self)
        except Exception:
            pass

        new_last_modified = fileio.get_last_modified_date(self._file_path)
        if old_last_modified == new_last_modified:
            self.saveDone.emit(False)

        if old_last_modified != new_last_modified:
            self.saveDone.emit(True)
            self.document().setModified(False)
            self._last_modified = new_last_modified

    def _on_find(self):
        self.findOpened.emit(self)

    def _on_goto_line(self):
        line = qtutils.get_comment(parent=self, text_message='', title='Goto Line')
        if not line:
            return

        line_number = int(line)
        text_cursor = self.textCursor()
        block_number = text_cursor.blockNumber()

        number = line_number - block_number
        if number > 0:
            move_type = text_cursor.NextBlock
            number -= 2
        if number < 0:
            move_type = text_cursor.PreviousBlock
            number = abs(number)

        text_cursor.movePosition(move_type, text_cursor.MoveAnchor, (number + 1))
        self.setTextCursor(text_cursor)

    def _on_duplicate_line(self):
        text_cursor = self.textCursor()

        selected_text = text_cursor.selectedText()
        if not selected_text:
            text_cursor.beginEditBlock()
            text_cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
            text_cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            selected_text = text_cursor.selectedText()
            text_cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.MoveAnchor)
            text_cursor.insertBlock()
            text_cursor.insertText(selected_text)
            text_cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.MoveAnchor)
            self.setTextCursor(text_cursor)
            text_cursor.endEditBlock()
        else:
            text_cursor.beginEditBlock()
            text_cursor.setPosition(text_cursor.selectionEnd(), QTextCursor.MoveAnchor)
            self.setTextCursor(text_cursor)
            text_cursor.insertBlock()
            position = text_cursor.position()
            text_cursor.insertText(selected_text)
            end_position = text_cursor.position()
            text_cursor.setPosition(position, QTextCursor.MoveAnchor)
            text_cursor.setPosition(end_position, QTextCursor.KeepAnchor)
            self.setTextCursor(text_cursor)
            text_cursor.endEditBlock()

    def _on_update_number_width(self, value=0):
        self.setViewportMargins(self._line_number_width(), 0, 0, 0)

    def _on_update_number_area(self, rect, y_value):
        if y_value:
            self._line_numbers.scroll(0, y_value)
        else:
            self._line_numbers.update(0, rect.y(), self._line_number_width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._update_number_width()

    def _on_cursor_position_changed(self):
        self._line_number_highlight()

    def _on_code_text_size_changed(self, value):
        self._set_text_size(value)

    def _on_activate(self):
        pass
