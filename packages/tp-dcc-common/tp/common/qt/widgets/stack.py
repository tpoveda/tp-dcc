from Qt.QtCore import QPoint, QPropertyAnimation, QEasingCurve
from Qt.QtWidgets import QFrame, QStackedWidget, QGraphicsOpacityEffect


def sliding_opacity_stacked_widget(parent=None):
	"""
	Creates a new QStackWidget that uses opacity animation to switch between stack widgets.

	:param QWidget parent: parent widget.
	:return: stack widget.
	:rtype: SlidingOpacityStackedWidget
	"""

	new_stack_widget = SlidingOpacityStackedWidget(parent=parent)
	return new_stack_widget


class SlidingOpacityStackedWidget(QStackedWidget):
	"""
	Custom stack widget that activates opacity animation when current stack index changes
	"""

	def __init__(self, parent=None):
		super(SlidingOpacityStackedWidget, self).__init__(parent)

		self._prev_index = 0
		self._to_show_pos_anim = QPropertyAnimation()
		self._to_show_pos_anim.setDuration(400)
		self._to_show_pos_anim.setPropertyName(b'pos')
		self._to_show_pos_anim.setEndValue(QPoint(0, 0))
		self._to_show_pos_anim.setEasingCurve(QEasingCurve.OutCubic)
		self._to_hide_pos_anim = QPropertyAnimation()
		self._to_hide_pos_anim.setDuration(400)
		self._to_hide_pos_anim.setPropertyName(b'pos')
		self._to_hide_pos_anim.setEndValue(QPoint(0, 0))
		self._to_hide_pos_anim.setEasingCurve(QEasingCurve.OutCubic)
		self._opacity_effect = QGraphicsOpacityEffect()
		self._opacity_anim = QPropertyAnimation()
		self._opacity_anim.setDuration(400)
		self._opacity_anim.setEasingCurve(QEasingCurve.InCubic)
		self._opacity_anim.setPropertyName(b'opacity')
		self._opacity_anim.setStartValue(0.0)
		self._opacity_anim.setEndValue(1.0)
		self._opacity_anim.setTargetObject(self._opacity_effect)
		self._opacity_anim.finished.connect(self._on_disable_opacity)

		self.currentChanged.connect(self._on_play_anim)

	def _on_play_anim(self, index):
		"""
		Internal callback function that is called when an animated is played.

		:param int index: new stack index.
		"""

		current_widget = self.widget(index)
		if self._prev_index < index:
			self._to_show_pos_anim.setStartValue(QPoint(self.width(), 0))
			self._to_show_pos_anim.setTargetObject(current_widget)
			self._to_show_pos_anim.start()
		else:
			self._to_hide_pos_anim.setStartValue(QPoint(-self.width(), 0))
			self._to_hide_pos_anim.setTargetObject(current_widget)
			self._to_hide_pos_anim.start()
		current_widget.setGraphicsEffect(self._opacity_effect)
		current_widget.graphicsEffect().setEnabled(True)
		self._opacity_anim.start()
		self._prev_index = index

	def _on_disable_opacity(self):
		"""
		Internal callbakc function that is called when opacity animation finishes
		"""

		self.currentWidget().graphicsEffect().setEnabled(False)


class StackItem(QFrame):
	def __init__(self, title, parent, start_hidden=False):
		super().__init__(parent)

		if start_hidden:
			self.hide()

		self._stack_widget = parent
