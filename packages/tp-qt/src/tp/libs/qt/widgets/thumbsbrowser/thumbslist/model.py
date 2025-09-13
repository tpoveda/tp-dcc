from __future__ import annotations

import os
import time
import random
import typing
from pathlib import Path
from functools import partial
from typing import cast, TypedDict, Any

from loguru import logger
from Qt.QtCore import (
    Qt,
    Signal,
    QObject,
    QSize,
    QModelIndex,
    QSortFilterProxyModel,
    QThreadPool,
)
from Qt.QtWidgets import QStyleOptionViewItem
from Qt.QtGui import QFont, QImage, QPixmap, QStandardItem, QStandardItemModel, QPainter

from tp.libs.qt import icons
from tp.libs.qt import utils
from tp.libs.python import osplatform

from .utils import IconLoader

if typing.TYPE_CHECKING:
    from tp.preferences.directory import DirectoryPath
    from tp.preferences.assets import BrowserPreference


class ThumbRole:
    """Roles used in the browser model."""

    TAGS = Qt.UserRole
    DESCRIPTION = Qt.UserRole + 1
    FILENAME = Qt.UserRole + 2
    WEBSITES = Qt.UserRole + 3
    CREATORS = Qt.UserRole + 4
    RENDERER = Qt.UserRole + 5


class ThumbApplicationMetadataInfo(TypedDict):
    """Metadata information about the application that created the thumbnail."""

    name: str
    version: str


class ThumbMetadataInfo(TypedDict):
    """ "Metadata information for a thumbnail."""

    time: str
    version: str
    user: str
    name: str
    application: ThumbApplicationMetadataInfo
    description: str
    tags: list[str]


class SerializedThumbData(TypedDict):
    """Serialized data for a thumbnail."""

    metadata: ThumbMetadataInfo


