from __future__ import annotations

from Qt.QtCore import Qt, Signal, Property, QTimer, QPropertyAnimation, QEasingCurve
from Qt.QtWidgets import QApplication, QWidget
from Qt.QtGui import QKeyEvent, QFocusEvent

from tp.common.qt.widgets import layouts


class SlidingWidget(QWidget):
	"""
	Widget that accepts two widgets. The primary widget slides open on mouse focus, slides closed when the mouse moves
	out of the widget and loses focus.

	.. code-block:: python:
		sliding_widget = SlidingWidget(parent=self)
		sliding_widget.set_widgets(self._search_edit, self._title_label)
	"""

	focusCleared = Signal()

	def __init__(self, duration: int = 80, parent: QWidget | None = None):
		super().__init__(parent)

		self._duration = duration
		self._primary_widget = None					# type: QWidget
		self._secondary_widget = None				# type: QWidget
		self._anim = None							# type: QPropertyAnimation
		self._original_key_press_event = None		# type: QKeyEvent
		self._original_focus_out_event = None		# type: QFocusEvent
		self._original_focus_in_event = None		# type: QFocusEvent
		self._timeout = 3000
		self._timeout_active = True
		self._sliding_active = True
		self._slide_direction = Qt.RightToLeft
		self._slide_stretch = 0
		self._primary_index = 1
		self._secondary_index = 0
		self._opened = False

		self._main_layout = layouts.horizontal_layout(margins=(0, 0, 0, 0), parent=self)
		self.setLayout(self._main_layout)

		self._close_timer = QTimer(parent=self)
		self._close_timer.setSingleShot(True)
		self._close_timer.timeout.connect(self._on_close_timer_timeout)

	def set_widgets(self, primary: QWidget, secondary: QWidget):
		"""
		Sets the primary and secondary widgets.

		:param QWidget primary: widget that will be expanded when clicked.
		:param QWidget secondary: widget that will be hidden when primary widget is focused.
		"""

		while self._main_layout.count():
			self._main_layout.takeAt(0)

		self._set_secondary_widget(secondary)
		self._set_primary_widget(primary)

	def set_sliding_active(self, flag: bool):
		"""
		Sets whether sliding is active.

		:param bool flag: True to enable sliding; False otherwise.
		"""

		update = bool(self._sliding_active)
		self._sliding_active = flag
		if update:
			self.animate(expand=True)

	def set_timeout_active(self, flag: bool):
		"""
		Sets whether timeout is active.

		:param bool flag: True to enable timeout; False to disable it.
		"""

		self._timeout_active = flag

	def set_slide_direction(self, direction: Qt.LayoutDirection):
		"""
		Sets the slide direction.

		:param Qt.LayoutDirection direction: direction
		"""

		self._primary_index = 1 if direction == Qt.RightToLeft else 0
		self._secondary_index = 0 if direction == Qt.RightToLeft else 1

	def set_duration(self, duration: float):
		"""
		Sets the animation duration.

		:param bool duration: animation duration in milliseconds.
		"""

		self._duration = duration

	def animate(self, expand: bool = True):
		"""
		Animates the sliding of the widget.

		:param bool expand: True to expand the sliding widget; False to collapse it.
		"""

		self._anim = QPropertyAnimation(self, b'slide_stretch')
		self._anim.setDuration(self._duration)
		self._anim.setEasingCurve(QEasingCurve.InOutSine)
		if expand:
			self._anim.setStartValue(1)
			self._anim.setEndValue(99)
			self._anim.start()
			self._opened = True
		else:
			self._anim.setStartValue(self._main_layout.stretch(1))
			self._anim.setEndValue(self._primary_index)
			self._anim.start()
			self._opened = False

	def _get_slide_stretch(self) -> int:
		"""
		Internal function that returns the current slide stretch.

		:return: slide stretch value.
		:rtype: int
		"""

		return self._slide_stretch

	def _set_slide_stretch(self, value: int):
		"""
		Internal function that sets the stretch for the main layout widgets.

		:param int value: stretch value.
		"""

		self._slide_stretch = value
		self._main_layout.setStretch(self._secondary_index, 100 - value)
		self._main_layout.setStretch(self._primary_index, value)

	slide_stretch = Property(int, _get_slide_stretch, _set_slide_stretch)		# Property to be animated

	def _update_initial_stretch(self):
		"""
		Internal function that updates the initial stretch.
		"""

		if not self._sliding_active:
			return
		if self._primary_widget is not None and self._secondary_widget is not None:
			QApplication.processEvents()
			self._main_layout.setStretch(self._secondary_index, 100)
			self._main_layout.setStretch(self._primary_index, 1)

	def _set_primary_widget(self, widget: QWidget):
		"""
		Internal function that sets the primary widget, which is the one that will be expanded when clicked.

		:param QWidget widget: widget to set as primary sliding widget.
		"""

		self._primary_widget = widget

		self._main_layout.addWidget(widget)
		self._update_initial_stretch()

		self._original_key_press_event = widget.keyPressEvent
		self._original_focus_in_event = widget.focusInEvent
		self._original_focus_out_event = widget.focusOutEvent
		widget.keyPressEvent = self._widget_key_press_event
		widget.focusInEvent = self._widget_focus_in_event
		widget.focusOutEvent = self._widget_focus_out_event

	def _set_secondary_widget(self, widget: QWidget):
		"""
		Internal function that sets the secondary widget, which is the one that will be shown most of the time but will
		be hidden when the primary is clicked.

		:param QWidget widget: widget to set as secondary sliding widget.
		"""

		self._secondary_widget = widget

		self._main_layout.addWidget(widget)
		self._secondary_widget.setMinimumWidth(1)
		self._update_initial_stretch()

	def _widget_key_press_event(self, event: QKeyEvent):
		"""
		Internal function used to override the keyPressEvent function of the primary widget.

		:param QKeyEvent event: key event.
		"""

		self._close_timer.start(self._timeout)
		self._original_key_press_event(event)

	def _widget_focus_in_event(self, event: QFocusEvent):
		"""
		Internal function used to override the focusOutEvent function of the primary widget.

		:param QKeyEvent event: key event.
		"""

		if not self._sliding_active:
			return
		if self._opened:
			self._close_timer.start(self._timeout)
			return

		if hasattr(event, 'reason') and \
				event.reason() == Qt.FocusReason.MouseFocusReason or hasattr(event, 'reason') is False:
			self.animate(expand=True)

			# force close after a few seconds
			self._close_timer.start(self._timeout)

		self._original_focus_in_event(event)

	def _widget_focus_out_event(self, event: QFocusEvent):
		"""
		Internal function used to override the focusInEvent function of the primary widget.

		:param QKeyEvent event: key event.
		"""

		if not self._sliding_active:
			return
		self.animate(expand=False)
		self._original_focus_out_event(event)

	def _on_close_timer_timeout(self):
		"""
		Internal callback function that is called when close timer time out.
		"""

		if self._timeout_active:
			self._primary_widget.clearFocus()
			self.focusCleared.emit()

