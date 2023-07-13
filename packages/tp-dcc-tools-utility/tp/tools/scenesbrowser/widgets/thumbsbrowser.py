from __future__ import annotations

import typing
from typing import List, Dict, Type

from overrides import override
from Qt.QtCore import Qt, QObject, Signal, QSize, QModelIndex, QThreadPool, QSortFilterProxyModel, QAbstractItemModel
from Qt.QtWidgets import (
	QSizePolicy, QWidget, QHBoxLayout, QListView, QStyledItemDelegate, QStyleOptionViewItem, QAction, QAbstractItemView
)
from Qt.QtGui import QIcon, QPainter, QStandardItemModel

from tp.preferences.interfaces import core
from tp.common.python import osplatform, helpers, path
from tp.common.qt import consts, dpi, qtutils, contexts
from tp.common.qt.widgets import layouts, buttons, frameless, treeviews, popups
from tp.common.qt.models import utils, datasources, treemodel, delegates, consts as model_consts
from tp.common.resources import api as resources

if typing.TYPE_CHECKING:
	from tp.preferences.assets import BrowserPreference
	from tp.tools.toolbox.widgets.toolui import ToolUiWidget

IMAGE_EXTENSIONS = consts.QT_SUPPORTED_EXTENSIONS


class ModelRoles:

	TAG = Qt.UserRole + 1
	DESCRIPTION = Qt.UserRole + 2
	FILENAME = Qt.UserRole + 3
	WEBSITES = Qt.UserRole + 4
	CREATOR = Qt.UserRole + 5
	RENDERER = Qt.UserRole + 6
	TAG_TO_ROLE = {
		'tags': TAG,
		'filename': FILENAME,
		'description': DESCRIPTION,
		'creators': CREATOR,
		'websites': WEBSITES,
		'renderer': RENDERER
	}


class ThumbsListView(QListView):

	contextMenuRequested = Signal(list, object)
	stateChanged = Signal()

	_DEFAULT_ICON_SIZE = QSize(256, 256)
	_DEFAULT_COLUMN_COUNT = 4
	_MAX_THREAD_COUNT = 200

	def __init__(
			self, icon_size: QSize = _DEFAULT_ICON_SIZE, uniform_icons: bool = False,
			delegate_class: Type | None = None, parent: QWidget | None = None):
		super().__init__(parent)

		self._current_icon_size = icon_size or self._DEFAULT_ICON_SIZE
		self._column_count = self._DEFAULT_COLUMN_COUNT
		self._uniform_icons = uniform_icons
		self._delegate = delegate_class(self) if delegate_class is not None else ThumbnailDelegate(self)
		self._zoomable = True
		self._pagination = True
		self._persistent_filter = []				# type: List[str, List[str]]

		self._thread_pool = QThreadPool.globalInstance()
		self._thread_pool.setMaxThreadCount(self._MAX_THREAD_COUNT)

		self._proxy_filter_model = MultipleFilterProxyModel(parent=self)
		self._proxy_filter_model.setDynamicSortFilter(True)
		self._proxy_filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

		self.setLayoutMode(self.LayoutMode.Batched)
		self.setItemDelegate(self._delegate)
		self.setIconSize(self._current_icon_size)

		self._setup_ui()
		self._setup_signals()

	@override(check_signature=False)
	def setModel(self, model: ThumbsBrowserFileModel) -> None:
		self._proxy_filter_model.setSourceModel(model)
		model.set_uniform_item_sizes(self._uniform_icons)
		result = super().setModel(self._proxy_filter_model)
		self.selectionModel().selectionChanged.connect(self._on_selection_changed)

		return result

	def root_model(self) -> ThumbsBrowserFileModel:
		"""
		Returns root source model instance.

		:return: root source model.
		:rtype: ThumbsBrowserFileModel
		"""

		return utils.data_model_from_proxy_model(self.model())

	def _setup_ui(self):
		"""
		Internal function that initializes thumbnails list view widgets.
		"""

		self.setMouseTracking(True)
		self.setViewMode(QListView.IconMode)
		self.setResizeMode(QListView.Adjust)
		self.setSelectionMode(QListView.SingleSelection)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setUniformItemSizes(self._uniform_icons)
		self.setDragEnabled(False)
		self.setAcceptDrops(False)
		self.setUpdatesEnabled(True)
		self.verticalScrollBar().setSingleStep(5)

	def _setup_signals(self):
		"""
		Internal function that setup signal connections.
		"""

		vertical_scrollbar = self.verticalScrollBar()
		vertical_scrollbar.valueChanged.connect(self._on_vertical_scrollbar_value_changed)
		vertical_scrollbar.rangeChanged.connect(self._on_vertical_scrollbar_range_changed)
		vertical_scrollbar.sliderReleased.connect(self.stateChanged.emit)
		self.clicked.connect(self.stateChanged.emit)
		self.activated.connect(self.stateChanged.emit)
		self.entered.connect(self.stateChanged.emit)

	def _on_vertical_scrollbar_value_changed(self):
		"""
		Internal callback function that is called each time vertical scrollbar value changes.
		"""

		pass

	def _on_vertical_scrollbar_range_changed(self):
		"""
		Internal callback function that is called each time vertical scrollbar range changes.
		"""

		pass

	def _on_selection_changed(self):
		"""
		Internal callback function that is called each time model selection changes.
		"""

		print('Selection changed ...')