class ItemData:
    _EMPTY_THUMBNAIL: str | None = None

    def __init__(
        self,
        name: str | None = None,
        icon_path: str | None = None,
        file_path: str = "",
        tooltip: str = "",
        thumbnail: str = "",
        auto_thumb_from_image: bool = False,
    ) -> None:
        super().__init__()

        if ItemData._EMPTY_THUMBNAIL is None:
            ItemData._EMPTY_THUMBNAIL = icons.icon_path("emptyThumbnail")["sizes"][200][
                "path"
            ]

        self._name = name or ""
        self._icon_path = icon_path or ""
        self._file_path = file_path
        self._tooltip = tooltip
        self._thumbnail = thumbnail
        self._auto_thumb_from_image = auto_thumb_from_image
        self._resolved_thumbnail: str | None = None

        self._user = ""
        self._file_name = ""
        self._extension = ""
        self._directory = ""
        self._image_extension = "jpg"
        self._metadata: dict[str, Any] = {}
        self._icon_loader: IconLoader | None = None

        self.set_file_path(file_path)
        self._name = self._name or self._file_name

    # === File Path === #

    @property
    def name(self) -> str:
        """The name of the thumb data."""

        return self._name

    @property
    def file_name(self) -> str:
        """The file name of the thumb data without extension."""

        return self._file_name

    @property
    def directory(self) -> str:
        """The directory of the thumb data."""

        return self._directory

    @property
    def tooltip(self) -> str:
        """The tooltip of the thumb data."""

        return self._tooltip

    def set_file_path(self, file_path: str):
        """Set the file path and extracts related file and directory
        information such as directory, file name, extension, and image
        extension if applicable.

        Args:
            file_path: The full file path string to be set and parsed.
        """

        path = Path(file_path)
        self._file_path = file_path
        self._directory = str(path.parent)
        self._file_name = path.name
        suffix = path.suffix.lower()
        self._extension = suffix[1:] if suffix else ""
        if self._extension in [
            image_ext.lower() for image_ext in utils.get_supported_image_extensions()
        ]:
            self._image_extension = self._extension

    def file_name_with_extension(self) -> str:
        """Returns the file name with its extension.

        Returns:
            The file name with its extension as a string.
        """

        return (
            f"{self._file_name}.{self._extension}"
            if self._extension
            else self._file_name
        )

    def full_path(self) -> str:
        """Returns the full path of the file.

        Returns:
            The full file path as a string.
        """

        return Path(self._directory, self.file_name_with_extension()).as_posix()

    # noinspection PyMethodMayBeStatic
    def _normalize_path(self, path: str) -> str:
        """Normalize the given path for reliable comparison.

        Args:
            path: The file path to normalize.

        Returns:
            A normalized path string using forward slashes.
        """

        if not path:
            return ""

        try:
            normalized = Path(path).resolve()
            return normalized.as_posix()
        except (OSError, ValueError):
            # Fallback for invalid paths.
            return Path(path).as_posix()

    # endregion

    # region === Thumbnail === #

    @property
    def icon_loader(self) -> IconLoader | None:
        """The icon loader used to load the thumbnail icon."""

        return self._icon_loader

    @icon_loader.setter
    def icon_loader(self, value: IconLoader) -> None:
        """Sets the icon loader used to load the thumbnail icon."""

        self._icon_loader = value

    def thumbnail_exists(self) -> bool:
        """Checks if the thumbnail exists.

        Returns:
            `True` if the thumbnail exists; `False` otherwise.
        """

        return bool(self._thumbnail) and Path(self._thumbnail).exists()

    def expected_thumbnail_path(self) -> str:
        """Return the path to the thumbnail image.

        This method retrieves the path of the thumbnail image if it is
        explicitly set. If no specific thumbnail path is defined, it constructs
        the path based on the directory, file name, and image extension.

        Returns:
            The file system path to the thumbnail image.
        """

        return (
            self._thumbnail
            or Path(
                self._directory, f"{self._file_name}.{self._image_extension}"
            ).as_posix()
        )

    def thumbnail(self) -> str:
        """Resolves and return the thumbnail path for the current object.

        Notes:
            If the thumbnail was already resolved previously, it will return
            the cached path. Otherwise, it checks for the expected thumbnail
            path, validates its existence, and sets the resolved thumbnail path
            accordingly.

        Returns:
            The resolved thumbnail path.
        """

        if self._resolved_thumbnail is not None:
            return self._resolved_thumbnail

        thumbnail_path = self.expected_thumbnail_path()
        if thumbnail_path and Path(thumbnail_path).exists():
            self._resolved_thumbnail = thumbnail_path
            self._thumbnail = thumbnail_path
        else:
            self._resolved_thumbnail = self._EMPTY_THUMBNAIL

        return self._resolved_thumbnail

    def set_thumbnail(self, thumbnail_path: str):
        """Set the thumbnail for the object, updates the associated image
        extension, and invalidates the thumbnail cache if changes are detected.

        Args:
            thumbnail_path: The path to the new thumbnail image. If the
                provided value is `None` or the same as the current normalized
                path, no changes will be made.
        """

        # Normalize both paths for comparison.
        new_path_normalized = (
            self._normalize_path(thumbnail_path) if thumbnail_path else None
        )
        current_path_normalized = (
            self._normalize_path(self._thumbnail) if self._thumbnail else None
        )
        if new_path_normalized == current_path_normalized:
            return

        self._thumbnail = thumbnail_path
        if thumbnail_path:
            image_extension = Path(thumbnail_path).suffix
            self._image_extension = (
                image_extension[1:].lower() if image_extension else ""
            )

        # Invalidate the thumbnail cache to ensure the new thumbnail is
        # resolved on the next call.
        self._resolved_thumbnail = None

    def icon_loaded(self) -> bool:
        """Check if the icon loader has been initialized and the icon is loaded.

        Returns:
            True if the icon is loaded, False otherwise.
        """

        return self._icon_loader is not None and self._icon_loader.is_finished()

    # endregion

    # region === MetaData === #

    def description(self) -> str:
        return self._metadata.get("description")

    def websites(self) -> list[str]:
        return self._metadata.get("websites", [])

    def creators(self) -> list[str]:
        return self._metadata.get("creators", [])

    def tags(self) -> list[str]:
        return self._metadata.get("tags", [])

    def has_tag(self, tag: str):
        return True if tag in self.tags() else False

    def has_any_tags(self, tags: list[str]) -> bool:
        return any(tag in self.tags() for tag in tags)

    def serialize(self) -> SerializedThumbData:
        """Serialize the thumb data into a dictionary.

        Returns:
            A dictionary containing the serialized thumb data.
        """

        return {
            "metadata": {
                "time": "",
                "version": "",
                "user": "",
                "name": str(self._name),
                "application": {
                    "name": "",
                    "version": "",
                },
                "description": "",
                "tags": [],
            }
        }

    # endregion


