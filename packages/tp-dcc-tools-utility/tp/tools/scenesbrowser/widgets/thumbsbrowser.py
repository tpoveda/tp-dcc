from __future__ import annotations

import os
import math
import time
import random
import typing
from functools import partial
from typing import Tuple, List, Dict, Type, Iterator, Union, Any

from overrides import override
from Qt import QtCompat
from Qt.QtCore import (
    Qt, QObject, Signal, QPoint, QRect, QSize, QModelIndex, QThreadPool, QSortFilterProxyModel, QItemSelectionModel,
    QTimer, QRegExp
)
from Qt.QtWidgets import (
    QSizePolicy, QWidget, QHBoxLayout, QListView, QStyle, QStyledItemDelegate, QStyleOptionViewItem, QAction,
    QAbstractItemView
)
from Qt.QtGui import (
    QColor, QIcon, QPixmap, QImage, QFont, QFontMetricsF, QPainter, QBrush, QPen, QStandardItemModel, QStandardItem,
    QResizeEvent, QMouseEvent, QWheelEvent, QKeyEvent
)

from tp.core import log, scenefiles
from tp.preferences.interfaces import core
from tp.common.python import osplatform, helpers, path
from tp.common.qt import consts, dpi, qtutils, contexts
from tp.common.qt.widgets import layouts, buttons, frameless, treeviews, popups, search, windows
from tp.common.qt.models import utils, datasources, treemodel, delegates, consts as model_consts
from tp.common.resources import icon, api as resources

if typing.TYPE_CHECKING:
    from tp.preferences.assets import BrowserPreference
    from tp.tools.toolbox.widgets.toolui import ToolUiWidget

IMAGE_EXTENSIONS = consts.QT_SUPPORTED_EXTENSIONS

