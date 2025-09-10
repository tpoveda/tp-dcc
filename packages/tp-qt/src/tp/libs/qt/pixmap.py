from __future__ import annotations

from Qt.QtCore import Qt
from Qt.QtGui import QColor, QImage, QPixmap, QPainter

from . import color


def colorize_pixmap(
    pixmap: QPixmap, new_color: str | tuple[int, int, int] | QColor
) -> QPixmap:
    """Colorize the given pixmap with a new color based on its alpha map.

    Args:
        pixmap: pixmap to colorize.
        new_color: new color in tuple format (255, 255, 255).

    Returns:
        Colorized pixmap.
    """

    if isinstance(new_color, str):
        new_color = color.from_string(new_color)
    elif isinstance(new_color, (tuple, list)):
        new_color = QColor(*new_color)
    if not new_color:
        return pixmap

    mask = pixmap.mask()
    pixmap.fill(new_color)
    pixmap.setMask(mask)

    return pixmap


def grayscale_pixmap(pixmap: QPixmap) -> QPixmap:
    """Convert the given pixmap to grayscale while preserving its alpha channel.

    Args:
        pixmap: Pixmap to convert to grayscale.

    Returns:
        Grayscale pixmap.
    """

    original_image = pixmap.toImage()
    image_format = original_image.format()
    gray = original_image.convertToFormat(QImage.Format_Grayscale8)
    image = gray.convertToFormat(image_format)
    if original_image.hasAlphaChannel():
        original_alpha = original_image.convertToFormat(QImage.Format_Alpha8)
        image.setAlphaChannel(original_alpha)

    return QPixmap(image)


def tint_pixmap(
    pixmap: QPixmap,
    tint_color: tuple[float, float, float, float] = (255, 255, 255, 100),
    composition_mode: QPainter.CompositionMode = QPainter.CompositionMode_Plus,
) -> None:
    """Tints the given pixmap with the given color using the specified
    composition mode.

    Args:
        pixmap: Pixmap to tint.
        tint_color: Tint color in RGBA format (255, 255, 255, 100).
        composition_mode: Composition mode to use.

    Notes:
        - No new pixmap is generated, source pixmap is modified.
    """

    tint_color = QColor(*tint_color)
    _overlay_pixmap = QPixmap(pixmap.width(), pixmap.height())
    _overlay_pixmap.fill(tint_color)
    _overlay_pixmap.setMask(pixmap.mask())

    painter = QPainter(pixmap)
    painter.setCompositionMode(composition_mode)
    painter.drawPixmap(
        0,
        0,
        _overlay_pixmap.width(),
        _overlay_pixmap.height(),
        _overlay_pixmap,
    )
    painter.end()


def overlay_pixmap(
    pixmap: QPixmap,
    over_pixmap: QPixmap,
    overlay_color: str | tuple[int, int, int] | QColor,
    align: Qt.AlignmentFlag = Qt.AlignCenter,
):
    """Overlay one pixmap over the other.

    Args:
        pixmap: Base pixmap to overlay over_pixmap on top.
        over_pixmap: Pixmap to overlay on top of pixmap.
        overlay_color: Overlay color in tuple format (255, 255, 255).
        align: Overlay alignment mode.

    Notes:
        - No new pixmap is generated, source pixmap is modified.
    """

    if overlay_color and isinstance(overlay_color, str):
        overlay_color = color.from_string(overlay_color)

    if overlay_color is not None:
        over_pixmap = colorize_pixmap(over_pixmap, overlay_color)

    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

    x = 0
    y = 0
    if align is Qt.AlignCenter:
        x = pixmap.width() / 2 - over_pixmap.width() / 2
        y = pixmap.height() / 2 - over_pixmap.height() / 2
    elif align is None:
        x = 0
        y = 0

    painter.drawPixmap(x, y, over_pixmap.width(), over_pixmap.height(), over_pixmap)
    painter.end()