class ThumbItemModel(QStandardItem):
    def __init__(
        self,
        data: ItemData,
        square_icon: bool = False,
        parent: ThumbItemModel | None = None,
    ):
        super().__init__(parent)

        self._data = data
        self._square_icon = square_icon
        self._hash = int(time.time() * random.random())

        self._padding = 0
        self._text_height = 11
        self._border_width = 1
        self._text_padding_horizontal = 7
        self._text_padding_vertical = 2
        self._show_text = True
        self._icon_size = QSize(256, 256)
        self._font = QFont("Tahoma")
        self._aspect_ratio = Qt.KeepAspectRatioByExpanding
        self._pixmap: QPixmap | None = None

    # region === Properties === #

    @property
    def item_data(self) -> ItemData:
        """The thumb data associated with this item."""

        return self._data

    @property
    def item_text(self) -> str:
        """The text associated with this item."""

        return self._data.name

    @property
    def square_icon(self) -> bool:
        """Whether the icon should be square."""

        return self._square_icon

    @square_icon.setter
    def square_icon(self, flag: bool):
        """Sets whether the icon should be square."""

        self._square_icon = flag

    # endregion

    # region === Rendering === #

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """Paints the given item in the view using the specified painter and
        style option.

        Args:
            painter: The painter object used to render the item.
            option: The style option that provides metrics and styling
                information for the item being painted.
            index: The model index of the item in the data model that is being
                rendered.
        """

        painter.save()
        painter.restore()

    def sizeHint(self) -> QSize:
        """Returns the size hint for the item.

        Returns:
            The size hint as a QSize object.
        """

        model = cast(ThumbsListModel, self.model())
        size_hint = model.icon_size

        pixmap_size = QSize(1, 1)
        if self._pixmap:
            pixmap_size = self._pixmap.rect().size()

        size = min(size_hint.height(), size_hint.width())
        pixmap_size = QSize(128, 128) if pixmap_size == QSize(0, 0) else pixmap_size

        aspect_ratio = 1
        if not self._square_icon:
            aspect_ratio = float(pixmap_size.width()) / float(pixmap_size.height())

        size_hint.setWidth(size * aspect_ratio)

        size_hint.setHeight(size + 1)

        if self._show_text:
            size_hint.setHeight(
                size_hint.height() + self._text_height + self._text_padding_vertical * 2
            )

        return size_hint


