from __future__ import annotations

from typing import cast

from Qt.QtCore import Qt, Signal, QSize, QThreadPool, QModelIndex, QItemSelection
from Qt.QtWidgets import QWidget, QListView, QStyledItemDelegate, QStyleOptionViewItem
from Qt.QtGui import QPainter, QMouseEvent

from .model import ThumbItemModel, ThumbsListModel
from .model import ThumbsListFilterProxyModel
from ...viewmodel import modelutils
from ...viewmodel.listview import ListView
from ...mouseslider import MouseDragSlider, SliderSettings


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
    _DEFAULT_MINIMUM_ICON_SIZE = 20
    _DEFAULT_MAXIMUM_ICON_SIZE = 512
    _MAX_THREAD_COUNT = 200

    stateChanged = Signal()
    contextMenuRequested = Signal(list, object)

    def __init__(
        self,
        icon_size: QSize | None = None,
        uniform_icons: bool = False,
        delegate_class: type[QStyledItemDelegate] | None = None,
        mouse_slider: bool = False,
        slider_settings: SliderSettings | None = None,
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
        self._mouse_slider = (
            MouseDragSlider(parent=self, **(slider_settings or {}))
            if mouse_slider
            else None
        )

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

    # region === Setup === #

    def _setup_signals(self):
        """Set up the signals of the list view."""

        vertical_scroll_bar = self.verticalScrollBar()
        vertical_scroll_bar.valueChanged.connect(self._pagination_load_next_items)
        vertical_scroll_bar.rangeChanged.connect(self._pagination_load_next_items)
        vertical_scroll_bar.sliderReleased.connect(self.stateChanged.emit)
        self.clicked.connect(self.stateChanged.emit)
        self.activated.connect(self.stateChanged.emit)
        self.entered.connect(self.stateChanged.emit)

    # endregion

    # region === Model === #

    def root_model(self) -> ThumbsListModel | None:
        """Returns the root model of the view.

        Returns:
            The root model of the view.
        """

        # noinspection PyTypeChecker
        return modelutils.get_source_model(self.model())

    def setModel(self, model: ThumbsListModel) -> None:
        """Set the model for the thumbnail list view.

        Args:
            model: The model to set.
        """

        self._proxy_model.setSourceModel(model)
        model.icon_size = self._current_icon_size
        model.set_uniform_item_sizes(self._uniform_icons)

        super().setModel(self._proxy_model)

        # noinspection PyBroadException
        try:
            self.selectionModel().selectionChanged.disconnect(
                self._on_selection_changed
            )
        except Exception:
            pass
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def invisible_root_item(self) -> ThumbItemModel | None:
        """Returns the invisible root item of the model.

        Returns:
            The invisible root item of the model.
        """

        current_model = self.root_model()
        return (
            cast(ThumbItemModel, current_model.invisibleRootItem())
            if current_model is not None
            else None
        )

    def refresh(self):
        proxy_model: ThumbsListFilterProxyModel | None = cast(
            ThumbsListFilterProxyModel, self.model()
        )
        if proxy_model is not None:
            proxy_model.layoutChanged.emit()

        self._update_image_size_for_column_layout(self._column_count)

        # Make sure updates are enabled.
        if not self.updatesEnabled():
            self.setUpdatesEnabled(True)

    # endregion

    # region === Visuals === #

    def setIconSize(self, size: QSize) -> None:
        """Set the icon size of the thumbnails.

        Args:
            size: The new icon size.
        """

        self._current_icon_size = size

        model = self.root_model()
        if model is not None:
            model.icon_size = size

        super().setIconSize(size)

    def setUniformItemSizes(self, uniform: bool) -> None:
        """Set whether the icons should be uniform in size.

        Args:
            uniform: Whether to use uniform icon sizes.
        """

        self._uniform_icons = uniform

        # super().setUniformItemSizes(uniform)

        root_model = self.root_model()
        if root_model is not None:
            root_model.set_uniform_item_sizes(uniform)

    def set_columns(self, columns: int, refresh: bool = False) -> None:
        """Set the number of columns in the view.

        Args:
            columns: The number of columns to set.
            refresh: Whether to refresh the view after setting the columns.
        """

        self._column_count = columns

        if refresh:
            self._update_image_size_for_column_layout(columns)

    def _update_image_size_for_column_layout(self, column_count: int) -> None:
        """Update the image size based on the number of columns.

        This method calculates the appropriate icon size to fit the specified
        number of columns within the current view width, taking into account
        the space occupied by the vertical scrollbar. It ensures that the icon
        size remains within predefined minimum and maximum limits.

        Args:
            column_count: The number of columns to fit in the view.
        """

        view_size = self.size()
        view_width = view_size.width() - self.verticalScrollBar().sizeHint().width() - 2
        image_width = int(view_width / float(column_count))

        # If the calculated image width is outside the allowed range, do not update.
        if (
            image_width >= self._DEFAULT_MAXIMUM_ICON_SIZE
            or image_width <= self._DEFAULT_MINIMUM_ICON_SIZE
        ):
            return

        self._column_count = column_count
        self.setIconSize(QSize(image_width, image_width))
        self._pagination_load_next_items()

    # endregion

    # region === Navigation === #

    def _pagination_load_next_items(self):
        pass

    # endregion

    # region === Events == #

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events.

        Args:
            event: The mouse event.
        """

        if self._mouse_slider:
            self._mouse_slider.mouse_pressed(event)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move events.

        Args:
            event: The mouse event.
        """

        if self._mouse_slider:
            moving = self._mouse_slider.mouse_moved(event)

            # If sliding, do not pass the event to the parent.
            if moving:
                return None

        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release events.

        Args:
            event: The mouse event.
        """

        if self._mouse_slider:
            self._mouse_slider.mouse_released(event)

        super().mouseReleaseEvent(event)

    # endregion

    # region === Callbacks === #

    def _on_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ):
        print("selection changed ...")

    # endregion
