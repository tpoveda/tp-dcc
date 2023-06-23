from typing import Type

from overrides import override

from tp.common.qt import api as qt
from tp.common.qt.widgets import overlay
from tp.common.resources import api as resources


class LoadingWidget(overlay.OverlayWidget):
	"""
	Overlay widget that appears on top of other widgets and shows a label with a loading image at the center.
	"""

	def __init__(self, parent: qt.QWidget):
		super().__init__(parent, layout_class=qt.QHBoxLayout)

	@override
	def setup_ui(self, layout_class: Type = qt.QLayout):
		super().setup_ui(layout_class)

		self.setStyleSheet('LoadingWidget {background-color: #77111111;}')

		self._label = qt.QLabel('Loading...  ', parent=self)
		self._image_label = qt.QLabel(parent=self)
		size = qt.dpi_scale(24)
		self._image_label.setPixmap(resources.icon('loading').pixmap(size, size))

		self._loading_frame = LoadingFrame(parent=self)
		self._loading_frame_layout = qt.horizontal_layout()
		self._loading_frame.setLayout(self._loading_frame_layout)

		self._loading_frame_layout.addWidget(self._image_label)
		self._loading_frame_layout.addWidget(self._label)
		self._loading_frame_layout.setContentsMargins(*qt.margins_dpi_scale(5, 0, 5, 0))
		self._loading_frame_layout.setStretch(0, 2)
		self._loading_frame_layout.setStretch(1, 3)
		self._loading_frame.setFixedSize(qt.size_by_dpi(qt.QSize(150, 40)))
		qt.set_stylesheet_object_name(self._loading_frame, 'border')

		self.main_layout.addStretch(1)
		self.main_layout.addWidget(self._loading_frame)
		self.main_layout.addStretch(1)

	@override
	def update(self) -> None:
		x1 = qt.consts.FRAMELESS_HORIZONTAL_PADDING
		y1 = qt.consts.FRAMELESS_VERTICAL_PADDING
		x_padding = qt.consts.FRAMELESS_HORIZONTAL_PADDING
		y_padding = qt.consts.FRAMELESS_VERTICAL_PADDING
		self.setGeometry(
			x1, y1,
			self.parent().geometry().width() - x_padding * 2,
			self.parent().geometry().height() - y_padding * 2)
		super().update()

	@override
	def mousePressEvent(self, event: qt.QMouseEvent) -> None:
		super().mousePressEvent(event)
		self.hide()


class LoadingFrame(qt.QFrame):
	"""
	For stylesheet purposes
	"""

	pass
