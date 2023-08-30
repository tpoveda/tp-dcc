from __future__ import annotations

import typing
from typing import List

from overrides import override

from tp.common.qt import api as qt
from tp.tools.animpicker import consts

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.widgets.buttons import ColorButton


class TearOffDialog(qt.QDialog):
	pass


class ColorPaletteDialog(qt.QDialog):

	saveINI = qt.Signal()

	def __init__(self, custom_colors: List[qt.QColor] | None = None, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._designated_button = None
		self._revert_color = qt.QColor()
		self._close = False

		self.setWindowFlags(self.windowFlags() & ~qt.Qt.WindowContextHelpButtonHint)
		self.setWindowFlags(self.windowFlags() | qt.Qt.Popup)
		self.setWindowTitle('Color Swatch Palette')

		layout = qt.vertical_layout(margins=(6, 6, 6, 6))
		self.setLayout(layout)

		self._palette_widget = ColorPaletteWidget(draggable=False, custom_colors=custom_colors, parent=self)

		button_layout = qt.horizontal_layout()
		self._done_button = qt.QPushButton('Done', parent=self)
		self._revert_button = qt.QPushButton('Revert', parent=self)
		button_layout.addWidget(self._done_button)
		button_layout.addWidget(self._revert_button)

		layout.addWidget(self._palette_widget)
		layout.addLayout(button_layout)

		self._palette_widget.setButtonColor.connect(self._on_palette_set_button_color)
		self._done_button.clicked.connect(self.close)
		self._revert_button.clicked.connect(self._on_revert_button_clicked)

	@property
	def designated_button(self) -> ColorButton:
		return self._designated_button

	@designated_button.setter
	def designated_button(self, value: ColorButton):
		self._designated_button = value
		self._revert_color = value.color()

	@override
	def showEvent(self, arg__1: qt.QShowEvent) -> None:
		self.adjustSize()
		self.setFixedSize(self.size())
		super().showEvent(arg__1)

	@override
	def closeEvent(self, arg__1: qt.QCloseEvent) -> None:
		if self.sender() is None and not self._close:
			self._revert()
		self._close = False
		self.saveINI.emit()
		super().closeEvent(arg__1)

	@override
	def close(self) -> bool:
		self._close = True
		return super().close()

	def set_designated_button_color(self, color: qt.QColor):
		"""
		Sets current button color.

		:param ColorButton color: color to set color button instance to.
		"""

		if self.designated_button:
			self.designated_button.set_color(color)

	def clear_selection(self):
		"""
		Clears current selected color
		"""

		self._palette_widget.clear_selection()

	def _revert(self):
		"""
		Internal function that reverts to previous selected color.
		"""

		self.set_designated_button_color(self._revert_color)
		self.close()

	def _on_palette_set_button_color(self, color: qt.QColor):
		"""
		Internal callback function that is called when Palette Set Button color signal is called.

		:param qt.QColor color: set color.
		"""

		if self.designated_button:
			self.designated_button.set_color(color)

	def _on_revert_button_clicked(self):
		"""
		Internal callback function that is called when Revert button is clicked by the user.
		"""

		self._revert()


class ColorPaletteWidget(qt.QWidget):

	setButtonColor = qt.Signal(qt.QColor)

	def __init__(
			self, draggable: bool = True, custom_colors: List[qt.QColor] | None = None,
			parent: ColorPaletteDialog | None = None):
		super().__init__(parent=parent)

		self._pressed = None						# type: qt.QPushButton
		self._drag_color = qt.QColor()
		self._draggable = draggable
		self._previous_button = None

		layout = qt.vertical_layout(spacing=1, margins=(0, 0, 0, 0))
		self.setLayout(layout)

		if custom_colors:
			self._build_color_column(custom_colors)

		self._build_gray_color_column(0.06)
		self._build_hsv_color_column(0.06, 0.2, 1.0)
		self._build_hsv_color_column(0.06, 0.4, 1.0)
		self._build_hsv_color_column(0.06, 0.6, 1.0)
		self._build_hsv_color_column(0.06, 0.8, 1.0)
		self._build_hsv_color_column(0.06, 1.0, 1.0)
		self._build_hsv_color_column(0.06, 1.0, 0.8)
		self._build_hsv_color_column(0.06, 1.0, 0.6)
		self._build_hsv_color_column(0.06, 1.0, 0.4)
		self._build_hsv_color_column(0.06, 1.0, 0.2)

	@override
	def eventFilter(self, watched: qt.QObject, event: qt.QEvent) -> bool:

		if self._draggable and isinstance(watched, qt.QPushButton):
			if event.type() == qt.QEvent.MouseButtonPress:
				self._pressed = watched
				self._drag_color = watched.palette().color(qt.QPalette.Button)
			elif event.type() == qt.QEvent.MouseMove:
				if self._pressed == watched:
					if watched.isDown():
						watched.setDown(False)
					drag = qt.QDrag(watched)
					data = qt.QMimeData()
					data.setData(consts.MIME_COLOR, 'color')
					data.setColorData(self._drag_color)
					drag.setMimeData(data)
					pixmap = qt.QPixmap(18, 18)
					pixmap.fill(self._drag_color)
					drag.setDragCursor(pixmap, qt.Qt.CopyAction)
					drag.start()
					self._pressed = None
			elif event.type() == qt.QEvent.MouseButtonRelease:
				self._pressed = None
			elif event.type() == qt.QEvent.ChildRemoved:
				watched.setDown(False)

		return super().eventFilter(watched, event)

	def clear_selection(self):
		"""
		Clear selected color.
		"""

		if self._previous_button:
			color = self._previous_button.property('color')
			rgb_color = color.getRgb()[:3]
			rgb_color_lighter = color.lighter(120).getRgb()[:3]
			self._previous_button.setStyleSheet(
				'QPushButton{background-color: rgb(' + str(rgb_color[0]) + ', ' + str(rgb_color[1]) + ', ' +
				str(rgb_color[2]) + ');}QPushButton:hover{background-color: rgb(' + str(rgb_color_lighter[0]) + ', '
				+ str(rgb_color_lighter[1]) + ', ' + str(rgb_color_lighter[2]) + '); border: 1px solid black;}')
		self._previous_button = None

	def _build_color_column(self, color_set: List[qt.QColor]):
		"""
		Internal function that builds color column from the given list of colors.

		:param List[qt.QColor] color_set: list of colors.
		"""

		layout = qt.horizontal_layout(spacing=1, margins=(0, 0, 0, 0))
		for color in color_set:
			frame = qt.QFrame(parent=self)
			frame.setFixedSize(20, 20)
			frame.setFrameShape(qt.QFrame.Box)
			frame.setFrameShadow(qt.QFrame.Plain)
			frame.setLineWidth(0)
			frame_layout = qt.horizontal_layout(margins=(0, 0, 0, 0))
			button = qt.QPushButton(parent=frame)
			button.setFixedSize(qt.QSize(18, 18))
			button.setFocusPolicy(qt.Qt.NoFocus)
			rgb_color = color.getRgb()[:3]
			rgb_color_lighter = color.lighter(120).getRgb()[:3]
			button.setStyleSheet(
				'QPushButton{background-color: rgb(' + str(rgb_color[0]) + ', ' + str(rgb_color[1]) + ', ' +
				str(rgb_color[2]) + ');}QPushButton:hover{background-color: rgb(' + str(rgb_color_lighter[0]) + ', '
				+ str(rgb_color_lighter[1]) + ', ' + str(rgb_color_lighter[2]) + '); border: 1px solid black;}')
			button.setProperty('color', color)
			frame.setLayout(frame_layout)
			layout.addWidget(frame)
			color_palette_tooltip = 'To change a color, drag and drop onto a button.\nOr if you drop onto map, it changes background color.\nColor : '
			if hasattr(color, 'ann'):
				button.setToolTip(f'{("" if not self._draggable else color_palette_tooltip)}{color.ann}')
			else:
				button.setToolTip(f'{("" if not self._draggable else color_palette_tooltip)}' + 'R%d G%d B%d' % color.getRgb()[:3])
			button.installEventFilter(self)
			button.clicked.connect(self._on_color_button_clicked)
			button.pressed.connect(self._on_color_button_pressed)
		layout.addStretch()
		self.layout().insertLayout(self.layout().count(), layout)

	def _build_gray_color_column(self, step: float):
		"""
		Internal function that builds a grey color column with given gray step.

		:param float step: gray step.
		"""

		color_set = []
		value = 0.0
		while value < 1.0:
			color_set.append(qt.QColor.fromRgbF(value, value, value))
			value += step
		self._build_color_column(color_set)

	def _build_hsv_color_column(self, step: float, saturation: float, value: float):
		"""
		Internal function that builds HSV color column.

		:param float step: HSV color step
		:param float saturation: HSV color saturation.
		:param float value: HSV color value.
		"""

		color_set = []
		hue = 0.0
		while hue < 1.0:
			color_set.append(qt.QColor.fromHsvF(hue, saturation, value))
			hue += step
		self._build_color_column(color_set)

	def _on_color_button_clicked(self):
		"""
		Internal callback function that is called each time a color button is clicked by the user.
		"""

		self.setButtonColor.emit(self.sender().property('color'))

	def _on_color_button_pressed(self):
		"""
		Internal callback function that is called each time a color button is pressed by the user.
		"""

		self.clear_selection()
		button = self.sender()
		rgb_color_darker = button.property('color').darker(120).getRgb()[:3]
		button.setStyleSheet(
			'QPushButton{background-color: rgb(' + str(rgb_color_darker[0]) + ', ' + str(rgb_color_darker[1]) + ', ' +
			str(rgb_color_darker[2]) + ');border: 2px solid black;}')
		self._previous_button = button