logger = log.tpLogger


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
    requestDoubleClick = Signal(QModelIndex, object)
    requestSelectionChanged = Signal(QModelIndex, object)

    _DEFAULT_ICON_SIZE = QSize(256, 256)
    _DEFAULT_COLUMN_COUNT = 4
    _MAX_THREAD_COUNT = 200
    _DEFAULT_MIN_ICON_SIZE = 20
    _DEFAULT_MAX_ICON_SIZE = 512

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

    @property
    def thread_pool(self) -> QThreadPool:
        return self._thread_pool

    @override(check_signature=False)
    def setModel(self, model: ThumbsBrowserFileModel) -> None:
        self._proxy_filter_model.setSourceModel(model)
        model.set_uniform_item_sizes(self._uniform_icons)
        result = super().setModel(self._proxy_filter_model)
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)

        return result

    @override
    def setIconSize(self, size: QSize) -> None:
        self._current_icon_size = size
        super().setIconSize(size)

    @override
    def resizeEvent(self, e: QResizeEvent) -> None:
        super().resizeEvent(e)
        icon_size = self.iconSize()
        self._column_count = math.floor(self.size().width() / icon_size.width())

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.LeftButton:
            return

        index, data_model = utils.data_model_index_from_index(self.currentIndex())
        if data_model is not None:
            item = data_model.itemFromIndex(index)			# type: TreeItem
            data_model.double_click_event(index, item)
            self.requestDoubleClick.emit(index, item)
            event.accept()

    @override
    def wheelEvent(self, e: QWheelEvent) -> None:
        modifiers = e.modifiers()
        if not self._zoomable or modifiers != Qt.ControlModifier:
            super().wheelEvent(e)
            return

        indices = self.selectedIndexes()
        index = None
        if indices:
            index = indices[0]
            viewport_rect = self.viewport().rect()
            if not viewport_rect.intersects(self.visualRect(index)):
                index = None
        if index is None:
            event_pos = e.pos()
            index = self.indexAt(event_pos)
            if not index.isValid():
                _index = self.closest_index(event_pos)
                if _index is not None:
                    index = _index

        delta = e.angleDelta().y() / 8
        self._set_zoom_amount(delta)
        self.scrollTo(index)
        e.accept()
        self.stateChanged.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_F and not event.modifiers():
            if self.underMouse():
                selection = self.selectedIndexes()
                if selection:
                    self.scrollTo(selection[0])
                    event.accept()
                    return

        super().keyPressEvent(event)

    def refresh(self):
        """
        Refreshes icons.
        """

        proxy_model = self.model()
        if proxy_model:
            proxy_model.layoutChanged.emit()
        self._update_image_size_for_column_count(self._column_count)
        if not self.updatesEnabled():
            self.setUpdatesEnabled(True)

    def root_model(self) -> ThumbsBrowserFileModel:
        """
        Returns root source model instance.

        :return: root source model.
        :rtype: ThumbsBrowserFileModel
        """

        return utils.data_model_from_proxy_model(self.model())

    def current_index_int(self) -> int:
        """
        Returns the current index of the selected item.

        :return: selected item index.
        :rtype: int
        """

        return self.currentIndex().row()

    def set_current_index_int(self, index: int, scroll_to: bool = False):
        """
        Selects item with given index.

        :param int index: item index.
        :param bool scroll_to: whether to automatically scroll to selected item.
        """

        data_model = self.root_model()
        if not data_model:
            return

        auto_scroll = self.hasAutoScroll()
        self.setAutoScroll(scroll_to)
        self.selectionModel().setCurrentIndex(data_model.index(index, 0), QItemSelectionModel.ClearAndSelect)
        self.setAutoScroll(auto_scroll)

    def closest_index(self, pos: QPoint) -> QModelIndex | None:
        """
        Returns the closes model index based on given position.

        :param QPoint pos: position.
        :return: closes model to given position.
        :rtype: QModelIndex or None
        """

        max_dist = -1
        closest_index = None
        for index in self.iterate_visible_indices():
            rect = self.visualRect(index)
            if rect.top() <= pos.y() <= rect.bottom():		# only items from the same row
                dist = pos.x() - rect.center().x()
                if max_dist == -1 or dist < max_dist:
                    closest_index = index
                    max_dist = dist

        return closest_index

    def iterate_visible_indices(self, pre: int = 0, post: int = 0) -> Iterator[QModelIndex] | None:
        """
        Generator function that iterates over all visible indices.

        :param int pre: extra items to add behind the currently visible items.
        :param int post: extra items to add after the currently visible items.
        :return: list of valid indices that are visible plus the pre and post ones.
        :rtype: List[QModelIndex] or None
        """

        viewport_rect = self.viewport().rect()
        if viewport_rect.width() == 0 or viewport_rect.height() == 0:
            return None

        proxy_model = self.model()
        if not proxy_model:
            return None

        proxy_start_index = self.indexAt(QPoint())
        if not proxy_start_index.isValid():
            return None

        start_row = proxy_start_index.row()
        if start_row > 0:
            proxy_start_index = proxy_model.index(0, 0)
        elif pre:
            for i in range(start_row - pre, start_row - 2):
                proxy_index = proxy_model.index(i, 0)
                if not proxy_index.isValid():
                    break
                yield proxy_index

        yield proxy_start_index

        end_index = proxy_start_index
        while True:
            sibling = end_index.sibling(end_index.row() + 1, 0)
            if not sibling.isValid():
                break
            if not viewport_rect.intersects(self.visualRect(sibling)):
                break
            end_index = sibling
            yield end_index

        if post:
            for i in range(end_index.row() + post, end_index.row() - 1):
                proxy_index = proxy_model.index(i, 0)
                if not proxy_index.isValid():
                    break
                yield proxy_index

    def iterate_visible_items(self, pre: int = 0, post: int = 0) -> Iterator[TreeItem]:
        """
        Generator function that iterates over all visible items.

        :param int pre: extra items to add behind the currently visible items.
        :param int post: extra items to add after the currently visible items.
        :return: list of valid indices that are visible plus the pre and post ones.
        :rtype: Iterator[TreeItem]
        """

        for visible_index in self.iterate_visible_indices(pre, post):
            index, data_model = utils.data_model_index_from_index(visible_index)
            yield data_model.itemFromIndex(index)

    def set_columns(self, columns: int, refresh: bool = False):
        """
        Sets the number of columns for the thumbs view.

        :param int columns: columns to set.
        :param bool refresh: whether to refresh view.
        """

        self._column_count = columns
        if refresh:
            self._update_image_size_for_column_count(columns)

    def state(self) -> Dict:
        """
        Returns settings from the list view.

        :return: list view settings.
        :rtype: Dict
        """

        return {
            'sliderPos': self.verticalScrollBar().value(),
            'sliderMin': self.verticalScrollBar().minimum(),
            'sliderMax': self.verticalScrollBar().maximum(),
            'selected': self.current_index_int(),
            'columns': self._DEFAULT_COLUMN_COUNT,
            'iconSize': self._current_icon_size,
            'initialIconSize': self._DEFAULT_ICON_SIZE,
            'fixedSize': self.parentWidget().minimumSize()
        }

    def set_state(self, state: Dict, scroll_to: bool = False):
        """
        Updates list view with given state data and optionally scroll to item.

        :param Dict state: state to load list view from.
        :param bool scroll_to: whether to scroll to item.
        """

        self._DEFAULT_COLUMN_COUNT = state['columns']
        self._current_icon_size = state['iconSize']
        self._DEFAULT_ICON_SIZE = state['initialIconSize']
        fixed_size = state['fixedSize']
        if fixed_size.width() != 0:
            self.parentWidget().setFixedWidth(fixed_size.width())
        if fixed_size.height() != 0:
            self.parentWidget().setFixedHeight(fixed_size.height())
        vertical_scroll_bar = self.verticalScrollBar()
        vertical_scroll_bar.setMinimum(state['sliderMin'])
        vertical_scroll_bar.setMaximum(state['sliderMax'])
        vertical_scroll_bar.setValue(state['sliderPos'])
        if not self.isVisible():
            return
        if state['selected'] != -1:
            QTimer.singleShot(0, lambda: self.set_current_index_int(state['selected'], scroll_to))

    def filter(self, text: str, tag: str | None = None):
        """
        Function that filters current thumb items based on given text and tags.

        :param str text: filter search text.
        :param str or None tag: optional filter search tag.
        """

        tag = tag or 'filename'
        if helpers.is_string(tag):
            tag = [tag]
        fixed_filter_text, fixed_filter_tags = self._persistent_filter or ['', []]
        tags = set(tag)
        if fixed_filter_text:
            tags.update(fixed_filter_tags)
            text = ''.join([f'(?=.*{text})'] + [f'(?=.*{fixed_filter_text})'])
        role = Qt.DisplayRole
        for t in tag:
            tag_role = ModelRoles.TAG_TO_ROLE.get(t)
            if tag_role is not None:
                role = role | tag_role

        self._proxy_filter_model.setFilterRole(role)
        self._proxy_filter_model.setFilterRegExp(QRegExp(text, Qt.CaseInsensitive, QRegExp.RegExp))

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
        self.clicked.connect(lambda: self.stateChanged.emit())
        self.activated.connect(lambda: self.stateChanged.emit())
        self.entered.connect(lambda: self.stateChanged.emit())

    def _set_zoom_amount(self, value: int):
        """
        Internal function that sets the internal thumb view zoom amount.

        :param int value: zoom amount.
        """

        column_count = self._column_count
        if value > 0:
            _column_count = column_count + 1
        else:
            _column_count = column_count - 1
        if _column_count <= 0:
            return

        self._update_image_size_for_column_count(_column_count)

    def _update_image_size_for_column_count(self, column_count: int):
        """
        Internal function that updates image size based on the given column count.

        :param int column_count: column count.
        """

        view_size = self.size()
        view_width = view_size.width() - self.verticalScrollBar().size().width() - 2
        image_width = int(view_width / column_count)
        if image_width >= self._DEFAULT_MAX_ICON_SIZE or image_width <= self._DEFAULT_MIN_ICON_SIZE:
            return
        self._column_count = column_count
        self.setIconSize(QSize(image_width, image_width))
        self._pagination_load_next_items()

    def _pagination_load_next_items(self):
        """
        Internal function that call models loadData method so images can be loaded when the vertical slider hits its
        max value.
        """

        if not self._pagination:
            return

        current_model = self.root_model()
        if current_model is None:
            return

        items_to_load = []
        vis = list(self.iterate_visible_items(current_model.chunk_count, current_model.chunk_count))
        for visible_item in vis:
            internal_item = visible_item.item
            if internal_item.icon_loaded() and not visible_item.pixmap().isNull():
                continue
            thread = internal_item.icon_thread
            if thread is None:
                items_to_load.append(visible_item)
            elif not thread.isRunning():
                items_to_load.append(visible_item)

        if items_to_load:
            current_model.load_items(items_to_load)

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

        index = self.currentIndex()
        data_model_index, data_model = utils.data_model_index_from_index(index)
        if not data_model_index.isValid():
            return

        item = data_model.itemFromIndex(data_model_index)
        data_model.selection_changed_event(data_model_index, item)
        self.requestSelectionChanged.emit(data_model_index, item)


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
    uniformIconAction = Signal(QAction)
    snapshotAction = Signal()
    snapshotNewAction = Signal()
    createThumbnailAction = Signal()
    newFromClipboardAction = Signal()
    selectDirectoriesAction = Signal()

    APPLY_ACTION = 0
    CREATE_ACTION = 1
    RENAME_ACTION = 2
    DELETE_ACTION = 3
    BROWSE_ACTION = 4
    SET_DIRECTORY_ACTION = 5
    REFRESH_ACTION = 6
    UNIFORM_ICON_ACTION = 7
    SNAPSHOT_ACTION = 8
    SNAPSHOT_NEW_ACTION = 9
    CREATE_THUMBNAIL_ACTION = 10
    NEW_FROM_CLIPBOARD_ACTION = 11
    DIRECTORY_POPUP_ACTION = 12

    def __init__(
            self, uniform_icons: bool = True, item_name: str = '', apply_text: str = 'Apply',
            apply_icon: str = 'checkmark', create_text: str = 'New', new_active: bool = True, rename_active: bool = True,
            delete_active: bool = True, snapshot_active: bool = False, create_thumbnail_active: bool = False,
            new_clipboard_active: bool = False, parent: ThumbsBrowser | None = None):

        self._uniform_icons = uniform_icons
        self._dots_menu_name = item_name
        self._apply_text = apply_text
        self._apply_icon = apply_icon
        self._create_text = create_text
        self._menu_actions = {}  # type: Dict[str or int, QAction]

        super().__init__(parent=parent)

        self.set_create_active(new_active)
        self.set_rename_active(rename_active)
        self.set_delete_active(delete_active)
        self.set_snapshot_active(snapshot_active)
        self.set_from_snapshot_active(new_clipboard_active)
        self.set_from_clipboard_active(new_clipboard_active)
        self.set_create_thumbnail_active(create_thumbnail_active)

    @override
    def setup_ui(self):
        super().setup_ui()

        self.set_icon(self.MENU_ICON)
        self.setToolTip(f'File menu. Manage {self._dots_menu_name}')
        self.menu_align = Qt.AlignRight

        file_browser = 'Finder' if osplatform.is_mac() else 'Explorer'

        apply_icon = resources.icon(self._apply_icon)
        save_icon = resources.icon('save')
        rename_icon = resources.icon('rename')
        delete_icon = resources.icon('trash')
        add_folder_icon = resources.icon('add_folder')
        browse_icon = resources.icon('folder')
        refresh_icon = resources.icon('refresh')
        snapshot_icon = resources.icon('camera')

        new_actions = [
            ('DoubleClick', (f'{self._apply_text} (Double Click)', self.applyAction.emit, apply_icon, False)),
            (DotsMenu.CREATE_ACTION, (f'{self._create_text} {self._dots_menu_name}', self.createAction.emit, save_icon, False)),
            (DotsMenu.RENAME_ACTION, (f'Rename {self._dots_menu_name}', self.renameAction.emit, rename_icon, False)),
            (DotsMenu.DELETE_ACTION, (f'Delete {self._dots_menu_name}', self.deleteAction.emit, delete_icon, False)),
            ('---', None),
            (DotsMenu.SET_DIRECTORY_ACTION, (f'Set {self._dots_menu_name} Dir', self.setDirectoryAction.emit, add_folder_icon, False)),
            (DotsMenu.DIRECTORY_POPUP_ACTION, ('Select Directories...', self.selectDirectoriesAction.emit, add_folder_icon, False)),
            (DotsMenu.BROWSE_ACTION, (f'Open in {file_browser}...', self.browseAction.emit, browse_icon, False)),
            (DotsMenu.REFRESH_ACTION, ('Refresh Thumbnails', self.refreshAction.emit, refresh_icon, False)),
            ('---', None),
            (DotsMenu.UNIFORM_ICON_ACTION, ('Square Icons', self._on_uniform_action_clicked, None, True)),
            (DotsMenu.SNAPSHOT_NEW_ACTION, ('Snapshot New', self._on_new_item_snapshot_menu_clicked, snapshot_icon, False)),
            (DotsMenu.SNAPSHOT_ACTION, ('Replace Image (Please select an item)', self._on_snapshot_menu_clicked, snapshot_icon, False)),
            (DotsMenu.NEW_FROM_CLIPBOARD_ACTION, ('Paste from Clipboard', self._on_snapshot_menu_clicked, snapshot_icon, False)),
            (DotsMenu.CREATE_THUMBNAIL_ACTION, ('New Thumbnail', self.createThumbnailAction.emit, apply_icon, False)),
        ]
        for key, value in new_actions:
            if value is None and key == '---':
                self.add_separator()
            else:
                text, connect, icon, checkable = value
                self._menu_actions[key] = self.addAction(text, connect=connect, action_icon=icon, checkable=checkable)

        self._menu_actions[DotsMenu.SNAPSHOT_ACTION].setEnabled(False)
        self._menu_actions[DotsMenu.UNIFORM_ICON_ACTION].setChecked(self._uniform_icons)
        self._menu_actions[DotsMenu.DIRECTORY_POPUP_ACTION].setVisible(False)

    def set_action_active(self, action_id: int, active: bool):
        """
        Sets whether action with given id is active.

        :param int action_id: id of the action to active/deactivate.
        :param bool active: True to activate the action; False to deactivate it.
        """

        if action_id not in self._menu_actions:
            return

        self._menu_actions[action_id].setVisible(active)

    def set_create_active(self, active: bool):
        """
        Sets whether set create action is active.

        :param bool active: True to enable create action; False to disable it.
        """

        self.set_action_active(DotsMenu.CREATE_ACTION, active)

    def set_rename_active(self, active: bool):
        """
        Sets whether rename action is active.

        :param bool active: True to enable rename action; False to disable it.
        """

        self.set_action_active(DotsMenu.RENAME_ACTION, active)

    def set_delete_active(self, active: bool):
        """
        Sets whether delete action is active.

        :param bool active: True to enable delete action; False to disable it.
        """

        self.set_action_active(DotsMenu.DELETE_ACTION, active)

    def set_snapshot_active(self, active: bool):
        """
        Sets whether snapshot action is active.

        :param bool active: True to enable snapshot action; False to disable it.
        """

        self.set_action_active(DotsMenu.SNAPSHOT_ACTION, active)
        parent = self.parent()				# type: ThumbsBrowser
        if not parent.snapshot_window:
            parent.new_snapshot_window()

    def set_snapshot_enabled(self, flag: bool):
        """
        Sets whether snapshot action is enabled.

        :param bool flag: True to enable snapshot action; False to disable it.
        """

        snapshot_action = self._menu_actions[DotsMenu.SNAPSHOT_ACTION]
        snapshot_action.setEnabled(flag)
        if snapshot_action.isEnabled():
            snapshot_action.setText('Snapshot Replace')
        else:
            snapshot_action.setText('Snapshot Replace (Please select an item)')

    def set_from_snapshot_active(self, active: bool):
        """
        Sets whether set from snapshot action is active.

        :param bool active: True to enable set from snapshot action; False to disable it.
        """

        self.set_action_active(DotsMenu.SNAPSHOT_NEW_ACTION, active)

    def set_from_clipboard_active(self, active: bool):
        """
        Sets whether set from clipboard action is active.

        :param bool active: True to enable set from clipboard action; False to disable it.
        """

        self.set_action_active(DotsMenu.NEW_FROM_CLIPBOARD_ACTION, active)

    def set_create_thumbnail_active(self, active: bool):
        """
        Sets whether create thumbnail action is active.

        :param bool active: True to enable create thumbnail action; False to disable it.
        """

        self.set_action_active(DotsMenu.CREATE_THUMBNAIL_ACTION, active)

    def set_directory_active(self, active: bool):
        """
        Sets whether set directory action is active.

        :param bool active: True to enable set directory action; False to disable it.
        """

        self.set_action_active(DotsMenu.SET_DIRECTORY_ACTION, active)

    def _on_uniform_action_clicked(self, action_clicked: QAction):
        """
        Internal callback function that is called each time uniform action is clicked by the user.

        :param QAction action_clicked: clicked action.
        """

        self._uniform_icons = action_clicked.isChecked()
        self.uniformIconAction.emit(action_clicked)

    def _on_new_item_snapshot_menu_clicked(self):
        """
        Internal callback function that is called each time new snapshot action is clicked by the user.
        """

        parent = self.parent()				# type: ThumbsBrowser
        parent.set_snapshot_type(SnapshotType.NEW)
        parent.snapshot_window.show()

    def _on_snapshot_menu_clicked(self):
        """
        Internal callback function that is called each time edit snapshot action is clicked by the user.
        """

        parent = self.parent()				# type: ThumbsBrowser
        parent.set_snapshot_type(SnapshotType.EDIT)
        parent.snapshot_window.show()