class ThumbsListFilterProxyModel(QSortFilterProxyModel):
    """A proxy model that supports multiple filtering roles and criteria."""

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Determines whether a row in the source model satisfies the criteria
        defined by the filter's regular expression and role.

        Args:
            source_row: The row index in the source model to be evaluated.
            source_parent: The parent index in the model. It represents
                the parent of the row to be evaluated.

        Returns:
            True if the row should be accepted based on the filter criteria;
                False otherwise.
        """

        filter_reg_exp = self.filterRegularExpression()
        if not filter_reg_exp.isValid():
            return True

        requested_role = self.filterRole()
        consolidated_data = ""
        source_model = self.sourceModel()
        row_index = source_model.index(source_row, 0)

        if requested_role == ThumbRole.FILENAME:
            data = source_model.data(row_index, ThumbRole.TAGS)
            consolidated_data += str(data)

        for role in (
            Qt.DisplayRole,
            ThumbRole.TAGS,
            ThumbRole.DESCRIPTION,
            ThumbRole.FILENAME,
            ThumbRole.WEBSITES,
            ThumbRole.CREATORS,
        ):
            if requested_role == role:
                data = source_model.data(row_index, role)
                consolidated_data += str(data)

        return filter_reg_exp.match(consolidated_data).capturedStart() != -1


class ThumbsListModel(QStandardItemModel):
    # Total number of items to load per chunk for lazy loading.
    CHUNK_COUNT = 20

    refreshRequested = Signal()
    doubleClicked = Signal(str)
    parentClosed = Signal(bool)
    itemSelectionChanged = Signal(str, object)

    def __init__(
        self,
        extensions: list[str],
        directories: list[str] | None = None,
        active_directories: list[str] | None = None,
        chunk_count: int | None = None,
        uniform_icons: bool = False,
        include_sub_directories: bool = False,
        preferences: BrowserPreference | None = None,
        parent: QObject | None = None,
    ) -> None:
        """Initialize the `ThumbsListModel`.

        Args:
            extensions: A list of file extensions to filter the thumbnails.
            directories: A list of directory paths to load thumbnails from.
            active_directories: A list of active directory paths to filter
            chunk_count: Number of items to load per chunk for lazy loading.
            uniform_icons: Whether to use uniform icons for all items.
            include_sub_directories: Whether to include sub-directories when
                loading thumbnails.
            parent: The parent QObject, if any.
        """

        super().__init__(parent=parent)

        if not osplatform.is_windows():
            self._extensions = (
                list(
                    set(
                        [i.upper() for i in extensions]
                        + [i.lower() for i in extensions]
                    )
                )
                + extensions
            )
        else:
            self._extensions = extensions
        self._chunk_count = chunk_count or self.CHUNK_COUNT
        self._uniform_icons = uniform_icons
        self._include_sub_directories = include_sub_directories
        self._preferences = preferences

        self._thread_pool = QThreadPool.globalInstance()

        self._loaded_count = 0
        self._items: list[ThumbItemModel] = []
        self._directories: list[DirectoryPath] | None = None
        self._active_directories: list[DirectoryPath] | None = None
        self._icon_size = QSize(256, 256)
        self._current_item_data: ItemData | None = None
        self._current_item_image_path: str | None = None

        if directories:
            self.set_directories(directories, False)

        self.set_active_directories(active_directories, False)

    # === QAbstractItemModel overrides === #

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole) -> Any:
        """Returns the data for the given index and role.

        Args:
            index: The model index to retrieve data for.
            role: The role of the data to retrieve.

        Returns:
            The data for the given index and role.
        """

        if not index.isValid():
            return None

        item = cast(ThumbItemModel, self.itemFromIndex(index))
        if item is None:
            return None

        thumb_data = item.thumb()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return item.thumb_text()
        elif role == Qt.ToolTipRole:
            return item.toolTip()
        elif role == Qt.DecorationRole:
            return item.icon()
        elif role == ThumbRole.FILENAME:
            return thumb_data.file_name
        elif role == ThumbRole.DESCRIPTION:
            return thumb_data.description()
        elif role == ThumbRole.TAGS:
            return thumb_data.tags()
        elif role == ThumbRole.WEBSITES:
            return thumb_data.websites()
        elif role == ThumbRole.CREATORS:
            return thumb_data.creators()

        return super().data(index, role)

    def clear(self) -> None:
        """Clears the thumbs and the data from the model."""

        # Remove non-started threads from the thread pool.
        self._thread_pool.clear()

        # Wait for all threads to finish before clearing the model.
        while not self._thread_pool.waitForDone():
            continue

        self._loaded_count = 0

        super().clear()

    # endregion

    # region === Preferences ===

    @property
    def preferences(self) -> BrowserPreference | None:
        """The browser preferences."""

        return self._preferences

    def refresh_asset_folders(self) -> None:
        """Refresh the asset folders from the preferences."""

        if not self._preferences:
            return

        self._preferences.refresh_asset_folders(set_active=True)

    # endregion

    # region === Directories === #

    def set_directory(
        self, directory: str | DirectoryPath | None, refresh: bool = True
    ):
        """Sets the directory to be used by the model.

        Args:
            directory: The directory path to set.
            refresh: Whether to refresh the model after setting the directory.
        """

        self.set_directories(
            [DirectoryPath(directory)]
            if isinstance(directory, str)
            else [directory]
            if directory
            else None,
            refresh=refresh,
        )

    def set_directories(
        self, directories: list[str | DirectoryPath] | None, refresh: bool = True
    ):
        """Sets the directories to be used by the model.

        Args:
            directories: A list of directory paths to set.
            refresh: Whether to refresh the model after setting the directories.
        """

        self._directories = (
            [
                DirectoryPath(directory) if isinstance(directory, str) else directory
                for directory in directories
            ]
            if directories and isinstance(directories, list)
            else None
        )

        if refresh:
            self.refresh()

    def active_directories(self) -> list[DirectoryPath]:
        """Returns the active directories used by the model.

        Returns:
            A list of active directories.
        """

        if self._active_directories is None:
            self._active_directories = self._directories

        return self._active_directories or []

    def set_active_directories(
        self, directories: list[str | DirectoryPath] | None, refresh: bool = True
    ):
        """Sets the active directories to be used by the model.

        Args:
            directories: A list of directory paths to set as active.
            refresh: Whether to refresh the model after setting the active
                directories.
        """

        self._active_directories = (
            [
                DirectoryPath(directory) if isinstance(directory, str) else directory
                for directory in directories
            ]
            if directories and isinstance(directories, list)
            else None
        )

        if refresh:
            self.refresh()

    # endregion

    # region === Items === #

    @property
    def current_item_data(self) -> ItemData | None:
        """The data of the currently selected item."""

        return self._current_item_data

    @property
    def current_item_image_path(self) -> str | None:
        """The image path of the currently selected item."""

        return self._current_item_image_path

    @property
    def icon_size(self) -> QSize:
        """The icon size used by the model."""

        return self._icon_size

    @icon_size.setter
    def icon_size(self, value: QSize) -> None:
        """Set the icon size used by the model."""

        self._icon_size = value

    def set_uniform_item_sizes(self, flag: bool) -> None:
        """Sets whether the icons should be uniform in size.

        Args:
            flag: `True` to use uniform icon sizes; `False` otherwise.
        """

        self._uniform_icons = flag

        for row in range(self.rowCount()):
            item = cast(ThumbItemModel, self.itemFromIndex(self.index(row, 0)))
            item.square_icon = flag

    # endregion

    # region === Loading === #

    def update_from_prefs(self, update_items: bool = True) -> None:
        """Updates the model's directories and active directories from the
        preferences.

        Args:
            update_items: Whether to update the items if the active directories
                have changed.
        """

        if not self._preferences:
            return

        self._directories = self._preferences.browser_folder_paths()
        old_active_directories = self._active_directories
        self._active_directories = self._preferences.active_browser_paths()

        # If the active directories have changed, update the items.
        if update_items and not set(
            [Path(a.path).as_posix() for a in old_active_directories]
        ) == set([Path(b.path).as_posix() for b in self._active_directories]):
            logger.debug("Active directories have changed, updating items...")
            self._update_items()

    def load_data(self, chunk_count: int = 0) -> None:
        """Loads data based on a specified chunk count.

        This function uses a lazy loading filter to determine the items
        to load and then performs the data loading operation.

        Args:
            chunk_count: The number of chunks to consider for lazy loading.
                If set to 0, all available data is loaded.

        Notes:
            - Lazy loading happens either on initialization and any time the
                vertical bar hits the max value.
        """

        items_to_load = self.lazy_load_filter(chunk_count)
        self._load_items(items_to_load)

    def lazy_load_filter(self, chunk_count: int = 0) -> list[ThumbItemModel]:
        """Retrieves the next chunk of items for lazy loading.

        Args:
            chunk_count: Number of items to load. If 0, uses the default chunk
                size configured for this model. If the model defines a default
                chunk in its constructor, this value will be ignored.

        Returns:
            A list of `QStandardItem` objects representing the next chunk of
                items to be loaded.
        """

        files_to_load: list[ThumbItemModel] = []

        chunk_count = self._chunk_count if chunk_count == 0 else chunk_count
        if len(self._items) < self._loaded_count:
            files_to_load.extend(
                [
                    cast(ThumbItemModel, self.itemFromIndex(self.index(row, 0)))
                    for row in range(self.rowCount())
                ]
            )
        else:
            for i in range(self._loaded_count, self._loaded_count + chunk_count):
                index = self.index(i, 0)
                if not index.isValid():
                    continue
                item = cast(ThumbItemModel, self.itemFromIndex(index))
                if item is not None:
                    files_to_load.append(item)

        return files_to_load

    def _load_items(self, items_to_load: list[ThumbItemModel]) -> None:
        """Loads the specified items using separate threads for each item.

        Args:
            items_to_load: A list of `ThumbItemModel` items to be loaded.
        """

        threads: list[IconLoader] = []
        for item in items_to_load:
            thread = self._load_item_in_thread(item)
            if thread is not None:
                threads.append(thread)
            self._loaded_count += 1

        # Start all threads in the thread pool.
        for thread in threads:
            self._thread_pool.start(thread)

    def _load_item_in_thread(
        self, item_to_load: ThumbItemModel, start: bool = False
    ) -> IconLoader | None:
        """Loads a thumbnail item in a separate thread if a valid thumbnail path
        exists.

        This method checks if the given item's thumbnail exists and is a valid
        file. If so, it initializes a new thread for loading the thumbnail and
        connects the necessary signals for updating the item's icon.

        Optionally, the thread can be started immediately if specified.

        Args:
            item_to_load: The thumbnail item to be loaded.
            start: Whether to start the thread immediately after loading the
                item.

        Returns:
            The worker thread created for loading the thumbnail, or `None` if
                no valid thumbnail was found.
        """

        item_data = item_to_load.item_data
        thumbnail = item_data.thumbnail()
        if not thumbnail or os.path.isfile(thumbnail):
            return None

        worker_thread = IconLoader(icon_path=thumbnail)
        worker_thread.signals.updated.connect(
            partial(self._set_item_icon_from_image, item_to_load)
        )
        self.parentClosed.connect(worker_thread.finish)

        # Make sure to keep a reference to the worker thread in the item data
        # to prevent it from being garbage collected.
        item_data.icon_loader = worker_thread

        if start:
            self._thread_pool.start(worker_thread)
            self._loaded_count += 1

        return worker_thread

    def _set_item_icon_from_image(self, item: ThumbItemModel, image: QImage) -> None:
        """Sets the icon of the given item from the provided image.

        This method converts the provided `QImage` into a `QPixmap`, scales it
        to fit the model's icon size while maintaining the aspect ratio, and
        then sets it as the item's icon.

        Args:
            item: The thumbnail item whose icon is to be set.
            image: The `QImage` to be converted and set as the item's icon.
        """

        print("Setting image icon from image...")

    def refresh(self):
        self.clear()
        self.refreshRequested.emit()
        self.update_from_prefs(update_items=False)
        self._update_items()

    def _update_items(self):
        print("Updating items ...")

    def reset(self):
        """Resets the model data, notifying the views that the model has been
        reset.
        """

        self.beginResetModel()
        self.endResetModel()

    def _get_next_chunk_items(
        self, chunk_size: int | None = None
    ) -> list[ThumbItemModel]:
        """Retrieves the next chunk of items for lazy loading.

        This method supports incremental loading of items to improve
        performance when dealing with large datasets. It can load all
        remaining items if the current loaded count exceeds available items
        or load a specific chunk size.

        Args:
            chunk_size: Number of items to load. If 0, uses the default chunk
                size configured for this model. If the model defines a default
                chunk in its constructor, this value will be ignored.

        Returns:
            A list of `QStandardItem` objects representing the next chunk of
                items to be loaded.
        """

        chunk_size = self._chunk_count or chunk_size

        # If we have fewer file items than loaded count, load all remaining
        # items.
        if len(self._items) < self._loaded_count:
            return [
                cast(ThumbItemModel, self.itemFromIndex(self.index(row, 0)))
                for row in range(self.rowCount())
            ]

        # Load the next chunk of items.
        items_to_load: list[ThumbItemModel] = []
        end_index = self._loaded_count + chunk_size
        for i in range(self._loaded_count, end_index):
            index = self.index(i, 0)
            if not index.isValid():
                continue
            item = cast(ThumbItemModel, self.itemFromIndex(index))
            if item is not None:
                items_to_load.append(item)

        return items_to_load
