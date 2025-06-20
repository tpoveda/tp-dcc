from __future__ import annotations

import os
from typing import TypedDict

from loguru import logger
from Qt.QtCore import Qt, QSize
from Qt.QtGui import QIcon

from tp.core import host
from tp.libs.python.decorators import Singleton


class IconSizeDict(TypedDict):
    """Typed dictionary that defines an icon size."""

    path: str


class IconDict(TypedDict):
    """Typed dictionary that defines an icon."""

    name: str
    sizes: dict[int, IconSizeDict]
    relativeDir: str


class IconsManager(metaclass=Singleton):
    """Manages icons by caching and providing access to their paths, data, and
    resized versions.

    This class is responsible for managing icons by maintaining a centralized
    cache that stores information about available icons. It retrieves icon
    file data, builds a cache for optimized access, and offers various utility
    methods for manipulating and retrieving icons by their names or paths.

    Attributes:
        _icons_cache: Cache storing information about icons including name,
            relative directory, and sizes.
        _icon_paths: List of directories containing icon files.
    """

    _icons_cache: dict[str, IconDict] = {}
    _icon_paths: list[str] = []

    def __init__(self):
        super().__init__()

        self.refresh()

    @classmethod
    def refresh(cls):
        """Refreshes all the available icons."""

        cls._icons_cache.clear()
        cls._icon_paths.clear()

        cls._icon_paths = os.getenv("TP_DCC_ICON_PATHS", "").split(os.pathsep)
        for _icon_path in cls._icon_paths:
            if not _icon_path or not os.path.exists(_icon_path):
                continue
            for root, _, files in os.walk(_icon_path):
                for file_name in files:
                    if not file_name.endswith(".png"):
                        continue
                    icon_name = file_name.split(os.extsep)[0]
                    name_split = icon_name.split("_")
                    if len(name_split) < 1:
                        continue
                    name = "_".join(name_split[:-1])
                    try:
                        size = int(name_split[-1])
                    except ValueError:
                        logger.warning(
                            f"Incorrect size formatting: {os.path.join(root, file_name)}"
                        )
                        continue

                    if name in cls._icons_cache:
                        sizes = cls._icons_cache[name]["sizes"]
                        if size in sizes:
                            continue
                        # noinspection PyTypedDict
                        sizes[size] = IconSizeDict(path=os.path.join(root, file_name))
                    else:
                        # noinspection PyTypeChecker
                        cls._icons_cache[name] = IconDict(
                            name=name,
                            relativeDir=root.replace(_icon_path, ""),
                            sizes={
                                size: IconSizeDict(path=os.path.join(root, file_name))
                            },
                        )

    @classmethod
    def icon_path(cls, icon_name: str) -> IconDict:
        """Fetch the path details for a specified icon from the cached icon
        data.

        Args:
            icon_name: The name of the icon to retrieve from the cache.

        Returns:
            The cached dictionary containing the icon details if found; `None`
                if the icon is not present in the cache.
        """

        return cls._icons_cache.get(icon_name)

    @classmethod
    def icon_data_for_name(cls, icon_name: str, size: int = 16) -> IconSizeDict:
        """Return icon data for a given icon name and size.

        Notes:
            If the icon name contains an underscore with a numeric
            suffix (e.g., "icon_16"), the size is extracted from the suffix.
            If the specified size is not available, the method defaults to
            retrieving the data for the largest available size of the icon.

        Args:
            icon_name: The name of the icon for which to retrieve data. If
                the name includes a numeric suffix separated by an underscore,
                it will be treated as the size.
            size: The desired size of the icon. Defaults to 16 if not
                explicitly provided or if a size cannot be determined from the
                icon name.

        Returns:
            A dictionary containing the icon data for the specified size.
                If no data is found for the given icon name, an empty
                dictionary is returned.
        """

        if "_" in icon_name:
            splitter = icon_name.split("_")
            if splitter[-1].isdigit():
                size = splitter[-1]
                icon_name = "_".join(splitter[:-1])
        else:
            size = str(size)

        icon_data = cls._icons_cache.get(icon_name, {})
        if not icon_data:
            return IconSizeDict(path="")

        sizes = icon_data["sizes"]
        if size not in sizes:
            size = list(sizes.keys())[-1]
            icon_data = sizes[size]
        else:
            icon_data = icon_data["sizes"][size]

        return icon_data

    @classmethod
    def icon_path_for_name(cls, icon_name: str, size: int = 16) -> str:
        """Return the file path of the icon for the specified name and size.

        Args:
            icon_name: The name of the icon to retrieve.
            size: The size of the icon in pixels. Defaults to 16.

        Returns:
            The file path of the icon, or an empty string if the icon is not
                found.
        """

        return cls.icon_data_for_name(icon_name, size).get("path", "")

    @classmethod
    def resize_icon(cls, icon: QIcon, size: QSize) -> QIcon:
        """Resizes a given `QIcon` to the specified `QSize` while preserving
        its aspect ratio.

        Args:
            icon: The input QIcon to resize.
            size: The target size for the icon.

        Returns:
            A new `QIcon` resized to the specified dimensions, or the original
                `QIcon` if no resizing is possible.
        """

        if len(icon.availableSizes()) == 0:
            return icon

        original_size = icon.availableSizes()[0]
        pixmap = icon.pixmap(original_size)
        pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        return QIcon(pixmap)

    @classmethod
    def icon(cls, icon_name: str, size: int = 16) -> QIcon | None:
        """Create and returns a `QIcon` object based on the given icon name
        and size.

        Notes:
            It supports headless environments, returning `None` to avoid
                issues with icon loading when a graphical user interface is
                not present.

        Args:
            icon_name: The name or path of the icon to be loaded. This can be
                a resource path (e.g., starting with ":/" or "qrc:/") or a
                custom icon name.
            size: The desired size of the icon. Defaults to 16. If the size
                is -1, the icon will not be resized.

        Returns:
            A `QIcon` object constructed based on the provided icon name and
                size. If the application is in headless mode, it returns
                `None`.
        """

        # In headless mode, return None to avoid loading icons.
        if host.current_host().host.is_headless:
            return None

        if icon_name.startswith((":/", "qrc:/", ":")):
            new_icon = QIcon(icon_name)
        else:
            icon_data = cls.icon_data_for_name(icon_name, size=size)
            new_icon = QIcon(icon_data.get("path", ""))

        if size != -1:
            new_icon = cls.resize_icon(new_icon, QSize(size, size))

        return new_icon


# noinspection PyTypeChecker
manager: IconsManager = IconsManager()
icon = manager.icon
icon_data_for_name = manager.icon_data_for_name
icon_path_for_name = manager.icon_path_for_name
icon_path = manager.icon_path