class ThumbsBrowser(QWidget):

	_THEME_PREFS = None

	class SnapshotType:
		NEW = 0
		EDIT = 1

	class ThumbsBrowserListView(ThumbsListView):

		def __init__(self, slider: bool = False, slider_args: Dict | None = None, *args, **kwargs):
			super().__init__(*args, **kwargs)

			slider_args = slider_args or {}
			self._virtual_slider = None
			if slider:
				pass

	class DotsMenu(buttons.IconMenuButton):

		MENU_ICON = 'menu_dots'

		applyAction = Signal()
		createAction = Signal()
		renameAction = Signal()
		deleteAction = Signal()
		browseAction = Signal()
		setDirectoryAction = Signal()
		refreshAction = Signal()

		APPLY_ACTION = 0
		CREATE_ACTION = 1
		RENAME_ACTION = 2
		DELETE_ACTION = 3
		BROWSE_ACTION = 4
		SET_DIRECTORY_ACTION = 5
		REFRESH_ACTION = 6

		def __init__(
				self, uniform_icons: bool = True, item_name: str = '', apply_text: str = 'Apply',
				apply_icon: str = 'checkmark', create_text: str = 'New', parent: ThumbsBrowser | None = None):

			self._uniform_icons = uniform_icons
			self._dots_menu_name = item_name
			self._apply_text = apply_text
			self._apply_icon = apply_icon
			self._create_text = create_text
			self._menu_actions = {}  # type: Dict[str or int, QAction]

			super().__init__(parent=parent)

		@override
		def setup_ui(self):
			super().setup_ui()

			self.set_icon(self.MENU_ICON)
			self.setToolTip(f'File menu. Manage {self._dots_menu_name}')

			file_browser = 'Finder' if osplatform.is_mac() else 'Explorer'

			apply_icon = resources.icon(self._apply_icon)
			save_icon = resources.icon('save')
			rename_icon = resources.icon('rename')

			new_actions = [
				('DoubleClick', (f'{self._apply_text} (Double Click)', self.applyAction.emit, apply_icon, False)),
				(ThumbsBrowser.DotsMenu.CREATE_ACTION, (f'{self._create_text} {self._dots_menu_name}', self.createAction.emit, save_icon, False)),
			]
			for key, value in new_actions:
				if value is None and key == '---':
					self.add_separator()
				else:
					text, connect, icon, checkable = value
					self._menu_actions[key] = self.addAction(text, connect=connect, action_icon=icon, checkable=checkable)

	def __init__(
			self, tool_ui_widget: ToolUiWidget | None = None, columns: int | None = None, icon_size: QSize | None = None,
			fixed_width: int | None = None, fixed_height: int | None = None, uniform_icons: bool = False,
			item_name: str = '', apply_text: str = 'Apply', apply_icon: str = 'checkmark', create_text: str = 'New',
			new_active: bool = True, snapshot_active: bool = False, snapshot_new_active: bool = False,
			clipboard_active: bool = False, create_thumbnail_active: bool = False, select_directories_active: bool = False,
			virtual_slider: bool = False, virtual_slider_args: Dict | None = None,
			list_delegate_class: ThumbnailDelegate | None = None, parent: QWidget | None = None):
		super().__init__(parent=parent)

		if ThumbsBrowser._THEME_PREFS is None:
			ThumbsBrowser._THEME_PREFS = core.theme_preference_interface()

		self._tool_ui_widget = tool_ui_widget
		self._uniform_icons = uniform_icons
		self._item_name = item_name
		self._apply_text = apply_text
		self._apply_icon = apply_icon
		self._create_text = create_text
		self._virtual_slider = virtual_slider
		self._list_delegate_class = list_delegate_class
		self._virtual_slider_args = virtual_slider_args or {}
		self._directory_popup = DirectoryPopup()
		self._snapshot_type = ThumbsBrowser.SnapshotType.EDIT
		self._has_refreshed_view = False
		self._auto_resize_items = True
		self._folder_popup_button = None										# type: buttons.BaseButton
		self._previous_save_directories = {'to': None, 'directories': []}

		if not select_directories_active:
			self._folder_popup_button.hide()

		if icon_size is not None:
			pass

		if columns:
			pass

		# if fixed_height:
		# 	self.setFixedHeight(dpi.dpi_scale(fixed_height), save=True)

		self._setup_ui()
		self._setup_signals()

	def model(self) -> ThumbsBrowserFileModel:
		"""
		Returns thumb browser model instance.

		:return: thumb browser model.
		:rtype: ThumbsBrowserFileModel
		"""

		return self._thumb_widget.root_model()

	def set_model(self, model: ThumbsBrowserFileModel):
		"""
		Sets thumb browser model to use.

		:param ThumbsBrowserFileModel model: thumb browser model instance.
		"""

		self._thumb_widget.setModel(model)
		model.refresh_asset_folders()
		model.refresh_list()

		self._directory_popup.selectionChanged.connect(self._on_directory_popup_selection_changed)
		model.itemSelectionChanged.connect(self._on_model_item_selection_changed)

	def _setup_ui(self):
		"""
		Internal function that setups thumbnail browser widgets.
		"""

		main_layout = layouts.vertical_layout(margins=(0, 0, 0, 0))
		self.setLayout(main_layout)

		self._thumb_widget = ThumbsBrowser.ThumbsBrowserListView(
			delegate_class=self._list_delegate_class, uniform_icons=self._uniform_icons, slider=self._virtual_slider,
			slider_args=self._virtual_slider_args, parent=self)
		self._thumb_widget.setSpacing(0)

		main_layout.addLayout(self._setup_top_bar())
		main_layout.addWidget(self._thumb_widget, 1)

	def _setup_signals(self):
		"""
		Internal function that creates widget signal connections.
		"""

		pass

	def _setup_top_bar(self) -> QHBoxLayout:
		"""
		Internal function that setup top bar widgets.

		:return: top bar horizontal layouts.
		:rtype: QHBoxLayout
		"""

		top_layout = layouts.horizontal_layout(spacing=consts.SMALL_SPACING, margins=(0, 0, 0, consts.SPACING))
		self._folder_popup_button = buttons.styled_button(
			icon='folder', style=consts.ButtonStyles.TRANSPARENT_BACKGROUND, tooltip='Folder')
		self._info_button = buttons.styled_button(
			icon='information', style=consts.ButtonStyles.TRANSPARENT_BACKGROUND,
			tooltip='Thumbnail information and add meta data')
		self._dots_menu = ThumbsBrowser.DotsMenu(
			uniform_icons=self._uniform_icons, item_name=self._item_name, apply_text=self._apply_text,
			apply_icon=self._apply_icon, create_text=self._create_text, parent=self)
		self._folder_popup_button.leftClicked.connect(self._on_folder_popup_button_left_clicked)

		top_layout.addWidget(self._folder_popup_button)
		top_layout.addWidget(self._info_button)
		top_layout.addWidget(self._dots_menu)

		return top_layout

	def _refresh_directory_popup(self):
		"""
		Internal function that refreshes directory popup window.
		"""

		model = self.model()
		model.update_from_prefs()
		self._directory_popup.anchor_widget = self
		self._directory_popup.browser_preference = self.model().preference()
		self._directory_popup.reset()
		self._directory_popup.set_active_items(model.active_directories, model.preference().active_categories())

	def _on_folder_popup_button_left_clicked(self):
		"""
		Internal callback function that is called each time folder popup button is left-clicked by the user.
		Opens select directories popup dialog.
		"""

		if not self._directory_popup.isVisible():
			self._refresh_directory_popup()
			self._directory_popup.show()
		else:
			self._directory_popup.close()

	def _on_directory_popup_selection_changed(self):
		"""
		Internal callback function that is called each time a directory is selected within directory popup window.
		"""

		print('Directory selected!')

	def _on_model_item_selection_changed(self):
		"""
		Internal callback function that is called each time model item selection changes.
		"""

		print('Model selection changed ...')


