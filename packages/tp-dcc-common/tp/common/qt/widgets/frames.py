from Qt.QtCore import Signal
from Qt.QtWidgets import QFrame
from Qt.QtGui import QMouseEvent


class BaseFrame(QFrame):
	"""
	Extended QFrame that expnads following functionality:
		- Exposes a mouseReleased signal that is called when mouse is released
	"""

	mouseReleased = Signal(object)

	def mouseReleaseEvent(self, event: QMouseEvent) -> None:
		self.mouseReleased.emit()
		return super().mouseReleaseEvent(event)
