from __future__ import annotations

import time
import random
import typing
from pathlib import Path
from typing import cast, TypedDict, Any

from Qt.QtCore import (
    Qt,
    Signal,
    QObject,
    QModelIndex,
    QSortFilterProxyModel,
    QThreadPool,
)
from Qt.QtWidgets import QStyleOptionViewItem
from Qt.QtGui import QStandardItem, QStandardItemModel, QPainter

from tp.libs.qt import icons
from tp.libs.qt import utils
from tp.libs.python import osplatform

from .utils import IconLoader

if typing.TYPE_CHECKING:
    from tp.preferences.directory import DirectoryPath
    from .view import ThumbsListView


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


class ThumbData:
    _EMPTY_THUMBNAIL: str | None = None

    def __init__(
        self,
        name: str | None = None,
        icon_path: str | None = None,
        file_path: str = "",
        thumbnail: str = "",
    ):
        super().__init__()

        if ThumbData._EMPTY_THUMBNAIL is None:
            ThumbData._EMPTY_THUMBNAIL = icons.icon_path("emptyThumbnail")["sizes"][
                200
            ]["path"]

        self._name = name or ""
        self._file_path = file_path
        self._thumbnail = thumbnail
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

    @property
    def name(self) -> str:
        """The name of the thumb data."""

        return self._name

    @property
    def file_name(self) -> str:
        """The file name of the thumb data without extension."""

        return self._file_name

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

    def thumbnail_exists(self) -> bool:
        """Checks if the thumbnail exists.

        Returns:
            True if the thumbnail exists, False otherwise.
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

    def icon_loaded(self) -> bool:
        """Check if the icon loader has been initialized and the icon is loaded.

        Returns:
            True if the icon is loaded, False otherwise.
        """

        return self._icon_loader is not None and self._icon_loader.is_finished()

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


class ThumbItemModel(QStandardItem):
    def __init__(
        self,
        data: ThumbData,
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

    def thumb(self) -> ThumbData:
        """Returns the thumb data associated with this item.

        Returns:
            The ThumbData instance associated with this item.
        """

        return self._data

    def thumb_text(self) -> str:
        """Returns the text representation of the thumb data.

        Returns:
            The text representation of the thumb data.
        """

        return self._data.name

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
    CHUNK_COUNT = 20

    refreshRequested = Signal()
    doubleClicked = Signal(str)
    parentClosed = Signal(bool)
    itemSelectionChanged = Signal(str, object)

    def __init__(
        self,
        view: ThumbsListView,
        extensions: list[str],
        directories: list[str] | None = None,
        active_directories: list[str] | None = None,
        chunk_count: int | None = None,
        uniform_icons: bool = False,
        include_sub_directories: bool = False,
        parent: QObject | None = None,
    ):
        super().__init__(parent=parent)

        self._view = view
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

        self._thread_pool = QThreadPool.globalInstance()

        self._loaded_count = 0
        self._file_items: list[ThumbItemModel] = []
        self._directories: list[DirectoryPath] | None = None
        self._active_directories: list[DirectoryPath] | None = None

        if directories:
            self.set_directories(directories, False)

        self.set_active_directories(active_directories, False)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole):
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

    def load_data(self, chunk_count: int = 0):
        pass

    def refresh(self):
        self.clear()
        self.refreshRequested.emit()
        self._update_from_prefs(False)
        self._update_items()

    def clear(self):
        """Clears the thumbs and the data from the model."""

        # Remove non-started threads from the thread pool.
        self._thread_pool.clear()

        # Wait for all threads to finish before clearing the model.
        while self._thread_pool.waitForDone():
            continue

        self._loaded_count = 0

        super().clear()

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
        if len(self._file_items) < self._loaded_count:
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