class DirectoryPopup(frameless.FramelessWindow):

	class DirectoryTitleBar(frameless.FramelessWindow.TitleBar):

		@override
		def set_title_style(self, style: str):
			if style != 'POPUP':
				return
			self.setFixedHeight(dpi.dpi_scale(30))
			self._title_label.setFixedHeight(dpi.dpi_scale(20))
			self._help_button.hide()
			self._logo_button.hide()
			self._close_button.hide()
			self._left_contents.hide()
			self.set_title_spacing(False)
			self._main_layout.setContentsMargins(0, 0, 0, 0)
			self._split_layout.setSpacing(0)
			qtutils.set_horizontal_size_policy(self._right_contents, QSizePolicy.Ignored)
			self._title_layout.setContentsMargins(*dpi.margins_dpi_scale(7, 8, 20, 7))
			self._main_right_layout.setContentsMargins(*dpi.margins_dpi_scale(0, 0, 8, 0))

	class FolderTreeModel(treemodel.BaseTreeModel):

		class CategoryFolderDataSource(datasources.BaseDataSource):
			"""
			Category folder within folder tree
			"""

			def __init__(
					self, directory_info: Dict, model: DirectoryPopup.FolderTreeModel,
					parent: datasources.BaseDataSource | None = None):
				super().__init__(header_text='', model=model, parent=parent)

				self._internal_data = directory_info
				self._icon = None

			@property
			def internal_data(self) -> Dict:
				return self._internal_data

			@override
			def column_count(self) -> int:
				return 1

			@override(check_signature=False)
			def insert_row_data_source(self, index: int, data: Dict, item_type: str) -> datasources.BaseDataSource:
				if item_type == 'category':
					new_item = self._model.browser_preference.create_category(
						category_id=None, name=data['alias'], parent=self.folder_id(), children=data.get('children', []))
					new_item = DirectoryPopup.FolderTreeModel.CategoryFolderDataSource(new_item, model=self.model, parent=self)
				else:
					directory_path = path.DirectoryPath(data['path'], alias=data.get('alias'))
					new_item = DirectoryPopup.FolderTreeModel(directory_path, model=self.model, parent=self)
				self.insert_child(index, new_item)

				return new_item

			@override
			def icon(self, index: int) -> QIcon | None:
				return self._icon

			@override
			def data(self, index: int) -> str:
				return 'root' if self.is_root() else self._internal_data['alias']

			@override
			def set_data(self, index: int, value: str) -> bool:
				if not value or value == self._internal_data['alias']:
					return False

				self._internal_data['alias'] = value

				return True

			def folder_id(self) -> str:
				"""
				Returns internal folder id.

				:return: folder id.
				"""

				return self._internal_data.get('id', '')

		class FolderItemDataSource(CategoryFolderDataSource):

			def __init__(
					self, directory_info: Dict, model: DirectoryPopup.FolderTreeModel,
					parent: datasources.BaseDataSource | None = None):
				super().__init__(directory_info=directory_info, model=model, parent=parent)

				self._icon = resources.icon('folder')

		def __init__(
				self, preference: BrowserPreference,  root: datasources.BaseDataSource | None, parent: QObject | None):
			super().__init__(root=root, parent=parent)

			self._browser_preference = preference

			self.dataChanged.connect(self._on_data_changed)
			self.rowsInserted.connect(self._on_rows_inserted)
			self.rowsRemoved.connect(self._on_rows_removed)

		@property
		def browser_preference(self) -> BrowserPreference:
			return self._browser_preference

		@browser_preference.setter
		def browser_preference(self, value: BrowserPreference):
			self._browser_preference = value

		@override
		def refresh(self):
			"""
			Reloads model data.
			"""

			categories, directories = self._browser_preference.categories(), self._browser_preference.browser_folder_paths()
			_root = DirectoryPopup.FolderTreeModel.CategoryFolderDataSource({}, model=self)
			tree = {d.id: DirectoryPopup.FolderTreeModel.FolderItemDataSource(d, model=self) for d in directories}
			for cat in categories:
				tree[cat['id']] = DirectoryPopup.FolderTreeModel.CategoryFolderDataSource(cat, model=self)
			for cat in categories:
				category_item = tree[cat['id']]
				parent = tree.get(cat['parent'] or '')
				children = cat['children'] or []
				if parent is not None:
					category_item.set_parent_source(parent)
				for child in children:
					existing_child = tree.get(child)
					if existing_child is None:
						continue
					existing_child.set_parent_source(category_item)

			for item in tree.values():
				if item.parent_source() is None:
					item.set_parent_source(_root)

			self.set_root(_root, refresh=False)

			super().refresh()

		def save_to_preferences(self):
			"""
			Updates browser preferences from the model data.
			"""

			directories = []
			categories = []

			for item in self.root.iterate_children(recursive=True):
				if type(item) == DirectoryPopup.FolderTreeModel.FolderItemDataSource:
					directories.append(item.internal_data)
					continue
				children = [i.folder_id() for i in item.children]
				parent = item.parent_source()
				data = item.internal_data
				parent_id = ''
				if not parent.is_root():
					parent_id = parent.folder_id()
				categories.append({'id': data['id'], 'alias': data['alias'], 'parent': parent_id, 'children': children})

			self._browser_preference.clear_browser_directories(save=False)
			self._browser_preference.clear_categories(save=False)
			self._browser_preference.add_browser_directories(directories, save=False)
			self._browser_preference.add_categories(categories, save=True)

		def _on_data_changed(self, top_left: QModelIndex, bottom_right: QModelIndex, role: Qt.UserRole):
			"""
			Internal callback function that is called each time model data changes.

			:param QModelIndex top_left:
			:param QModelIndex bottom_right:
			:param Qt.UserRole role:
			:return:
			"""

			data_source = self.item_from_index(top_left)
			if type(data_source) == DirectoryPopup.FolderTreeModel.CategoryFolderDataSource:
				self._browser_preference.update_category(data_source.folder_id(), data_source.internal_data)
				return

			self._browser_preference.set_directory_alias(data_source.internal_data)

		def _on_rows_inserted(self):
			"""
			Internal callback function that is called each time new rows are inserted into the model.
			Updates preferences from model data.
			"""

			self.save_to_preferences()

		def _on_rows_removed(self):
			"""
			Internal callback function that is called each time rows are removed from the model.
			Updates preferences from model data.
			"""

			self.save_to_preferences()

	selectionChanged = Signal(object)

	def __init__(
			self, auto_hide: bool = False, attach_to_parent: bool = True,
			browser_preference: BrowserPreference | None = None, parent: ThumbsBrowser | None = None):
		super().__init__(
			title='Directories', width=200, height=400, overlay=False, on_top=False, minimize_enabled=False,
			maximize_button=False, save_window_pref=False, title_bar_class=DirectoryPopup.DirectoryTitleBar, parent=parent)

		self._auto_hide = auto_hide
		self._attach_to_parent = attach_to_parent
		self._browser_preference = browser_preference
		self._browsing = False
		self._attached = True
		self._anchor_widget = None							# type: QWidget
		self._tree_model = DirectoryPopup.FolderTreeModel(browser_preference, root=None, parent=self)

		self._init_ui()

	@property
	def anchor_widget(self) -> QWidget:
		return self._anchor_widget

	@anchor_widget.setter
	def anchor_widget(self, value: QWidget):
		self._anchor_widget = value

	@property
	def browser_preference(self) -> BrowserPreference:
		return self._browser_preference

	@browser_preference.setter
	def browser_preference(self, value: BrowserPreference):
		self._browser_preference = value
		self._tree_model.browser_preference = value

	# @override(check_signature=False)
	# def show(self, move: QPoint | None = None) -> None:

	@override
	def _setup_frameless_layout(self):
		super()._setup_frameless_layout()

		self.set_title_style('POPUP')
		self._title_bar.set_title_align(Qt.AlignLeft)

	def set_active_items(self, directories: List[path.DirectoryPath], categories):
		"""
		Set the active items within the tree view.

		:param List[path.DirectoryPath] directories: list of directories.
		:param List[str] categories: list of category ids.
		"""

		model = self._tree_view.model
		with contexts.block_signals(self._tree_view):
			proxy_model = self._tree_view.proxy_search
			selection_model = self._tree_view.selection_model()
			selection_model.clear()
			selected_indexes = []
			for item in directories:
				matched_items = proxy_model.match(
					model.index(0, 0), model_consts.uidRole + 1, item, hits=1, flags=Qt.MatchRecursive)
				selected_indexes.extend(matched_items)
			for selected in selected_indexes:
				pass

	def reset(self):
		"""
		Reset directory popup window contents.
		"""

		self._tree_model.refresh()
		self._tree_view.expand_all()

	def _init_ui(self):
		"""
		Internal function that setups UI.
		"""

		self._tree_view = treeviews.ExtendedTreeView(parent=self)
		self._tree_view.set_searchable(False)
		self._tree_view.set_toolbar_visible(False)
		self._tree_view.set_show_title_label(False)
		self._tree_view.tree_view.setHeaderHidden(True)
		self._tree_view.set_alternating_color_enabled(False)
		self._tree_view.tree_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		self._tree_view.tree_view.setIndentation(dpi.dpi_scale(10))
		self._tree_view.set_drag_drop_mode(QAbstractItemView.InternalMove)
		delegate = delegates.HtmlDelegate(parent=self._tree_view)
		self._tree_view.tree_view.setItemDelegateForColumn(0, delegate)
		self._tree_view.set_model(self._tree_model)

		main_layout = layouts.vertical_layout()
		self.set_main_layout(main_layout)
		header_layout = layouts.horizontal_layout(spacing=6, margins=(0, 2, 5, 2))
		self._title_bar.corner_contents_layout.addLayout(header_layout)

		icon_size = 13
		self._add_directory_button = buttons.BaseButton(parent=self)
		self._add_directory_button.set_icon('plus', size=icon_size)
		self._add_directory_button.setIconSize(QSize(icon_size, icon_size))
		self._add_directory_button.setFixedSize(QSize(icon_size, icon_size))
		self._remove_directory_button = buttons.BaseButton(parent=self)
		self._remove_directory_button.set_icon('minus', size=icon_size)
		self._remove_directory_button.setIconSize(QSize(icon_size, icon_size))
		self._remove_directory_button.setFixedSize(QSize(icon_size, icon_size))
		self._dots_menu_button = buttons.BaseButton(parent=self)
		self._dots_menu_button.set_icon('menu_dots', size=icon_size)
		self._dots_menu_button.setIconSize(QSize(icon_size, icon_size))
		self._dots_menu_button.setFixedSize(QSize(icon_size, icon_size))
		self._dots_menu_button.hide()
		self._close_button = buttons.BaseButton(icon='close', parent=self)
		self._close_button.setFixedSize(QSize(10, 10))
		self._title_bar.window_buttons_layout.addWidget(self._add_directory_button)
		self._title_bar.window_buttons_layout.addWidget(self._remove_directory_button)
		self._title_bar.window_buttons_layout.addWidget(self._dots_menu_button)
		self._title_bar.window_buttons_layout.addWidget(self._close_button)

		main_layout.addWidget(self._tree_view)

		self._add_directory_button.addAction(
			'Add Folder Alias from Disk', mouse_menu=Qt.LeftButton, action_icon=resources.icon('folder'),
			connect=self._on_add_folder_alias_action_triggered)
		self._add_directory_button.addAction(
			'Add Category (Empty Container)', mouse_menu=Qt.LeftButton, action_icon=resources.icon('sort_down'),
			connect=self._on_add_category_action_triggered)

		self._tree_view.selectionChanged.connect(self._on_tree_view_selection_changed)
		self._close_button.leftClicked.connect(self.close)

	def _on_add_folder_alias_action_triggered(self):
		"""
		Internal callback function that is called each time Add Folder Alias action is triggered by the user.
		Creates a new folder alias.
		"""

		print('Adding new folder alias')

	def _on_add_category_action_triggered(self):
		"""
		Internal callback function that is called each time Add Category action is triggered by the user.
		Creates a new category.
		"""

		with contexts.block_signals(self._tree_view):
			selected_items = self._tree_view.selected_items()
			parent = selected_items[0].parent_source() if selected_items else self._tree_model.root
			text = popups.input_dialog(
				title='Category Name', text='', message='Please enter name for the new category.', parent=self)
			if text:
				data = {'alias': text}
				parent_index = parent.model_index()
				inserted = self._tree_model.insertRow(parent.row_count(), parent=parent_index, data=data, item_type='category')
				if not inserted:
					return
				new_parent = parent.children[-1]
				new_parent_index = new_parent.model_index()
				for item in selected_items:
					parent_source = item.parent_source()
					self._tree_model.moveRows(parent_source.model_index(), item.index(), 1, new_parent_index, 0)
				self._tree_view.expand_all()

		self.reset()

	def _on_tree_view_selection_changed(self):
		"""
		Internal callback function that is called each time tree view selection changes.
		"""

		print('tree view selection changed...')