class ThumbsSearchWidget(QWidget):

    searchChanged = Signal(str, object)

    def __init__(self, theme_pref=None, parent: ThumbsBrowser | None = None):
        super().__init__(parent)

        self._theme_pref = theme_pref

        self._main_layout = layouts.horizontal_layout(parent=self)
        self.setLayout(self._main_layout)

        self._filter_menu = buttons.IconMenuButton(
            color=self._theme_pref.ICON_PRIMARY_COLOR, icon='filter', switch_icon_on_click=True, parent=self)
        self._filter_menu.setToolTip('Search filter by meta data')
        self._filter_menu.menu_align = Qt.AlignLeft
        self._filter_menu.addAction('Name And Tags', action_icon=resources.icon('filter'), data=['filename', 'tags'])
        self._filter_menu.addAction('File Name', action_icon=resources.icon('file'), data='filename')
        self._filter_menu.addAction('Description', action_icon=resources.icon('message'), data='description')
        self._filter_menu.addAction('Tags', action_icon=resources.icon('tag'), data='tags')
        self._filter_menu.set_menu_name('Name And Tags')

        self._search_edit = search.SearchLineEdit(parent=self)
        self._search_edit.setPlaceholderText('Search...')

        self._main_layout.addWidget(self._filter_menu)
        self._main_layout.addWidget(self._search_edit)

        self._filter_menu.actionTriggered.connect(self._on_filter_menu_action_triggered)
        self._search_edit.textChanged.connect(self._on_search_edit_text_changed)

        self.setFixedHeight(dpi.dpi_scale(22))

    @property
    def filter_menu(self) -> buttons.IconMenuButton:
        return self._filter_menu

    def _filter_menu_data(self) -> str | List[str]:
        """
        Filter menu data.

        :return: filter data.
        :rtype: str or List[str]
        """

        return self._filter_menu.current_action().data()

    def _on_filter_menu_action_triggered(self, triggered_action: QAction):
        """
        Internal callback function that is called each time a filter action is triggered by the user.

        :param QAction triggered_action: triggered action.
        """

        self.searchChanged.emit(self._search_edit.text(), triggered_action.data())

    def _on_search_edit_text_changed(self, text: str):
        """
        Internal callback function that is called each time search edit texst changes.

        :param str text: current search text.
        """

        self.searchChanged.emit(text, self._filter_menu_data())


class SnapshotWindow(frameless.FramelessWindowThin):
        pass


class InfoEmbedWindow(windows.EmbeddedWindow):
    def __init__(
            self, margins: Tuple[int, int, int, int] = (0, 0, 0, 0), default_visibility: bool = False,
            resize_target: QWidget | None = None, parent: ThumbsBrowser | None = None):

        super().__init__(
            margins=margins, default_visibility=default_visibility, resize_target=resize_target, parent=parent)

    @override
    def _setup_ui(self):
        super()._setup_ui()


