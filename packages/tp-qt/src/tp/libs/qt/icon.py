from __future__ import annotations

from typing import Iterable

from loguru import logger
from Qt.QtCore import Qt, QSize
from Qt.QtGui import QColor, QPixmap, QIcon, QPainter

from . import dpi, pixmap


def grayscale_icon(icon: QIcon) -> QIcon:
    """Convert the given icon to grayscale.

    Args:
        icon: Icon to convert to grayscale.

    Returns:
        Grayscale icon.
    """

    if not icon:
        return icon

    for size in icon.availableSizes():
        icon.addPixmap(icon.pixmap(size, QIcon.Disabled))

    return icon


def colorize_icon(
    icon: QIcon,
    size: int | None = None,
    color: tuple[int, int, int] | QColor = (255, 255, 255),
    overlay_icon: QIcon | None = None,
    overlay_color: tuple[int, int, int] | QColor = (255, 255, 255),
) -> QIcon:
    """Colorize the given icon.

    Args:
        icon: Icon to colorize.
        size: Icon size. If not given, the first available icon size will be used.
        color: RGB color in 0 to 255 range.
        overlay_icon: Optional icon to overlay.
        overlay_color: Overlay RGB color in 0 to 255 range.

    Returns:
        Colorized icon.
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

    colorized_pixmap = colorized_pixmap.scaled(
        size, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )

    return QIcon(colorized_pixmap)


def colorize_layered_icon(
    icons: list[QIcon],
    size: int = 16,
    colors: Iterable[QColor] | None = None,
    scaling: list[float] | None = None,
    tint_color: tuple[float, float, float, float] | None = None,
    tint_composition: QPainter.CompositionMode = QPainter.CompositionMode_Plus,
    grayscale: bool = False,
):
    """Layers multiple icons with various colors into one icon.

    Args:
        icons: List of icons to colorize.
        size: Icon size. If not given, the first available icon size will be
            used.
        colors: List of icon colors.
        scaling: List of icon scaling.
        tint_color: If given, the final icon will be tinted with this color.
        tint_composition: `QPainter` composition mode to use for tinting.
        grayscale: If `True`, the icons will be converted to grayscale.

    Returns:
        New colorized layered icon.
    """

    default_size = 1

    if not isinstance(icons, list):
        icons = [icons]
    elif isinstance(icons, list):
        icons = icons.copy()

    if isinstance(scaling, list):
        scaling = scaling.copy()

    if not isinstance(colors, list):
        colors = [colors]
    else:
        colors = colors.copy()

    if not icons:
        logger.warning("No icons provided to colorize_layered_icon()")
        _pixmap = QPixmap(16, 16)
        _pixmap.fill(QColor(255, 0, 0))

    if colors is None or (len(icons) > len(colors)):
        colors = colors or list()
        colors += [None] * (len(icons) - len(colors))

    if scaling is None or len(icons) > len(scaling):
        icon_scaling = scaling or []
        icon_scaling += [default_size] * (len(icons) - len(icon_scaling))

    icon_largest: QIcon | None = icons.pop(0) if icons else None
    if not icon_largest:
        return icon_largest

    sizes = icon_largest.availableSizes()
    if not sizes:
        return icon_largest

    original_size = sizes[0]
    color_to_apply = colors.pop(0)
    scale_to_apply = scaling.pop(0) if scaling else 1.0
    if color_to_apply is None:
        _pixmap = icon_largest.pixmap(original_size * scale_to_apply)
    else:
        _pixmap = pixmap.colorize_pixmap(
            icon_largest.pixmap(original_size * scale_to_apply), color_to_apply
        )

    # Overlay icons.
    for i, icon in enumerate(icons):
        if not icon:
            continue
        overlay_pixmap = icon.pixmap(original_size * scaling[i])
        pixmap.overlay_pixmap(_pixmap, overlay_pixmap, colors[i])

    # Tint.
    if tint_color is not None:
        pixmap.tint_pixmap(_pixmap, tint_color, composition_mode=tint_composition)

    _pixmap = _pixmap.scaled(
        QSize(size, size), Qt.KeepAspectRatio, Qt.SmoothTransformation
    )

    icon = QIcon(_pixmap)

    if grayscale:
        _pixmap = pixmap.grayscale_pixmap(_pixmap)
        icon = grayscale_icon(QIcon(_pixmap))

    return icon