class MultipleFilterProxyModel(QSortFilterProxyModel):

	@override
	def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:

		filter_reg_exp = self.filterRegExp()
		if filter_reg_exp.isEmpty():
			return True

		requested_role = self.filterRole()
		consolidated_data = ''
		source_model = self.sourceModel()
		row_index = source_model.index(source_row, 0)
		if requested_role == ModelRoles.FILENAME:
			data = source_model.data(row_index, ModelRoles.TAG)
			consolidated_data += str(data)
		for role in (
				Qt.DisplayRole, ModelRoles.TAG, ModelRoles.DESCRIPTION, ModelRoles.FILENAME,
				ModelRoles.WEBSITES, ModelRoles.CREATOR):
			if requested_role == role:
				data = source_model.data(row_index, role)
				consolidated_data += str(data)

		return filter_reg_exp.indexIn(consolidated_data) != -1


class ThumbnailDelegate(QStyledItemDelegate):

	@override
	def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
		source_index, data_model = utils.data_model_index_from_index(index)
		item = data_model.item_from_index(source_index)
		if not item:
			return

		return item.sizeHint()

	def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
		source_index, data_model = utils.data_model_index_from_index(index)
		item = data_model.item_from_index(source_index)
		if not item:
			return

		item.paint(painter, option, index)


