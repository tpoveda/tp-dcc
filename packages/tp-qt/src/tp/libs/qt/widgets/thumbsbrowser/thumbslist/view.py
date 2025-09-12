from __future__ import annotations

from typing import cast

from Qt.QtCore import Qt, Signal, QSize, QThreadPool, QModelIndex
from Qt.QtWidgets import QWidget, QListView, QStyledItemDelegate, QStyleOptionViewItem
from Qt.QtGui import QPainter

from .model import ThumbItemModel
from .model import ThumbsListFilterProxyModel
from ...viewmodel import modelutils
from ...viewmodel.listview import ListView


class ThumbnailsListViewDelegate(QStyledItemDelegate):
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        source_index, source_model = modelutils.map_to_source_model(index)
        item = cast(ThumbItemModel, source_model.itemFromIndex(source_index))
        return item.sizeHint() if item is not None else QSize()

    def paint(
        self, painter: QPainter, options: QStyleOptionViewItem, index: QModelIndex
    ):
        source_index, source_model = modelutils.map_to_source_model(index)
        item = cast(ThumbItemModel, source_model.itemFromIndex(source_index))
        if not item:
            return

        item.paint(painter, options, index)


class ThumbsListView(ListView):
    _DEFAULT_ICON_SIZE = QSize(256, 256)
    _MAX_THREAD_COUNT = 200

    stateChanged = Signal()
    contextMenuRequested = Signal(list, object)

    def __init__(
        self,
        icon_size: QSize | None = None,
        uniform_icons: bool = False,
        delegate_class: type[QStyledItemDelegate] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self._current_icon_size = QSize(icon_size or self._DEFAULT_ICON_SIZE)
        self._default_column_count = 4
        self._column_count = self._default_column_count
        self._uniform_icons = uniform_icons
        self._zoomable = True
        self._pagination = True
        self._persistent_filter: list[tuple[str, list[str]]] = []

        self._thread_pool = QThreadPool.globalInstance()
        self._thread_pool.setMaxThreadCount(self._MAX_THREAD_COUNT)

        self._proxy_model = ThumbsListFilterProxyModel(parent=self)
        self._proxy_model.setDynamicSortFilter(True)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitive)

        self._delegate = (
            delegate_class(parent=self)
            if delegate_class is not None
            else ThumbnailsListViewDelegate(parent=self)
        )
        self.setItemDelegate(self._delegate)

        self.setLayoutMode(QListView.LayoutMode.Batched)
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
        self.setIconSize(self._current_icon_size)

        self._setup_signals()

    def _setup_signals(self):
        """Set up the signals of the list view."""

        vertical_scroll_bar = self.verticalScrollBar()
        vertical_scroll_bar.valueChanged.connect(self._pagination_load_next_items)
        vertical_scroll_bar.rangeChanged.connect(self._pagination_load_next_items)
        vertical_scroll_bar.sliderReleased.connect(self.stateChanged.emit)
        self.clicked.connect(self.stateChanged.emit)
        self.activated.connect(self.stateChanged.emit)
        self.entered.connect(self.stateChanged.emit)

    # region === Visuals === #

    def setIconSize(self, size: QSize) -> None:
        """Set the icon size of the thumbnails.

        Args:
            size: The new icon size.
        """

        self._current_icon_size = size
        super().setIconSize(size)


    # endregion

    # region === Navigation === #

    def _pagination_load_next_items(self):
        pass

    # endregion
