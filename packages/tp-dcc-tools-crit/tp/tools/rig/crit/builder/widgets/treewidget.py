from __future__ import annotations

from tp.common.qt import api as qt
from tp.common.qt.widgets import sliding, groupedtreewidget


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
		self.setup_toolbar()

		self.main_layout.addLayout(self._toolbar_layout)
		self.main_layout.addWidget(self._tree_widget)
		self.setLayout(self.main_layout)

	def setup_signals(self):
		"""
		Setups tree widget frame UI signals.
		"""

		self._search_edit.textChanged.connect(self._on_search_text_changed)

	def setup_toolbar(self) -> qt.QHBoxLayout:
		"""
		Intenral function that setup tree widget frame toolbar.

		:return: toolbar layout.
		:rtype: qt.QHBoxLayout
		"""

		self._search_edit.setMinimumSize(qt.size_by_dpi(qt.QSize(21, 20)))
		self._sliding_widget.set_widgets(self._search_edit, self._title_label)
		self._toolbar_layout.addWidget(self._sliding_widget)

		line = qt.QFrame(parent=self)
		line.setFrameShape(qt.QFrame.HLine)
		line.setFrameShadow(qt.QFrame.Sunken)
		self._toolbar_layout.addWidget(line)

		return self._toolbar_layout

	def refresh(self):
		"""
		Updates tree widget UI.
		"""

		if not self._tree_widget:
			return

		self._tree_widget.refresh()

	def add_group(self, name: str = '', expanded: bool = True):
		"""
		Adds a new group into the tree widget.

		:param str name: optional group name.
		:param bool expanded: whether group should be expanded by default.
		"""

		if not self._tree_widget:
			return

		group_widget = groupedtreewidget.GroupedTreeWidget.GroupWidget(title=name, hide_title_frame=True)
		group_widget.setFixedHeight(10)

		return self._tree_widget.add_group(name, expanded=expanded, group_widget=group_widget)

	def delete_group(self):
		"""
		Deletes group.
		"""

		raise NotImplementedError()

	def _on_search_text_changed(self, text: str):
		"""
		Internal callback function that is called each time search text changes.

		:param str text: search text.
		"""

		if not self._tree_widget:
			return

		self._tree_widget.filter(text)
		self._tree_widget.refresh()
