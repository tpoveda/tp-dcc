from __future__ import annotations

from typing import Tuple

from overrides import override
from Qt.QtCore import Signal
from Qt.QtWidgets import QSizePolicy, QFrame, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QToolButton, QSpacerItem
from Qt.QtGui import QIcon, QMouseEvent

from tp.common.qt import consts, dpi, qtutils
from tp.common.qt.widgets import layouts, labels, dividers
from tp.common.resources import api as resources


class BaseFrame(QFrame):
	"""
	Extended QFrame that expands following functionality:
		- Exposes a mouseReleased signal that is called when mouse is released
	"""

	mouseReleased = Signal(QMouseEvent)

	def mouseReleaseEvent(self, event: QMouseEvent) -> None:
		self.mouseReleased.emit(event)
		return super().mouseReleaseEvent(event)


class CollapsableFrame(QWidget):
	"""
	Collapsable frame layout with a title that is inside a colored background frame layout that can be opened and
	collapsed.
	"""

	_COLLAPSED_ICON = None			# type: QIcon
	_EXPAND_ICON = None				# type: QIcon

	openRequested = Signal()
	closeRequested = Signal()
	toggled = Signal()

	def __init__(
			self, title: str, collapsed: bool = False, collapsable: bool = True,
			content_margins: Tuple[int, int, int, int] = consts.MARGINS,  content_spacing: int = consts.SPACING,
			parent: QWidget | None = None):
		"""
		Constructor function.

		:param str title: name of the collapsable frame layout.
		:param bool collapsed: whether the frame is collapsed by default.
		:param bool collapsable: whether frame contents are collapsable.
		:param Tuple[int, int, int, int] content_margins: left, top, right, bottom margins of the collapsable contents
			section (in pixels).
		:param int content_spacing: spacing (padding) of the collapsable contents section (in pixels).
		:param QWidget or None parent: optional parent widget.
		"""

		super().__init__(parent=parent)

		self._title = title
		self._collapsed = collapsed if collapsable else False
		self._collapsable = collapsable
		self._content_margins = content_margins
		self._content_spacing = content_spacing

		self._title_frame = None						# type: BaseFrame
		self._horizontal_layout = None					# type: QHBoxLayout
		self._icon_button = None						# type: QToolButton
		self._title_label = None						# type: labels.BaseLabel
		self._spacer_item = None						# type: QSpacerItem
		self._hider_widget = None						# type: QFrame
		self._hider_layout = None						# type: QVBoxLayout

		if CollapsableFrame._COLLAPSED_ICON is None:
			CollapsableFrame._COLLAPSED_ICON = resources.icon('sort_closed')
		if CollapsableFrame._EXPAND_ICON is None:
			CollapsableFrame._EXPAND_ICON = resources.icon('sort_down')

		self._main_layout = layouts.vertical_layout(spacing=0, margins=(0, 0, 0, 0), parent=self)

		self._setup_ui()
		self._setup_signals()

	@property
	def hider_layout(self) -> QVBoxLayout:
		return self._hider_layout

	def add_widget(self, widget: QWidget):
		"""
		Adds given widget into the content layout.

		:param QWidget widget: widget to add.
		"""

		self._hider_layout.addWidget(widget)

	def add_layout(self, layout: QVBoxLayout | QHBoxLayout | QGridLayout):
		"""
		Adds given widget into the content layout.

		:param QVBoxLayout or QHBoxLayout or QGridLayout layout: layout to add.
		"""

		self._hider_layout.addLayout(layout)

	def expand(self):
		"""
		Expands/Shows contents.
		"""

		self.setUpdatesEnabled(False)
		self._hider_widget.show()
		self._icon_button.setIcon(self._EXPAND_ICON)
		self.setUpdatesEnabled(True)
		self.openRequested.emit()
		self._collapsed = False

	def collapse(self):
		"""
		Collapses/Hides contents.
		"""

		self.setUpdatesEnabled(False)
		self._hider_widget.hide()
		self._icon_button.setIcon(self._COLLAPSED_ICON)
		qtutils.process_ui_events()
		self.setUpdatesEnabled(True)
		qtutils.process_ui_events()
		self.closeRequested.emit()
		self._collapsed = True

	def _setup_ui(self):
		"""
		Internal function that setup widgets.
		"""

		self._build_title_frame()
		self._build_hider_widget()
		self._main_layout.addWidget(self._title_frame)
		self._main_layout.addWidget(self._hider_widget)

		qtutils.set_stylesheet_object_name(self._title_frame, 'collapsed')

	def _setup_signals(self):
		"""
		Internal function that setup signal connections.
		"""

		self.openRequested.connect(self.toggled.emit)
		self.closeRequested.connect(self.toggled.emit)
		self._icon_button.clicked.connect(self._on_icon_button_clicked)
		self._title_frame.mouseReleased.connect(self._on_title_frame_mouse_released)

	def _build_title_frame(self):
		"""
		Internal function that builds the title part of the layout with a QFrame widget.
		"""

		self._title_frame = BaseFrame(parent=self)
		self._title_frame.setContentsMargins(0, 0, 0, 0)
		self._horizontal_layout = layouts.horizontal_layout(margins=(0, 0, 0, 0), parent=self._title_frame)
		self._icon_button = QToolButton(parent=self)
		self._icon_button.setContentsMargins(0, 0, 0, 0)
		self._icon_button.setIcon(self._COLLAPSED_ICON  if self._collapsed else self._EXPAND_ICON)
		self._title_label = labels.BaseLabel(text=self._title, bold=True, parent=self)
		self._title_label.setContentsMargins(0, 0, 0, 0)
		self._spacer_item = QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
		self._horizontal_layout.addWidget(self._icon_button)
		self._horizontal_layout.addWidget(self._title_label)
		self._horizontal_layout.addItem(self._spacer_item)

	def _build_hider_widget(self):
		"""
		Intenral function that builds the collapsable widget.
		"""

		self._hider_widget = QFrame(parent=self)
		self._hider_widget.setContentsMargins(0, 0, 0, 0)
		self._hider_layout = layouts.vertical_layout(
			spacing=self._content_spacing, margins=self._content_margins, parent=self._hider_widget)
		self._hider_widget.setHidden(self._collapsed)

	def _show_hide_widget(self):
		"""
		Internal function that shows/hides the hider widget which contains the contents specified by the user.
		"""

		if not self._collapsable:
			return

		if self._collapsed:
			self.expand()
			return

		self.collapse()

	def _on_icon_button_clicked(self, *args):
		"""
		Internal callback function that is called each time icon button is clicked by the user.
		"""

		self._show_hide_widget()

	def _on_title_frame_mouse_released(self, *args):
		"""
		Internal callback function that is called each time mouse is released over title frame.
		"""

		self._show_hide_widget()


class CollapsableFrameThin(CollapsableFrame):

	@override
	def _build_title_frame(self):
		super()._build_title_frame()

		divider = dividers.Divider(parent=self)
		self._spacer_item.changeSize(dpi.dpi_scale(3), 0)
		divider.setToolTip(self.toolTip())
		self._horizontal_layout.addWidget(divider, 1)
