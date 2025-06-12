from __future__ import annotations

import os
from typing import TypedDict

from loguru import logger
from Qt.QtCore import Qt, QSize
from Qt.QtGui import QIcon

from tp.libs.dcc import app
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
    """Class that allows to register and retrieve icons."""

    _icons_cache: dict[str, dict[str, IconDict]] = {}
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
        for icon_path in cls._icon_paths:
            if not icon_path or not os.path.exists(icon_path):
                continue
            for root, _, files in os.walk(icon_path):
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
                        sizes[size] = IconSizeDict(path=os.path.join(root, file_name))
                    else:
                        cls._icons_cache[name] = {
                            "name": name,
                            "relativeDir": root.replace(icon_path, ""),
                            "sizes": {
                                size: IconSizeDict(path=os.path.join(root, file_name))
                            },
                        }

    @classmethod
    def icon_path(cls, icon_name: str) -> dict[str, IconDict] | None:
        """Returns the path to the icon with the given name.

        :param icon_name: name of the icon to get the path for.
        :return: icon path if found; None otherwise.
        """

        return cls._icons_cache.get(icon_name)

    @classmethod
    def icon_data_for_name(cls, icon_name: str, size: int = 16) -> IconSizeDict:
        """Returns the icon data for the given icon name.

        :param icon_name: name of the icon to get the data for.
        :param size: size of the icon to get the data for.
        :return: icon data for the given icon name.
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
            return {}

        sizes = icon_data["sizes"]
        if size not in sizes:
            size = list(sizes.keys())[-1]
            icon_data = sizes[size]
        else:
            icon_data = icon_data["sizes"][size]

        return icon_data

    @classmethod
    def icon_path_for_name(cls, icon_name: str, size: int = 16) -> str:
        """Returns the icon path for the given icon name.

        :param icon_name: name of the icon to get the path for.
        :param size: size of the icon to get the path for.
        :return: icon path for the given icon name.
        """

        icon_data = cls.icon_data_for_name(icon_name, size)
        if not icon_data:
            return ""

        return icon_data["path"]

    @staticmethod
    def icon_path_is_from_qrc(icon_path: str) -> bool:
        """Returns whether the given icon path is from a Qt resource file or not.

        :param icon_path: icon path to check.
        :return: whether the icon path is from a Qt resource file or not.
        """

        return icon_path.startswith((":/", "qrc:/", ":"))

    @classmethod
    def resize_icon(cls, icon: QIcon, size: QSize) -> QIcon:
        """Resizes the given icon to the given size.
        Default scaling is done using smooth bi-linear interpolation and keep aspect
        ratio.

        :param icon: icon to resize.
        :param size: size to resize the icon to.
        :return: resized icon.
        """

        if len(icon.availableSizes()) == 0:
            return

        original_size = icon.availableSizes()[0]
        pixmap = icon.pixmap(original_size)
        pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return QIcon(pixmap)

    @classmethod
    def icon(cls, icon_name: str, size: int = 16) -> QIcon | None:
        """Returns the icon with the given name.

        :param icon_name: name of the icon to get.
        :param size: size of the icon to get.
        :return: QIcon with the icon data if found; None otherwise.
        """

        if app.FnApp().is_batch():
            return

        if cls.icon_path_is_from_qrc(icon_name):
            new_icon = QIcon(icon_name)
        else:
            icon_data = cls.icon_data_for_name(icon_name, size=size)
            new_icon = QIcon(icon_data.get("path", ""))
        if size != -1:
            new_icon = cls.resize_icon(new_icon, QSize(size, size))

        return new_icon


icon = IconsManager().icon
icon_data_for_name = IconsManager().icon_data_for_name
icon_path_for_name = IconsManager().icon_path_for_name
icon_path = IconsManager().icon_path