class ItemModel(QStandardItemModel):

	CHUNK_COUNT = 20			# total number of items to load a time


class FileModel(ItemModel):

	refreshRequested = Signal()
	doubleClicked = Signal(str)
	parentClosed = Signal(bool)
	itemSelectionChanged = Signal(str, object)

	def __init__(
			self, view: ThumbsListView, extensions: List[str], directories: List[path.DirectoryPath] | None = None,
			active_directories: List[str | path.DirectoryPath] | None = None, uniform_icons: bool = False,
			chunk_count: int = 0, include_sub_dirs: bool = False):
		super().__init__(parent=view)

		self._view = view
		self._extensions = extensions
		self._directories = directories
		self._uniform_icons = uniform_icons
		self._chunk_count = chunk_count or ItemModel.CHUNK_COUNT
		self._include_sub_dirs = include_sub_dirs
		self._active_directories = None									# type: List[path.DirectoryPath]
		self._current_image = None
		self._current_item = None
		self._file_items = []
		self._theme_prefs = core.theme_preference_interface()
		self._thread_pool = QThreadPool.globalInstance()
		self._loaded_count = 0

		if directories is not None:
			self.set_directories(directories, refresh=False)

		self.set_active_directories(active_directories, refresh=False)

	@property
	def active_directories(self) -> List[path.DirectoryPath]:
		if self._active_directories is None:
			self._active_directories = self._directories

		return self._active_directories or []

	@override
	def clear(self) -> None:

		self._thread_pool.clear()
		while not self._thread_pool.waitForDone():
			continue
		self._loaded_count = 0

		super().clear()

	def set_directories(self, directories: List[path.DirectoryPath], refresh: bool = True):
		"""
		Sets the directories where files should be searched from.
		
		:param List[path.DirectoryPath] directories: file directories. 
		:param bool refresh: whether to update model data after setting directories. 
		"""

		self._directories = helpers.force_list(directories)

		if refresh:
			self.refresh_list()

	def set_active_directories(self, directories: List[path.DirectoryPath], refresh: bool = True):
		"""
		Sets the active directories where files should be searched from.

		:param List[path.DirectoryPath] directories: active file directories.
		:param bool refresh: whether to update model data after setting directories.
		"""

		self._active_directories = helpers.force_list(directories)

		if refresh:
			self.refresh_list()

	def refresh_list(self):
		"""
		Refreshes the icon list if contents have been modified.
		"""

		self.clear()
		self._refresh_model_data()

	def _refresh_model_data(self):
		"""
		Internal function that refreshes models data.
		"""

		self.refreshRequested.emit()