class ThumbsBrowser(QWidget):

    _THEME_PREFS = None

    itemSelectionChanged = Signal(str, object)

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
        self._snapshot_type = SnapshotType.EDIT
        self._has_refreshed_view = False
        self._auto_resize_items = True
        self._folder_popup_button = None										# type: buttons.BaseButton
        self._snapshot_window = None											# type: SnapshotWindow
        self._search_widget = None												# type: ThumbsSearchWidget
        self._saved_height = None
        self._previous_save_directories = {'to': None, 'directories': []}

        if snapshot_active:
            self.new_snapshot_window()

        self._setup_ui()

        if not select_directories_active:
            self._folder_popup_button.hide()

        if icon_size is not None:
            self.set_icon_size(icon_size)
        if columns:
            self.set_columns(columns)
        if fixed_height:
            self.setFixedHeight(dpi.dpi_scale(fixed_height), save=True)
        if fixed_width:
            self.setFixedWidth(dpi.dpi_scale(fixed_width))

        self._dots_menu.set_create_active(new_active)
        self._dots_menu.set_snapshot_active(snapshot_active)
        self._dots_menu.set_from_clipboard_active(clipboard_active)
        self._dots_menu.set_from_snapshot_active(snapshot_new_active)
        self._dots_menu.set_create_thumbnail_active(create_thumbnail_active)

        self._setup_signals()

    @property
    def dots_menu(self) -> DotsMenu:
        return self._dots_menu

    @property
    def snapshot_window(self) -> SnapshotWindow:
        return self._snapshot_window

    @property
    def filter_menu(self) -> buttons.IconMenuButton:
        return self._search_widget.filter_menu

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        if self._has_refreshed_view:
            super().resizeEvent(event)
            return

        if self._thumb_widget is not None:
            self._thumb_widget.refresh()
            self._has_refreshed_view = True

        super().resizeEvent(event)

    @override(check_signature=False)
    def setFixedHeight(self, h: int, save: bool = False) -> None:
        super().setFixedHeight(h)
        if save:
            self._saved_height = h

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

    def directories(self) -> List[path.DirectoryPath]:
        """
        Returns list of directory paths.

        :return: directory paths.
        List[path.DirectoryPath]
        """

        return self.model().directories

    def active_directories(self) -> List[path.DirectoryPath]:
        """
        Returns list of active directory paths.

        :return: active directories.
        :rtype: List[path.DirectoryPath]
        """

        return self.model().active_directories

    def save_directory(self) -> str | None:
        """
        Returns the save directory either from user or from preferences.

        :return: save directory.
        :rtype: str or None
        """

        model = self.model()
        dirs = model.active_directories
        dirs = dirs or model.directories
        if not dirs:
            popups.show_warning(title='No directories found', message='No directories found!', button_b=None)
            return None

        if len(dirs) == 1:
            return dirs[0].path

        save_dir = self._display_save_popup()

        return save_dir.path if save_dir else ''

    def icon_size(self) -> QSize:
        """
        Returns thumbs icon size.

        :return: thumbs icon size.
        :rtype: QSize
        """

        return self._thumb_widget.iconSize()

    def set_icon_size(self, size: QSize):
        """
        Sets thumbs icon size.

        :param QSize size: icon size.
        """

        self._thumb_widget.setIconSize(size)

    def set_columns(self, columns: int):
        """
        Sets the number of thumb columns.

        :param int columns: columns count.
        """

        self._thumb_widget.set_columns(columns)

    def set_snapshot_type(self, snap_type: int):
        """
        Sets the type of snapshot for the current browser.

        :param int snap_type: snapshot type.
        """

        self._snapshot_type = snap_type
        if self._snapshot_window:
            if snap_type == SnapshotType.NEW:
                self._snapshot_window.setWindowTitle('Create New Item')
            else:
                self._snapshot_window.setWindowTitle('Edit Thumbnail')

    def new_snapshot_window(self) -> SnapshotWindow:
        """
        Creates a new snapshot UI window instance.

        :return: snapshot UI window instance.
        :rtype: SnapshotWindow
        """

        self._snapshot_window = SnapshotWindow()

        return self._snapshot_window

    def refresh_thumbs(self, scroll_to_item_name: int = -1):
        """
        Refreshes thumbs.

        :param str scroll_to_item_name: optional index of the item to scroll after refreshing.
        """

        if not qtutils.is_widget_visible(self):
            return

        data_model = self.model()
        item_name = data_model.current_item.name if data_model.current_item is not None else ''
        self._thumb_widget.thread_pool.waitForDone()
        self.setUpdatesEnabled(False)
        try:
            state = self._thumb_widget.state()
            data_model.set_uniform_item_sizes(self._uniform_icons)
            data_model.refresh_asset_folders()
            data_model.refresh_list()
            scroll_to = False
            if scroll_to_item_name != -1:
                state['selected'] = data_model.index_from_text(scroll_to_item_name).row()
                scroll_to = True
            else:
                index = data_model.findItems(item_name)
                if index:
                    index = self._thumb_widget.model().mapFromSource(index[0].index())
                    state['selected'] = index.row()
                    scroll_to = True
        finally:
            self.setUpdatesEnabled(True)
        self._refresh_directory_popup()
        self._thumb_widget.set_state(state, scroll_to=scroll_to)

    def filter(self, text: str, tag: str):
        """
        Function that filters current thumb items based on given text and tags.

        :param str text: filter search text.
        :param str tag: filter search tag.
        """

        self._thumb_widget.filter(text, tag)

    def _setup_ui(self):
        """
        Internal function that setups thumbnail browser widgets.
        """

        main_layout = layouts.vertical_layout(margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        self._thumb_widget = ThumbsBrowserListView(
            delegate_class=self._list_delegate_class, uniform_icons=self._uniform_icons, slider=self._virtual_slider,
            slider_args=self._virtual_slider_args, parent=self)
        self._thumb_widget.setSpacing(0)

        self._info_embed_window = InfoEmbedWindow(
            margins=(0, 0, 0, consts.SMALL_PADDING), resize_target=self._thumb_widget, parent=self)

        main_layout.addLayout(self._setup_top_bar())
        main_layout.addWidget(self._info_embed_window)
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
        self._search_widget = ThumbsSearchWidget(theme_pref=ThumbsBrowser._THEME_PREFS, parent=self)
        self._info_button = buttons.styled_button(
            icon='info', style=consts.ButtonStyles.TRANSPARENT_BACKGROUND,
            tooltip='Thumbnail information and add meta data')
        self._dots_menu = DotsMenu(
            uniform_icons=self._uniform_icons, item_name=self._item_name, apply_text=self._apply_text,
            apply_icon=self._apply_icon, create_text=self._create_text, parent=self)

        self._folder_popup_button.leftClicked.connect(self._on_folder_popup_button_left_clicked)
        self._search_widget.searchChanged.connect(self._on_search_changed)
        self._info_button.leftClicked.connect(self._on_info_button_left_clicked)
        self._dots_menu.uniformIconAction.connect(self._on_dots_menu_uniform_icon_action_triggered)

        top_layout.addWidget(self._folder_popup_button)
        top_layout.addWidget(self._search_widget)
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

    def _display_save_popup(
            self, title: str = 'Save Location', message: str = 'Save to Location:', button_a: str = 'Save',
            button_icon_a: str = 'save',
            directories: List[path.DirectoryPath] | None = None) -> path.DirectoryPath | None:
        """
        Internal function that display save popup window.

        :param str title: save popup title.
        :param str message: save popup message.
        :param str button_a: save popup button text.
        :param str button_icon: save popup button ico name.
        :param List[path.DirectoryPath] or None directories: optional list of directories.
        :return: save path.
        :rtype: path.DirectoryPath or None
        """

        directories = directories or self.active_directories() or self.directories()
        paths = [f.alias for f in directories]
        result = popups.show_combo(
            title=title, message=message, items=paths, default_item=0, data=directories, button_a=button_a,
            button_icon_a=button_icon_a)

        return result[2] if result[0] != -1 else None

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

    def _on_directory_popup_selection_changed(self, directories_ids: List[str]):
        """
        Internal callback function that is called each time a directory is selected within directory popup window.

        :param List[str] directories_ids: list of active directories ids.
        :return:
        """

        dirs = self.model().directories
        active = directories_ids
        model = self._thumb_widget.root_model()
        model.set_directories(dirs, refresh=False)
        model.set_active_directories([], refresh=False)
        model.refresh_list()
        self._thumb_widget.refresh()
        if not active:
            return
        self._thumb_widget.set_current_index_int(0)

    def _on_search_changed(self, text: str, tag: str):
        """
        Internal callback function that is called each time search text changes.

        :param str text: current search text.
        :param str tag: current search tag.
        """

        self.filter(text, tag)

    def _on_info_button_left_clicked(self):
        """
        Internal callback function that is called each time info button is left-clicked by the user.
        """

        pass

    def _on_dots_menu_uniform_icon_action_triggered(self):
        """
        Internal callback function that is called each time dots menu uniform icon action is triggered by the user.
        """

        pass

    def _on_model_item_selection_changed(self, name: str, item: FileItem):
        """
        Internal callback function that is called each time model item selection changes.

        :param str name: name of the selected file without extension.
        :param FileItem item: file item instance.
        """

        self._dots_menu.set_snapshot_enabled(True)
        self.itemSelectionChanged.emit(name, item)


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


class CategoryFolderDataSource(datasources.BaseDataSource):
    """
    Category folder within folder tree
    """

    def __init__(
            self, directory_info: Dict, model: FolderTreeModel,
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

    @override
    def custom_roles(self, index: int) -> list[Qt.ItemDataRole]:
        return [model_consts.uidRole + 1]

    @override
    def data_by_role(self, index: int, role: Qt.ItemDataRole) -> Any:
        if role == model_consts.uidRole + 1:
            return self.folder_id()

    @override(check_signature=False)
    def insert_row_data_sources(self, index: int, count: int, items: Dict):
        for item in items:
            data = {}
            if item.get('path'):
                item_type = 'path'
                data['path'] = item['path']
                data['alias'] = item['alias']
            else:
                item_type = 'category'
                data['alias'] = item['alias']
            child_item = self.insert_row_data_source(index, data, item_type)
            children = item.get('children', [])
            if children:
                child_item.insert_row_data_sources(0, len(children), items=children)

        self._model.browser_preference.save_settings()

    @override(check_signature=False)
    def insert_row_data_source(self, index: int, data: Dict, item_type: str) -> datasources.BaseDataSource:
        if item_type == 'category':
            new_item = self._model.browser_preference.create_category(
                category_id=None, name=data['alias'], parent=self.folder_id(), children=data.get('children', []))
            new_item = CategoryFolderDataSource(
                new_item, model=self.model, parent=self)
        else:
            directory_path = path.DirectoryPath(data['path'], alias=data.get('alias'))
            new_item = FolderTreeModel(directory_path, model=self.model, parent=self)
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

    @override
    def supports_drop(self, index: int) -> bool:
        return True

    @override
    def supports_drag(self, index: int) -> bool:
        return True

    def folder_id(self) -> str:
        """
        Returns internal folder id.

        :return: folder id.
        """

        return self._internal_data.get('id', '')


class FolderItemDataSource(CategoryFolderDataSource):
    """
    Folder folder within folder tree
    """

    def __init__(
            self, directory_info: Dict, model: FolderTreeModel,
            parent: datasources.BaseDataSource | None = None):
        super().__init__(directory_info=directory_info, model=model, parent=parent)

        self._icon = resources.icon('folder')

    @override
    def folder_id(self) -> str:
        return self._internal_data.id

    @override
    def data(self, index: int) -> str:
        return self._internal_data.alias

    @override
    def set_data(self, index: int, value: str) -> bool:
        if not value or value == self._internal_data.alias:
            return False
        self._internal_data.alias = value

        return True

    @override
    def supports_drop(self, index: int) -> bool:
        return False

    @override
    def tooltip(self, index: int) -> str:
        return self._internal_data.path


class FolderTreeModel(treemodel.BaseTreeModel):

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
            _root = CategoryFolderDataSource({}, model=self)
            tree = {d.id: FolderItemDataSource(d, model=self) for d in directories}
            for cat in categories:
                tree[cat['id']] = CategoryFolderDataSource(cat, model=self)
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
                if type(item) == FolderItemDataSource:
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
            if type(data_source) == CategoryFolderDataSource:
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


class DirectoryPopup(frameless.FramelessWindow):

    selectionChanged = Signal(list)

    def __init__(
            self, auto_hide: bool = False, attach_to_parent: bool = True,
            browser_preference: BrowserPreference | None = None, parent: ThumbsBrowser | None = None):
        super().__init__(
            title='Directories', width=200, height=400, overlay=False, on_top=False, minimize_enabled=False,
            maximize_button=False, save_window_pref=False, title_bar_class=DirectoryTitleBar, parent=parent)

        self._auto_hide = auto_hide
        self._attach_to_parent = attach_to_parent
        self._browser_preference = browser_preference
        self._browsing = False
        self._attached = True
        self._anchor_widget = None							# type: QWidget
        self._tree_model = FolderTreeModel(browser_preference, root=None, parent=self)

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

    @override(check_signature=False)
    def show(self, reattach: bool = True) -> None:
        if reattach:
            self._attached = True
        width = self.resizer_width()
        new_pos = self.move_attached(offset=(-width, 0))
        super().show(move=new_pos)
        if self._anchor_widget is not None:
            pass

    def move_attached(self, window_pos: QPoint | None = None, offset: Tuple[int, int] = (0, 0)) -> QPoint | None:
        """
        Moves window while attached to window.

        :param QPoint window_pos: parent window position.
        :param Tuple[int, int] offset: offset position.
        :return: new position.
        :rtype: QPoint or None
        """

        anchor_widget = self._anchor_widget
        if anchor_widget is None:
            return
        window_pos = window_pos if window_pos is not None else anchor_widget.mapToGlobal(QPoint(0, 0))
        x_pos = window_pos.x() - self.width() + (self.resizer_width() * 2) + dpi.dpi_scale(4) + dpi.dpi_scale(offset[0])
        pos = QPoint(anchor_widget.mapToGlobal(QPoint(0, dpi.dpi_scale(offset[1]))))
        pos.setX(x_pos)
        new_pos = qtutils.contain_widget_in_screen(self, pos)
        self.move(new_pos)

        return new_pos

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

        def _iterate_proxy_parent_index(model_index: QModelIndex):
            if not model_index.isValid():
                return
            parent_index = model_index.parent()
            yield parent_index
            for i in _iterate_proxy_parent_index(parent_index):
                if i is None:
                    return
                yield i

        model = self._tree_view.model
        with contexts.block_signals(self._tree_view):
            proxy_model = self._tree_view.proxy_search
            selection_model = self._tree_view.selection_model()
            selection_model.clear()
            selected_indexes = []				# type: List[QModelIndex]
            for item in categories:
                matched_items = proxy_model.match(
                    model.index(0, 0), model_consts.uidRole + 1, item, hits=1, flags=Qt.MatchRecursive)
                selected_indexes.extend(matched_items)
            for item in directories:
                matched_items = proxy_model.match(
                    model.index(0, 0), model_consts.uidRole + 1, item.id, hits=1, flags=Qt.MatchRecursive)
                selected_indexes.extend(matched_items)
            for selected in selected_indexes:
                for parent in _iterate_proxy_parent_index(selected):
                    if parent in selected_indexes:
                        break
                else:
                    selection_model.select(selected, QItemSelectionModel.Select)

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

        directories = []
        categories = []

        current_selection = self._tree_view.selected_items()
        for data_source in current_selection:
            if type(data_source) == CategoryFolderDataSource:
                categories.append(data_source.folder_id())
                for child in data_source.iterate_children():
                    if type(child) == FolderItemDataSource:
                        directories.append(child.internal_data)
            else:
                directories.append(data_source.internal_data)

        output_ids = [d.id for d in directories]

        self._browser_preference.set_active_directories(directories)
        self._browser_preference.set_active_categories(categories)

        self.selectionChanged.emit(output_ids)


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
        item = data_model.itemFromIndex(source_index)
        if not item:
            return

        return item.sizeHint()

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        source_index, data_model = utils.data_model_index_from_index(index)
        item = data_model.itemFromIndex(source_index)
        if not item:
            return

        item.paint(painter, option, index)


class ItemModel(QStandardItemModel):

    CHUNK_COUNT = 20			# total number of items to load a time

    @override
    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> Any:
        if not index.isValid():
            return

        item = self.itemFromIndex(index)			# type: TreeItem
        base_item = item.item
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return item.item_text()
        elif role == ModelRoles.FILENAME:
            return base_item.file_name
        elif role == ModelRoles.DESCRIPTION:
            return base_item.description()
        elif role == ModelRoles.TAG:
            return base_item.tags()
        elif role == ModelRoles.WEBSITES:
            return base_item.websites()
        elif role == ModelRoles.CREATOR:
            return base_item.creators()
        elif role == Qt.ToolTipRole:
            return item.toolTip()
        elif role == Qt.DecorationRole:
            return item.icon()

        return super().data(index, role)

    def double_click_event(self, model_index: QModelIndex, item: TreeItem):
        """
        Function that is called when item view is double-clicked by the user.

        :param QModelIndex model_index: model index.
        :param TreeItem item: item view.
        ..note:: it should be overriden in subclasses.
        """

        pass


class FileItem:

    _EMPTY_THUMBNAIL = None				# type: str

    def __init__(
            self, name: str | None = None, description: str | None = None, icon_path: str | None = None,
            file_path: str = '', tooltip: str = '', thumbnail: str = ''):
        super().__init__()

        if FileItem._EMPTY_THUMBNAIL is None:
            FileItem._EMPTY_THUMBNAIL = resources.get('images/empty_thumbnail.png')

        self._icon_path = icon_path or ''
        self._file_path = file_path
        self._description = description or ''
        self._tooltip = tooltip
        self._thumbnail = thumbnail
        self._file_name = ''
        self._extension = ''
        self._image_extension = 'jpg'
        self._directory = ''
        self._metadata = {}
        self._user = ''
        self._icon_thread = None					# type: icon.ThreadedIcon

        self.set_file_path(file_path)

        self._name = name or self._file_name

    @property
    def icon_path(self) -> str:
        return self._icon_path

    @property
    def file_name(self) -> str:
        return self._file_name

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def tooltip(self) -> str:
        return self._tooltip

    @tooltip.setter
    def tooltip(self, value: str):
        self._tooltip = value

    @property
    def name(self) -> str:
        return self._name

    @property
    def directory(self) -> str:
        return self._directory

    @property
    def metadata(self) -> Dict:
        return self._metadata

    @metadata.setter
    def metadata(self, value: Dict):
        self._metadata = value

    @property
    def icon_thread(self) -> icon.ThreadedIcon:
        return self._icon_thread

    @icon_thread.setter
    def icon_thread(self, value: icon.ThreadedIcon):
        self._icon_thread = value

    @property
    def thumbnail_path(self) -> str:
        _thumbnail_path = self._thumbnail_default_path()
        if _thumbnail_path and path.exists(_thumbnail_path):
            self._thumbnail = _thumbnail_path
            return _thumbnail_path

        return self._EMPTY_THUMBNAIL

    @thumbnail_path.setter
    def thumbnail_path(self, value: str):
        self._thumbnail = value
        self._image_extension = self._image_extension if value is None else os.path.splitext(value)[-1][1:].lower()

    def description(self) -> str:
        """
        Returns item description from metadata.

        :return: item description.
        :rtype: str
        """

        return self._metadata.get(scenefiles.INFO_DESCRIPTION, '')

    def creators(self) -> str:
        """
        Returns item creators from metadata.

        :return: item tags.
        :rtype: str
        """

        return self._metadata.get(scenefiles.INFO_CREATORS, '')

    def websites(self) -> str:
        """
        Returns item websites from metadata.

        :return: item tags.
        :rtype: str
        """

        return self._metadata.get(scenefiles.INFO_WEBSITES, '')

    def tags(self) -> str:
        """
        Returns item tags from metadata.

        :return: item tags.
        :rtype: str
        """

        return self._metadata.get(scenefiles.INFO_TAGS, '')

    def has_tag(self, tag: str) -> bool:
        """
        Returns whether given tag exists within tags metadata.

        :param str tag: tag to check.
        :return: True if given tag exists within tags metadata; False otherwise.
        :rtype: bool
        """

        for i in self.tags():
            if tag in i:
                return True

        return False

    def has_any_tags(self, tags: List[str]) -> bool:
        """
        Returns whether any of the given tags exist within tags metadata.

        :param List[str] tags: tags to check.
        :return: True if any of the given tags exist within tags metadata; False otherwise.
        :rtype: bool
        """

        for i in tags:
            if self.has_tag(i):
                return True

        return False

    def thumbnail_exists(self) -> bool:
        """
        Returns whether thumbnail exists for this file item.

        :return: True if thumbnail file exists in disk; False otherwise.
        :rtype: bool
        """

        return path.exists(self._thumbnail)

    def set_file_path(self, file_path: str):
        """

        :param str file_path: sets the path where file data is located.
        """

        self._directory = path.dirname(file_path)
        self._file_path = file_path
        file_name = path.basename(file_path)
        file_split = file_name.split('.')
        self._file_name = file_split[0]
        self._extension = file_split[1]
        if self._extension in IMAGE_EXTENSIONS:
            self._image_extension = self._extension

    def file_name_ext(self) -> str:
        """
        Returns file name with extension.

        :return: file name with extension.
        :rtype :str
        """

        return f'{self._file_name}.{self._extension}'

    def full_path(self) -> str:
        """
        Returns file absolute path.

        :return: file full path.
        :rtype: str
        """

        return path.join_path(self._directory, self.file_name_ext())

    def icon_loaded(self) -> bool:
        """
        Returns whether file icon is already loaded.

        :return: True if file icon is loaded; False otherwise.
        :rtype: bool
        """

        return self._icon_thread is not None and self._icon_thread.is_finished()

    def serialize(self) -> Dict:
        """
        Serializes current item.

        :return: serialized data.
        :rtype: Dict
        """

        return {
            'metadata': {
                'time': '',
                'version': '',
                'user': '',
                'name': self.name,
                'application': {'name': '', 'version': ''},
                'description': '',
                'tags': []
            }
        }

    def _thumbnail_default_path(self) -> str:
        """
        Returns the default path where file thumbnail should be located.

        :return: thumbnail path.
        :rtype: str
        """

        if not self._thumbnail:
            return path.join_path(self._directory, f'{self._file_name}.{self._image_extension}')

        return self._thumbnail


class TreeItem(QStandardItem):

    BACKGROUND_COLOR = QColor(70, 70, 80)
    BACKGROUND_COLOR_HOVER = QColor(50, 180, 150)
    BACKGROUND_COLOR_SELECTED = QColor(50, 180, 240)
    BACKGROUND_COLOR_ICON = QColor(50, 50, 50)
    TEXT_COLOR = QColor(255, 255, 255)
    TEXT_COLOR_SELECTED = QColor(255, 255, 255)
    TEXT_BACKGROUND_COLOR = QColor(0, 0, 0)
    BORDER_COLOR = QColor(0, 0, 0)
    BORDER_COLOR_HOVER = QColor(0, 0, 0)
    BORDER_COLOR_SELECTED = QColor(0, 0, 0)
    BACKGROUND_BRUSH = QBrush(BACKGROUND_COLOR)
    BACKGROUND_COLOR_HOVER_BRUSH = QBrush(BACKGROUND_COLOR_HOVER)
    BACKGROUND_COLOR_SELECTED_BRUSH = QBrush(BACKGROUND_COLOR_SELECTED)
    _HASH = None

    def __init__(
            self, item: FileItem, square_icon: bool = False, theme_pref = None,
            parent: QStandardItem | None = None):
        super().__init__(parent)

        self._item = item
        self._square_icon = square_icon
        self._theme_pref = theme_pref
        self._pixmap = None							# type: QPixmap
        self._current_theme = ''
        self._icon_size = QSize(256, 256)
        self._font = QFont('Tahoma')
        self._padding = 0
        self._text_height = 11
        self._border_width = 1
        self._text_padding_horizontal = 7
        self._text_padding_vertical = 2
        self._show_text = True
        self._aspect_ratio = Qt.KeepAspectRatioByExpanding

        self._generate_hash()

        self.setEditable(False)
        self.set_border_width(1)

        if theme_pref is not None:
            self._init_colors()

    @property
    def item(self) -> FileItem:
        return self._item

    @override
    def sizeHint(self) -> QSize:

        size_hint = self.model().view.icon_size()
        size = min(size_hint.height(), size_hint.width())
        pixmap_size = self._pixmap.rect().size() if self._pixmap else QSize(1, 1)
        aspect_ratio = float(pixmap_size.width()) / float(pixmap_size.height()) if self._square_icon else 1
        size_hint.setWidth(size * aspect_ratio)
        size_hint.setHeight(size + 1)
        if self._show_text:
            size_hint.setHeight(size_hint.height() + self._text_height + self._text_padding_vertical * 2)

        return size_hint

    @override(check_signature=False)
    def font(self, index: QModelIndex) -> QFont:
        return self._font

    @override(check_signature=False)
    def textAlignment(self, index: QModelIndex) -> Union[Qt.Alignment, Qt.AlignmentFlag]:
        return Qt.AlignLeft | Qt.AlignBottom

    @override
    def isEditable(self) -> bool:
        return False

    def item_text(self) -> str:
        """
        Returns item text.

        :return: item text.
        :rtype: str
        """

        return self._item.name

    def pixmap(self) -> QPixmap:
        """
        Returns item pixmap.

        :return: pixmap instance.
        :rtype: QPixmap
        """

        if self._pixmap is None:
            return QPixmap()

        if not self._pixmap.isNull():
            return self._pixmap
        elif not path.exists(self._item.icon_path):
            return QPixmap()

        return self._pixmap

    def set_border_width(self, width: int):
        """
        Sets border with.

        :param int width: border with in pixels.
        """

        self._border_width = dpi.dpi_scale(width)

    def update_theme(self, event=None):
        """
        Updates tree item visuals based on current theme.

        :param event: theme event.
        """

        pass

    def apply_from_image(self, image: QImage):
        """
        Applies given image as the icon for this item.

        :param QImage image: image to set as icon.
        """

        self._pixmap = QPixmap.fromImage(image)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Paints item within view.

        :param QPainter painter: painter instance.
        :param QStyleOptionViewItem option: item style option view.
        :param QModelIndex index: item model index.
        """

        painter.save()

        self._paint_background(painter, option, index)
        if self._show_text:
            self._paint_text(painter, option, index)
        if self._pixmap is not None:
            self._paint_icon(painter, option, index)

        painter.restore()

    def _generate_hash(self):
        """
        Internal function that generates an internal hash number.
        """

        self._HASH = int(time.time() * random.random())

    def _init_colors(self):
        """
        Internal function that initializes tree item colors.
        """

        self.update_theme()

    def _is_selected(self, option: QStyleOptionViewItem) -> bool:
        """
        Internal function that returns whether this item is selected.

        :param QStyleOptionViewItem option: item style option view.
        :return: True if item is selected; False otherwise.
        :rtype: bool
        """

        return option.state & QStyle.State_Selected == QStyle.State_Selected

    def _is_mouse_over(self, option: QStyleOptionViewItem) -> bool:
        """
        Internal function that returns whether mouse cursor is over this item.

        :param QStyleOptionViewItem option: item style option view.
        :return: True if mouse is over this item; False otherwise.
        :rtype: bool
        """

        return option.state & QStyle.State_MouseOver == QStyle.State_MouseOver

    def _icon_rect(self, option: QStyleOptionViewItem) -> QRect:
        """
        Internal function that returns the icon rect.

        :param QStyleOptionViewItem option: item style option view.
        :return: icon rect instance.
        :rtype: QRect
        """

        padding = self._padding
        rect = option.rect
        width = rect.width() - padding
        height = rect.height() - padding
        if self._show_text:
            height -= self._text_height + self._text_padding_vertical
        rect.setWidth(width)
        rect.setHeight(height)
        x = padding + (float(width - rect.width()) * 0.5)
        y = padding + (float(height - rect.height()) * 0.5)
        rect.translate(x, y)

        return rect

    def _icon_alignment(self, index: QModelIndex) -> Qt.Alignment:
        """
        Internal function that returns the alignment for the icon for the given model index.

        :param QModelIndex index: model index.
        :return: alignment.
        :rtype: Qt.Alignment
        """

        return Qt.AlignLeft | Qt.AlignVCenter

    def _paint_background(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Internal function that paints item background.

        :param QPainter painter: painter instance.
        :param QStyleOptionViewItem option: item style option view.
        :param QModelIndex index: item model index.
        """

        is_selected = self._is_selected(option)
        is_mouse_over = self._is_mouse_over(option)
        brush = self.BACKGROUND_BRUSH
        border_color = self.BORDER_COLOR
        if is_selected:
            brush = self.BACKGROUND_COLOR_SELECTED_BRUSH
            border_color = self.BORDER_COLOR_HOVER if is_mouse_over else self.BORDER_COLOR_SELECTED
        elif is_mouse_over:
            brush = self.BACKGROUND_COLOR_HOVER_BRUSH
            border_color = self.BORDER_COLOR_HOVER

        pen = QPen(border_color)
        pen.setJoinStyle(Qt.MiterJoin)
        pen.setWidth(self._border_width)
        painter.setPen(pen)
        rect = QRect(option.rect)
        rect.setWidth(rect.width() - self._border_width)
        rect.setHeight(rect.height() - self._border_width)
        rect.translate(int(self._border_width * 0.5), int(self._border_width * 0.5))
        painter.setBrush(brush)
        painter.drawRect(rect)

        icon_pen = QPen(self.BACKGROUND_COLOR_ICON)
        icon_pen.setWidth(0)
        icon_rect = QRect(rect)
        painter.setBrush(QBrush(self.BACKGROUND_COLOR_ICON))
        icon_rect.setHeight(icon_rect.height() - (self._text_height + self._text_padding_vertical * 2))
        icon_rect.translate(max(1, int(self._border_width * 0.5)), max(1, int(self._border_width * 0.5)))
        icon_rect.setWidth(icon_rect.width() - self._border_width * 2)
        painter.setPen(icon_pen)
        painter.drawRect(icon_rect)

    def _paint_text(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Internal function that paints item text.

        :param QPainter painter: painter instance.
        :param QStyleOptionViewItem option: item style option view.
        :param QModelIndex index: item model index.
        """

        is_selected = self._is_selected(option)
        text = self._item.name
        color = self.TEXT_COLOR_SELECTED if is_selected else self.TEXT_COLOR
        rect = QRect(option.rect)
        width = rect.width() - self._text_padding_horizontal * 2
        height = rect.height()
        padding = self._padding
        x, y = padding, padding
        rect.translate(x + self._text_padding_horizontal, y + self._text_padding_vertical)
        rect.setWidth(width - padding)
        rect.setHeight(height - padding - self._text_padding_vertical)
        font = self.font(index)
        font.setPixelSize(self._text_height)
        align = self.textAlignment(index)
        metrics = QFontMetricsF(font)
        text_width = metrics.width(text)
        if text_width > rect.width() - padding:
            text = metrics.elidedText(text, Qt.ElideRight, rect.width())
        text_background_color = self.BORDER_COLOR_SELECTED if is_selected else self.TEXT_BACKGROUND_COLOR
        text_bg = QRect(option.rect)
        text_bg.setTop(text_bg.top() + text_bg.height() - (self._text_height + self._text_padding_vertical * 2))
        text_bg.translate(max(1, int(self._border_width * 0.5)), max(1, int(self._border_width * 0.5)) - 2)
        text_bg.setWidth(text_bg.width() - self._border_width * 2 - 1)
        text_bg.setHeight(self._text_height + self._text_padding_vertical)
        painter.setBrush(text_background_color)
        painter.setPen(text_background_color)
        painter.drawRect(text_bg)
        pen = QPen(color)
        painter.setPen(pen)
        painter.setFont(font)
        painter.drawText(rect, align, text)

    def _paint_icon(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Internal function that paints item icon.

        :param QPainter painter: painter instance.
        :param QStyleOptionViewItem option: item style option view.
        :param QModelIndex index: item model index.
        """

        rect = self._icon_rect(option)
        pixmap = self.pixmap()
        if pixmap.isNull():
            return

        pixmap = pixmap.scaled(
            rect.width() - self._border_width * 2, rect.height() - self._border_width * 2,
            self._aspect_ratio, Qt.SmoothTransformation)
        pixmap_rect = QRect(rect)
        pixmap_rect.setWidth(pixmap.width())
        pixmap_rect.setHeight(pixmap.height())
        aspect_ratio = float(max(1, pixmap.width())) / float(max(1, pixmap.height()))
        icon_align = self._icon_alignment(index)
        if icon_align & Qt.AlignHCenter == Qt.AlignHCenter:
            x = float(rect.width() - pixmap.width()) * 0.5
        elif icon_align & Qt.AlignLeft == Qt.AlignLeft:
            x = 0
        else:
            x = float(rect.width() - pixmap.width()) * 0.5
            logger.warning('Flags not set for TreeItem._paintIcon()! x-Value!')
        if icon_align & Qt.AlignVCenter == Qt.AlignVCenter:
            y = float(rect.height() - pixmap.height()) * 0.5
        else:
            y = float(rect.height() - pixmap.height()) * 0.5
            logger.warning('Flags not set for TreeItem._paintIcon() y-Value!')
        x += self._border_width
        pixmap_rect.translate(int(x), int(y))

        if self._square_icon:
            clipped_rect = QRect(pixmap_rect)
            clipped_rect.setWidth(clipped_rect.width() - 1)
            if clipped_rect.height() <= clipped_rect.width():						# wide icons
                translate = (clipped_rect.width() - clipped_rect.height()) / 2
                clipped_rect.setWidth(clipped_rect.height() - 1)
                pixmap_rect.translate(int(-translate), 0)
            else:																	# tall icons
                translate = (clipped_rect.height() - clipped_rect.width()) / 2
                clipped_rect.setHeight(clipped_rect.width() + 2)
                clipped_rect.setWidth(clipped_rect.width())
                clipped_rect.translate(0, int(translate))
            painter.setClipRect(clipped_rect)
        else:
            if aspect_ratio > 1:
                pixmap_rect.setWidth(pixmap_rect.width())
            elif aspect_ratio >= 1:
                pixmap_rect.setWidth(pixmap_rect.width() - 1)

        painter.drawPixmap(pixmap_rect, pixmap)


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
        self._current_item = None										# type: FileItem
        self._file_items = []
        self._theme_prefs = core.theme_preference_interface()
        self._thread_pool = QThreadPool.globalInstance()
        self._loaded_count = 0

        if directories is not None:
            self.set_directories(directories, refresh=False)

        self.set_active_directories(active_directories, refresh=False)

    @property
    def view(self) -> ThumbsListView:
        return self._view

    @property
    def directories(self) -> List[path.DirectoryPath]:
        return self._directories

    @property
    def active_directories(self) -> List[path.DirectoryPath]:
        if self._active_directories is None:
            self._active_directories = self._directories

        return self._active_directories or []

    @property
    def chunk_count(self) -> int:
        return self._chunk_count

    @property
    def current_item(self) -> FileItem:
        return self._current_item

    @override
    def clear(self) -> None:

        self._thread_pool.clear()
        while not self._thread_pool.waitForDone():
            continue
        self._loaded_count = 0

        super().clear()

    @override
    def double_click_event(self, model_index: QModelIndex, item: TreeItem):

        self._current_image = item.item.name
        self.doubleClicked.emit(self._current_image)

        return self._current_image

    def selection_changed_event(self, model_index: QModelIndex, item: TreeItem):
        """
        Function that is called when item view is selected.

        :param QModelIndex model_index: model index.
        :param TreeItem item: item view.
        """

        try:
            self._current_item = item.item
            self._current_image = item.item.name
            self.itemSelectionChanged.emit(self._current_image, self._current_item)
            return self._current_image
        except AttributeError:
            pass

    def index_from_text(self, text: str) -> QModelIndex | None:
        """
        Returns model index from given text.

        :param str text: text to find index for.
        :return: model index.
        :rtype: QModelIndex or None
        """

        matched_items = self.findItems(text)
        return matched_items[0] if matched_items else None

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

    def _create_item(self, item: FileItem) -> TreeItem:
        """
        Internal function that creates a tree item and wraps given file item into it.

        :param FileItem item: file item to wrap into a tree item.
        :return: tree item instance.
        :rtype: TreeItem
        """

        tree_item = TreeItem(item=item, theme_pref=self._theme_prefs, square_icon=self._uniform_icons)
        self.appendRow(tree_item)

        return tree_item

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

    @override
    def _refresh_model_data(self):
        self.update_from_prefs(False)
        self._update_items()
        super()._refresh_model_data()

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

    def set_item_icon_from_image(self, item: TreeItem, image: QImage):
        """
        Function that sets item icon from image.

        :param TreeItem item: item to set icon for.
        :param QImage image: image to set as icon.
        """

        item.apply_from_image(image)
        index = item.index()
        QtCompat.dataChanged(self, index, index, [Qt.DecorationRole])

    def load_items(self, items_to_load: List[TreeItem]):
        """
        Loads given tree items.

        :param List[TreeItem] items_to_load: list of items to load.
        """

        threads = []
        for tree_item in items_to_load:
            thread = self._load_item_threaded(tree_item)
            if thread is not None:
                threads.append(thread)
            self._loaded_count += 1

        # once we have all threads that need to run, we run them at the same time
        for thread in threads:
            self._thread_pool.start(thread)

    def _update_items(self):
        """
        Internal function that updates and adds items to the internal list of items.
        This list is the one that is used to fill the view.

        :raises ValueError: if the extension argument does not stores a list of strings.
        """

        if not isinstance(self._extensions, list):
            raise ValueError(
                f'Extension must be a list of strings, such as ["mb", "ma"], "{type(self._extensions)}" type '
                f'given "{self._extensions}"')

        dirs = [d.path for d in list(self._active_directories)]
        if self._include_sub_dirs:
            for d in list(dirs):
                if path.exists(d):
                    dirs += path.directories(d, absolute=True)

        dirs = helpers.uniqify(dirs)
        self._file_items.clear()
        for d in dirs:
            for file in path.files_by_extension(d, self._extensions, sort=True):
                self._create_item_from_file_and_directory(d, file)

    def _generate_item(self, directory: str, file_path: str) -> FileItem:
        """
        Internal function that creates an image item that will be added to the list of file items, which will be showed
        within the UI.

        :param str directory: directory of the image.
        :param str file_path: absolute file path under the directory.
        :return: newly created item.
        :rtype: FileItem
        """

        item = FileItem(file_path=path.join_path(directory, file_path), description=None)
        item.tooltip = item.name

        return item

    def _create_item_from_file_and_directory(
            self, directory: str, file_path: str, load_image: bool = False) -> Tuple[TreeItem, FileItem]:
        """
        Internal function that creates an image item based on the given directory and file path.

        :param str directory: directory of the image.
        :param str file_path: absolute file path under the directory.
        :param bool load_image: If True, the image will be loaded on a separated thread and displayed when ready.
        :return: tuple containing the QItem and the image item.
        :rtype: Tuple[TreeItem, FileItem]
        """

        file_item = self._generate_item(directory, file_path)
        file_item.metadata = scenefiles.info_dictionary(file_item.file_name_ext(), file_item.directory)
        self._file_items.append(file_item)
        q_item = self._create_item(file_item)
        if load_image:
            self._load_item_threaded(q_item, start=True)

        return q_item, file_item

    def _load_item_threaded(self, tree_item: TreeItem, start: bool = False) -> icon.ThreadedIcon | None:
        """
        Internal function that loads given item in a thread.

        :param TreeItem tree_item: tree item to load.
        :param bool start: whether to start loading process.
        :return: icon thread used to load tree item icon.
        :rtype: icon.ThreadedIcon or None
        """

        item = tree_item.item
        thumbnail_path = item.thumbnail_path
        if not os.path.exists(thumbnail_path):
            return None

        worker_thread = icon.ThreadedIcon(icon_path=thumbnail_path)
        worker_thread.signals.updated.connect(partial(self.set_item_icon_from_image, tree_item))
        self.parentClosed.connect(worker_thread.finished)

        item.icon_thread = worker_thread

        if start:
            self._thread_pool.start(item.icon_thread)
            self._loaded_count += 1

        return item.icon_thread


class SuffixFilterModel(ThumbsBrowserFileModel):

    @override
    def _update_items(self):
        super()._update_items()
        for f in self._file_items:
            file_path = path.join_path(f.directory, f.file_name)
            f.thumbnail = self._check_file_image(file_path)

    def _check_file_image(self, file_path: str) -> str:
        """
        Internal function that returns the JPG or PNG that exists within given path.

        :param str file_path: file path with the extension excluded.
        :return: found path.
        :rtype: str
        """

        jpg_path = f'{file_path}.jpg'
        png_path = f'{file_path}.jpg'
        if path.exists(jpg_path):
            return jpg_path
        elif path.exists(png_path):
            return png_path

        print(jpg_path)

        return jpg_path


class MayaFileModel(SuffixFilterModel):

    def __init__(
            self, view: ThumbsListView, directories: List[path.DirectoryPath] | None = None,
            uniform_icons: bool = False, chunk_count: int = 0, browser_preferences: BrowserPreference | None = None):

        extensions = ['ma', 'mb']
        super().__init__(
            view=view, extensions=extensions, directories=directories, uniform_icons=uniform_icons,
            chunk_count=chunk_count, include_sub_dirs=True, browser_preferences=browser_preferences)
