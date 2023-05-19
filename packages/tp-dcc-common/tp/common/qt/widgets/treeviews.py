from __future__ import annotations

from Qt.QtCore import Qt, Signal, QModelIndex, QItemSelectionModel, QItemSelection
from Qt.QtWidgets import QApplication, QWidget, QFrame, QTreeView
from Qt.QtGui import QMouseEvent

from tp.common.qt import qtutils
from tp.common.qt.models import utils, treemodel, sortmodel
from tp.common.qt.widgets import layouts


class BaseTreeView(QTreeView):
	"""
	Extended QTreeView that extends default QTreeView with the following functionality:
		- Adds itemDoubleClicked signal that is emitted when user double-click on an item.
		- If shift ke is pressed, all the children items of the expanded/collapsed item will be also expanded/collapsed.
	"""

	itemDoubleClicked = Signal(QModelIndex)

	def __init__(self, parent: QWidget | None = None):
		super().__init__(parent)

		self._supports_shift_expand = True
		self.expanded.connect(self._on_expanded)

		self.setFocusPolicy(Qt.StrongFocus)

	def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
		index = self.indexAt(event.pos())
		if index.isValid():
			data_model_index, _ = utils.data_model_index_from_index(index)
			self.itemDoubleClicked.emit(data_model_index)

		super().mouseDoubleClickEvent(event)

	def _on_expanded(self, index: QModelIndex, expand: bool = True):
		"""
		Internal callback function that is called each time a tree view item is expanded.
		If shift key is pressed, all the children items of the expanded/collapsed item will be also expanded/collapsed.

		:param QModelIndex index: expanded model index.
		:param bool expand: whether the item was expanded/collapsed.
		"""

		modifier_pressed = QApplication.instance().keyboardModifiers() == Qt.ShiftModifier
		if not modifier_pressed and self._supports_shift_expand:
			return

		for i in range(self.model().rowCount(index)):
			child_index = self.model().index(i, 0, index)
			self.setExpanded(child_index, expand)


class ExtendedTreeView(QFrame):

	class ExtendedTreeViewSelectionChangedEvent:
		def __init__(self, current: QItemSelection, previous: QItemSelection, parent: ExtendedTreeView):
			self.indices = current.indexes()
			self.prev_indices = previous.indexes()
			self.current_items = [
				parent.model.item_from_index(utils.data_model_index_from_index(i)[0]) for i in self.indices]
			self.prev_items = [
				parent.model.item_from_index(utils.data_model_index_from_index(i)[0]) for i in self.prev_indices]

	selectionChanged = Signal(ExtendedTreeViewSelectionChangedEvent)
	contextMenuRequested = Signal(list, object)
	refreshRequested = Signal()

	def __init__(self, title: str = '', parent: QWidget | None = None, expand: bool = True, sorting: bool = True):
		super().__init__(parent)

		self.setFrameStyle(QFrame.NoFrame | QFrame.Plain)

		self._sorting = sorting
		self._model = None								# type: treemodel.BaseTreeModel
		self._column_data_sources = list()

		self._setup_ui()
		self._setup_signals()

		if expand:
			self.expand_all()

	@property
	def model(self) -> treemodel.BaseTreeModel:
		return self._model

	@property
	def tree_view(self) -> BaseTreeView:
		return self._tree_view

	def selection_model(self) -> QItemSelectionModel:
		"""
		Returns selection model for current model.

		:return: selection model.
		:rtype: QItemSelectionModel
		"""

		return self._tree_view.selectionModel()

	def set_model(self, model: treemodel.BaseTreeModel):
		"""
		Set the source model used by this view.

		:param treemodel.BaseTreeModel model: model to use.
		"""

		self._proxy_search.setSourceModel(model)
		self._proxy_search.setDynamicSortFilter(self._sorting)
		self._model = model

	def set_sorting_enabled(self, flag: bool):
		"""
		Sets whether sort is enabled witihn tree view model.

		:param bool flag: True to sort model; False otheriwse.
		"""

		self._tree_view.setModel(self._proxy_search)
		self._tree_view.setSortingEnabled(flag)
		self._tree_view.sortByColumn(0, Qt.AscendingOrder)
		self._proxy_search.setDynamicSortFilter(flag)
		if flag:
			self._proxy_search.setFilterKeyColumn(0)

	def set_alternating_color_enabled(self, flag: bool):
		"""
		Sets whether view should display tree rows with alternating colors.

		:param bool flag: True to alternate tree view row colors; False otherwise.
		"""

		qtutils.set_stylesheet_object_name(self._tree_view, '' if flag else 'disableAlternatingColor')
		self._tree_view.setAlternatingRowColors(flag)

	def expand_all(self):
		"""
		Expands all tree view contents.
		"""

		self._tree_view.expandAll()

	def collapse_all(self):
		"""
		Collapses all tree view contents.
		"""

		self._tree_view.collapseAll()

	def refresh(self):
		"""
		Refreshes tree view based on the model contents and adjust columns to the displayed contents.
		"""

		print('refreshing ...')
		print(self._model)

		for index in range(self._model.columnCount(QModelIndex())):
			self._tree_view.resizeColumnToContents(index)
			self._tree_view.setColumnWidth(index, self._tree_view.columnWidth(index) + 10)

	def _setup_ui(self):
		"""
		Internal function that creates tree view widgets.
		"""

		self._main_layout = layouts.vertical_layout(parent=self)

		self._tree_view = BaseTreeView(parent=self)
		self._tree_view.setSelectionMode(QTreeView.ExtendedSelection)
		self._tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
		self._main_layout.addWidget(self._tree_view)

		self._proxy_search = sortmodel.LeafTreeFilterProxyModel(sort=False, parent=self)
		self.set_sorting_enabled(self._sorting)
		self.set_alternating_color_enabled(True)

	def _setup_signals(self):
		"""
		Internal function that connects signals.
		"""

		selection_model = self.selection_model()
		selection_model.selectionChanged.connect(self._on_selection_changed)

	def _on_selection_changed(self, current: QItemSelection, previous: QItemSelection):
		"""
		Internal callback function that is called each time an item in the tree view is selected by the user.

		:param QItemSelection current: current selected items.
		:param QItemSelection previous: previous selected items.
		"""

		event = ExtendedTreeView.ExtendedTreeViewSelectionChangedEvent(current=current, previous=previous, parent=self)
		self.selectionChanged.emit(event)
