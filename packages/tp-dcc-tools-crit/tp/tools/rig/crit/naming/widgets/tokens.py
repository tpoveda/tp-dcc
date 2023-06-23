from __future__ import annotations

from overrides import override

from tp.common.qt import api as qt
from tp.common.naming import manager, token


class TokenDataSource(qt.BaseDataSource):
	def __init__(
			self, header_text: str | None = None, model: qt.BaseListModel | None = None, parent: qt.QWidget | None = None):
		super().__init__(header_text=header_text, model=model, parent=parent)

		self._tokens = list()			# type: list[token.Token]

	@override
	def row_count(self) -> int:
		return len(self._tokens)

	@override
	def is_editable(self, index: int) -> bool:
		return False

	@override
	def data(self, index: int) -> str:
		return self._tokens[index].name

	@override
	def tooltip(self, index: int) -> str:
		return self._tokens[index].description

	@override
	def foreground_color(self, index: int) -> qt.QColor | None:
		return self.ENABLED_COLOR

	@override(check_signature=False)
	def user_object(self, index: int) -> token.Token:
		return self._tokens[index]

	@override(check_signature=False)
	def set_user_objects(self, objects: list[token.Token]):
		self._tokens = objects


class TokenKeyValueKeyDataSource(qt.BaseDataSource):
	def __init__(self, model: qt.BaseTableModel | None = None, parent: qt.QWidget | None = None):
		super().__init__(header_text='Name', model=model, parent=parent)

	@property
	def children(self) -> list[token.KeyValue]:
		return self._children

	@override
	def column_count(self) -> int:
		return 2

	@override
	def is_editable(self, index: int) -> bool:
		return not self.user_object(index).protected

	@override
	def data(self, index: int) -> str:
		return self.user_object(index).name

	@override
	def set_data(self, index: int, value: str) -> bool:
		self.user_object(index).name = value
		return True

	@override
	def foreground_color(self, index: int) -> qt.QColor | None:
		return self.ENABLED_COLOR

	@override(check_signature=False)
	def user_object(self, index: int) -> token.KeyValue:
		return super().user_object(index)

	@override(check_signature=False)
	def user_objects(self) -> list[token.KeyValue]:
		return self._children

	@override(check_signature=False)
	def insert_row_data_sources(self, index: int, count: int, key_values):
		self.insert_children(index, key_values)
		return True


class TokenKeyValueValueDataSource(qt.BaseDataSource):

	@override(check_signature=False)
	def is_editable(self, row_data_source: qt.BaseDataSource, index: int) -> bool:
		return True

	@override(check_signature=False)
	def data(self, row_data_source: qt.BaseDataSource, index: int) -> str:
		key_value = row_data_source.user_object(index)		# type: token.KeyValue
		return key_value.value

	@override(check_signature=False)
	def set_data(self, row_data_source: qt.BaseDataSource, index: int, value: str) -> bool:
		key_value = row_data_source.user_object(index)
		key_value.value = str(value)
		return True


class TokensWidget(qt.QSplitter):
	def __init__(self, parent: qt.QWidget):
		super().__init__(parent)

		key_value_widget = qt.QWidget(parent=self)
		key_value_layout = qt.vertical_layout(spacing=1, parent=key_value_widget)
		key_value_options_edit_layout = qt.horizontal_layout(spacing=qt.consts.SPACING)
		self._add_key_value_label_button = qt.BaseButton(icon='plus', parent=self)
		self._remove_key_value_label_button = qt.BaseButton(icon='minus', parent=self)
		key_value_options_edit_layout.addStretch(0)
		key_value_options_edit_layout.addWidget(self._add_key_value_label_button)
		key_value_options_edit_layout.addWidget(self._remove_key_value_label_button)

		self._setup_views()
		self._setup_data_sources()

		key_value_layout.addWidget(self._key_value_table)
		key_value_layout.addLayout(key_value_options_edit_layout)
		self.addWidget(self._tokens_list)
		self.addWidget(key_value_widget)

		self._setup_signals()

	def refresh(self):
		"""
		Refreshes tokens list and table views.
		"""

		self.refresh_tokens_list()
		self.refresh_tokens_table()

	def refresh_tokens_list(self):
		"""
		Refreshes tokens list view.
		"""

		self._tokens_list_model.refresh()
		self._tokens_list.refresh()

	def refresh_tokens_table(self):
		"""
		Refreshes tokens table view.
		"""

		self._key_value_model.refresh()
		self._key_value_table.refresh()

	def reload_from_name_manager(self, name_manager: manager.NameManager):

		tokens = list(sorted(name_manager.iterate_tokens(recursive=True), key=lambda x: x.name))
		self._tokens_list_data_source.set_user_objects(tokens)
		self.refresh_tokens_list()
		self._tokens_list.selection_model().setCurrentIndex(
			self._tokens_list.model().index(0, 0), qt.QItemSelectionModel.ClearAndSelect)

	def _setup_views(self):
		"""
		Internal function that creates the view widgets within this splitter.
		"""

		self._tokens_list = qt.ExtendedListView(searchable=False, parent=self)
		self._tokens_list.setMaximumWidth(qt.dpi_scale(150))
		self._key_value_table = qt.ExtendedTableView(searchable=False, manual_reload=False, parent=self)
		self._key_value_table.table_view.verticalHeader().setVisible(False)
		self._tokens_list_model = qt.BaseListModel(parent=self)
		self._key_value_model = qt.BaseTableModel(parent=self)
		self._tokens_list.set_model(self._tokens_list_model)
		self._key_value_table.set_model(self._key_value_model)

	def _setup_data_sources(self):
		"""
		Creates the data sources and connects them to the respective views.
		"""

		self._tokens_list_data_source = TokenDataSource(model=self._tokens_list_model)
		self._tokens_edit_data_source = TokenKeyValueKeyDataSource(model=self._key_value_model)
		self._tokens_list.register_row_data_source(self._tokens_list_data_source)
		self._key_value_table.register_row_data_source(self._tokens_edit_data_source)
		self._key_value_table.register_column_data_sources([TokenKeyValueValueDataSource(header_text='Value')])

	def _setup_signals(self):
		"""
		Internal function that setup widget signals.
		"""

		self._tokens_list.selectionChanged.connect(self._on_tokens_list_selection_changed)

	def _on_tokens_list_selection_changed(self, event: qt.ExtendedListView.ExtendedListViewSelectionChangedEvent):
		"""
		Internal callback function that is called when a token item is selected.

		:param qt.ExtendedListView.ExtendedListViewSelectionChangedEvent event: selection changed event.
		"""

		for item in event.current_items:
			self._tokens_edit_data_source.set_user_objects(list(sorted(item.iterate_key_values(), key=lambda x: x.name)))
			break

		self.refresh_tokens_table()
