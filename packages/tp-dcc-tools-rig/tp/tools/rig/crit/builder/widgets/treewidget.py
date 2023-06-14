from __future__ import annotations

from tp.common.qt import api as qt
from tp.common.qt.widgets import sliding


class TreeWidgetFrame(qt.QFrame):

	class SearchSlidingWidget(sliding.SlidingWidget):

		def _widget_focus_out_event(self, event: qt.QFocusEvent):
			if self._primary_widget is not None and self._primary_widget.text() != '':
				return super()._widget_focus_out_event(event)

	def __init__(self, title: str = '', parent: qt.QWidget | None = None):
		super().__init__(parent)

		self.main_layout = qt.vertical_layout()
		self._title_label = qt.clipped_label(text=title.upper(), parent=self)
		self._search_edit = qt.SearchLineEdit(parent=self)
		self._sliding_widget = TreeWidgetFrame.SearchSlidingWidget(parent=self)
		self._toolbar_layout = qt.horizontal_layout(spacing=0, margins=(10, 6, 6, 0))

		self._tree_widget = None			# type: qt.QTreeWidget

	@property
	def tree_widget(self) -> qt.QTreeWidget | None:
		return self._tree_widget

	def setup_ui(self, tree_widget: qt.QTreeWidget):
		"""
		Setups tree widget frame UI with given Qt tree widget.

		:param  qt.QTreeWidget tree_widget: tree widget instance.
		"""

		self._tree_widget = tree_widget
		self._setup_toolbar()

		self.main_layout.addLayout(self._toolbar_layout)
		self.main_layout.addWidget(self._tree_widget)
		self.setLayout(self.main_layout)

	def _setup_toolbar(self):
		"""
		Intenral function that setup tree widget frame toolbar.
		"""

		pass
