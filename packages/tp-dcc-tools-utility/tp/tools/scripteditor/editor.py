from __future__ import annotations

from typing import Tuple

from tp.common.qt import api as qt

from tp.tools.scripteditor import highlighters
from tp.tools.scripteditor.widgets import texteditor


def python_editor(
		title: str = 'Python Editor',
		parent: qt.QWidget | None = None) -> Tuple[highlighters.PythonHighlighter, CodeEditor]:

	editor = CodeEditor(parent)
	editor.setWindowTitle(title)
	highlighter = highlighters.PythonHighlighter(editor.document())

	return highlighter, editor


def json_editor(
		title: str = 'JSON Editor',
		parent: qt.QWidget | None = None) -> Tuple[highlighters.JsonHighlighter, CodeEditor]:

	editor = CodeEditor(parent)
	editor.setWindowTitle(title)
	highlighter = highlighters.JsonHighlighter(editor.document())

	return highlighter, editor


class CodeEditor(texteditor.CodeTextEditor):

	BACKGROUND_COLOR = qt.QColor(21, 21, 21)
	LINE_NUMBER_COLOR = qt.QColor(200, 200, 200)

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent)

		self._tab_size = 4

		self._font = qt.QFont()
		self._font.setFamily('Consolas')
		self._font.setStyleHint(qt.QFont.Monospace)
		self._font.setPointSize(10)
		self.setFont(self._font)

		self._line_number_area = texteditor.LineNumberArea(self)

		self.setLineWrapMode(qt.QPlainTextEdit.NoWrap)
		self.setTabStopWidth(self._tab_size * self.fontMetrics().width(' '))

		self.blockCountChanged.connect(self._on_block_count_changed)
		self.updateRequest.connect(self._on_update_request)

	def _on_block_count_changed(self, _):
		"""
		Internal callback function that is called each time block count changes.
		Forces the update of the line number area width.
		"""

		self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

	def _on_update_request(self, rect: qt.QRect, dy: int):
		"""
		Internal callback function that is called each time code text editor update is requested.

		:param qt.QRect rect: code text editor rect.
		:param dy:
		"""

		if dy:
			self._line_number_area.scroll(0, dy)
		else:
			width = self._line_number_area.width()
			self._line_number_area.update(0, rect.y(), width, rect.height())

		if rect.contains(self.viewport().rect()):
			self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

	def resizeEvent(self, e: qt.QResizeEvent) -> None:
		super().resizeEvent(e)

		contents_rect = self.contentsRect()
		width = self.line_number_area_width()
		rect = qt.QRect(contents_rect.left(), contents_rect.top(), width, contents_rect.height())
		self._line_number_area.setGeometry(rect)

	def line_number_area_width(self) -> int:
		"""
		Returns the width that the line number area widget should ocuppy.

		:return: line number area width.
		:rtype: int
		"""

		digits = 1
		max_num = max(1, self.blockCount())
		while max_num >= 10:
			max_num *= 0.1
			digits += 1
		space = 20 + self.fontMetrics().width('9') * digits

		return space

	def paint_line_number_area_event(self, event: qt.QPaintEvent):
		"""
		Handles the painting of the line number area in its proper place.

		:param qt.QPaintEvent event: Qt paint event.
		"""

		painter = qt.QPainter(self._line_number_area)
		painter.fillRect(event.rect(), self.BACKGROUND_COLOR)
		block = self.firstVisibleBlock()
		block_number = block.blockNumber()
		offset = self.contentOffset()
		top = self.blockBoundingGeometry(block).translated(offset).top()
		bottom = top + self.blockBoundingRect(block).height()

		while block.isValid() and top <= event.rect().bottom():
			if block.isVisible() and bottom >= event.rect().top():
				number = str(block_number + 1)
				painter.setPen(self.LINE_NUMBER_COLOR)
				width = self._line_number_area.width() - 10
				height = self.fontMetrics().height()
				painter.drawText(0, int(top), int(width), int(height), qt.Qt.AlignRight, number)
			block = block.next()
			top = bottom
			bottom = top + self.blockBoundingRect(block).height()
			block_number += 1
