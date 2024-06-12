from __future__ import annotations

from typing import Iterable

from . import dpi, pixmap
from ..externals.Qt.QtCore import Qt, QSize
from ..externals.Qt.QtGui import QColor, QIcon


def colorize_icon(
        icon: QIcon, size: int | None = None, color: tuple[int, int, int] | QColor = (255, 255, 255),
        overlay_icon: QIcon | None = None, overlay_color: tuple[int, int, int] | QColor = (255, 255, 255)) -> QIcon:
    """
    Colorizes the given icon.

    :param icon: icon to colorize.
    :param size: icon size. If not given first available icon size will be used.
    :param color: RGB color in 0 to 255 range.
    :param overlay_icon: optional icon to overlay.
    :param overlay_color: overlay RGB color in 0 to 255 range.
    :return: colorized icon.
    """

    size = size or icon.availableSizes()[0]
    size = dpi.dpi_scale(size)
    if isinstance(size, (int, float)):
        size = QSize(size, size)

    orig_size = icon.availableSizes()[0]
    colorized_pixmap = pixmap.colorize_pixmap(icon.pixmap(orig_size), color)
    if overlay_icon is not None:
        overlay_pixmap = overlay_icon.pixmap(orig_size)
        pixmap.overlay_pixmap(colorized_pixmap, overlay_pixmap, overlay_color)

    colorized_pixmap = colorized_pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    return QIcon(colorized_pixmap)


def colorize_layered_icon(
        icons: list[QIcon], colors: Iterable[QColor] | None = None, scaling: list[float, float] | None = None):
    """
    Layers multiple icons with various colors into one icon.

    :param icons: list of icons to colorize.
    :param colors: list of icon colors.
    :param scaling: icon scaling.
    :return: new colorized icon.
    :rtype: QIcon
    """

    if not icons:
        return

    if isinstance(scaling, list):
        scaling = list(scaling)

    if not isinstance(colors, list):
        colors = [colors]
    else:
        colors = list(colors)

    default_size = 1

    if colors is None or (len(icons) > len(colors)):
        colors = colors or list()
        colors += [None] * (len(icons) - len(colors))

    if scaling is None or len(icons) > len(scaling):
        icon_scaling = scaling or []
        icon_scaling += [default_size] * (len(icons) - len(icon_scaling))

    icon_largest = icons.pop(0)
    return icon_largest
