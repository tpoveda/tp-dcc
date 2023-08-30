from __future__ import annotations

from tp.common.qt import api as qt


class NoddleView(qt.FramelessWindow):
	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)
