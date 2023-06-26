from __future__ import annotations

import typing
from typing import Tuple, List

from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
	from tp.tools.scripteditor.editor import CodeEditor


class LineNumberArea(qt.QWidget):
	"""
	Widget that represents line number within a code editor.
	"""

	def __init__(self, editor: CodeEditor):
		super().__init__(editor)

		self._code_editor = editor

	def sizeHint(self) -> qt.QSize:
		return qt.QSize(self._code_editor.line_number_area_width(), 0)

	def paintEvent(self, event: qt.QPaintEvent) -> None:
		self._code_editor.paint_line_number_area_event(event)


class CodeTextEditor(qt.QPlainTextEdit):

	_IS_FIRST = False
	_PRESSED_KEYS = []

	indented = qt.Signal(list)
	unindented = qt.Signal(list)
	commented = qt.Signal(list)
	uncommented = qt.Signal(list)

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent)

		self.indented.connect(self._on_indented)
		self.unindented.connect(self._on_unindented)
		self.commented.connect(self._on_commented)
		self.uncommented.connect(self._on_uncommented)

	def keyPressEvent(self, e: qt.QKeyEvent) -> None:
		self._IS_FIRST = True
		self._PRESSED_KEYS.append(e.key())
		start_line, end_line = self.selection_range()

		if e.key() == qt.Qt.Key_Tab and (end_line - start_line):
			lines = range(start_line, end_line + 1)
			self.indented.emit(lines)
			return
		elif e.key() == qt.Qt.Key_Backtab:
			lines = range(start_line, end_line + 1)
			self.unindented.emit(lines)
			return

		super().keyPressEvent(e)

	def keyReleaseEvent(self, e: qt.QKeyEvent) -> None:
		if self._IS_FIRST:
			self._process_multi_keys(self._PRESSED_KEYS)

		self._IS_FIRST = False
		self._PRESSED_KEYS.pop()

		super().keyReleaseEvent(e)

	def selection_range(self) -> Tuple[int, int]:
		"""
		Returns the text selection line range from cursor.

		:return: start line number and end line number.
		:rtype: Tuple[int, int]
		..note:: currently only continuous selection is supported.
		"""

		cursor = self.textCursor()
		if not cursor.hasSelection():
			return 0, 0

		start_pos = cursor.selectionStart()
		end_pos = cursor.selectionEnd()
		cursor.setPosition(start_pos)
		start_line = cursor.blockNumber()
		cursor.setPosition(end_pos)
		end_line = cursor.blockNumber()

		return start_line, end_line

	def clear_selection(self):
		"""
		Clears out text selection on cursor.
		"""

		pos = self.textCursor().selectionEnd()
		self.textCursor().movePosition(pos)

	def _insert_line_start(self, string: str, line_number: int):
		"""
		Inserts given string in the specific line number at the start of the line.

		:param str string: string to insert at the start of the line.
		:param int line_number: number of the line we want to insert text into.
		"""

		cursor = qt.QTextCursor(self.document().findBlockByLineNumber(line_number))
		self.setTextCursor(cursor)
		self.textCursor().insertText(string)

	def _remove_line_start(self, string: str, line_number: int):
		"""
		Removes given string in the specific line number from the start of the line.

		:param str string: string to insert at the start of the line.
		:param int line_number: number of the line we want to remove text from.
		"""

		cursor = qt.QTextCursor(self.document().findBlockByLineNumber(line_number))
		cursor.select(qt.QTextCursor.LineUnderCursor)
		text = cursor.selectedText()
		if text.startswith(string):
			cursor.removeSelectedText()
			cursor.insertText(text.split(string, 1)[-1])

	def _process_multi_keys(self, keys: List[int]):
		"""
		Internal function that handles the processing of multiple key combo events.

		:param List[int] keys: list of pressed keys.
		"""

		# TODO: Implement toggle comments indent event
		if keys == [qt.Qt.Key_Control, qt.Qt.Key_Slash]:
			pass

	def _on_indented(self, lines: List[int]):
		"""
		Internal callback function that is called each time the lines are indented.
		Handles the insertion of tab escape character in the indented lines.

		:param List[int] lines: indented line numbers.
		"""

		for line in lines:
			self._insert_line_start('\t', line)

	def _on_unindented(self, lines: List[int]):
		"""
		Internal callback function that is called each time the lines are unindented.
		Handles the removal of tab escape characters from the start of the lines.

		:param List[int] lines: unindented line numbers.
		"""

		for line in lines:
			self._remove_line_start('\t', line)

	def _on_commented(self, lines: List[int]):
		"""
		Internal callback function that is called each time the lines are commented.
		Handles the commenting of the lines.

		:param List[int] lines: commented line numbers.
		"""

		for line in lines:
			pass

	def _on_uncommented(self, lines: List[int]):
		"""
		Internal callback function that is called each time the lines are uncommented.
		Handles the uncommenting of the lines.

		:param List[int] lines: uncommented line numbers.
		"""

		for line in lines:
			pass