class ThumbsBrowserFileModel(FileModel):

	def __init__(
			self, view: ThumbsListView, extensions: List[str], directories: List[path.DirectoryPath] | None = None,
			active_directories: List[str | path.DirectoryPath] | None = None, uniform_icons: bool = False,
			chunk_count: int = 0, include_sub_dirs: bool = False, browser_preferences: BrowserPreference | None = None):

		self._browser_preferences = browser_preferences

		super().__init__(
			view=view, extensions=extensions, directories=directories, active_directories=active_directories,
			uniform_icons=uniform_icons, chunk_count=chunk_count, include_sub_dirs=include_sub_dirs)

	def preference(self) -> BrowserPreference:
		"""
		Returns browser preference instance.

		:return: browser preference.
		:rtype: BrowserPreference
		"""

		return self._browser_preferences

	def set_uniform_item_sizes(self, flag: bool):
		"""
		Sets whether item sizes should be uniform.

		:param bool flag: True to make sure items are square; False to make images to keep its original aspect ratio.
		"""

		self._uniform_icons = flag
		for row in range(self.rowCount()):
			item = self.itemFromIndex(self.index(row, 0))
			item.square_icon = flag

	def refresh_asset_folders(self):
		"""
		Retrieves folder in assets folder in preferences and set/save the settings.
		"""

		if not self._browser_preferences:
			return

		self._browser_preferences.refresh_asset_folders(set_active=True)

	def update_from_prefs(self, update_items: bool = True):
		"""
		Retrieves updated preference information and updates the model's items.

		:param bool update_items: whether to update model's items.
		"""

		if not self._browser_preferences:
			return

		self._directories = self._browser_preferences.browser_folder_paths()
		old_actives = self._active_directories
		self._active_directories = self._browser_preferences.active_browser_paths()

		if update_items and not set([path.normalize_path(a.path) for a in old_actives]) == set([path.normalize_path(a.path) for a in self._active_directories]):
			self._update_items()

	def _update_items(self):
		"""
		Internal function that updates and adds items to the internal list of items.
		This list is the one that is used to fill the view.
		"""

		print('Updating items ...')


class SuffixFilterModel(ThumbsBrowserFileModel):

	pass


class MayaFileModel(SuffixFilterModel):

	def __init__(
			self, view: ThumbsListView, directories: List[path.DirectoryPath] | None = None,
			uniform_icons: bool = False, chunk_count: int = 0, browser_preferences: BrowserPreference | None = None):

		extensions = ['ma', 'mb']
		super().__init__(
			view=view, extensions=extensions, directories=directories, uniform_icons=uniform_icons,
			chunk_count=chunk_count, include_sub_dirs=True, browser_preferences=browser_preferences)
