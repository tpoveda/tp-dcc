from __future__ import annotations

from Qt.QtWidgets import QWidget

from tp.core.abstract import window
from tp.common.python import decorators


class StandaloneWindow(window.AbstractWindow):
	"""
	Window intended to be used in standalone Python applications.
	"""

	def __init__(self, parent: QWidget | None = None):
		super().__init__(parent)

		self._standalone = True

