from __future__ import annotations

from Qt.QtCore import Qt
from Qt.QtGui import QColor, QPixmap, QPainter

from . import color


def colorize_pixmap(
    pixmap: QPixmap, new_color: str | tuple[int, int, int] | QColor
) -> QPixmap:
    """
    Colorizes the given pixmap with a new color based on its alpha map.

    :param pixmap: pixmap to colorize.
    :param new_color: new color in tuple format (255, 255, 255).
    :return: colorized pixmap.
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


def overlay_pixmap(
    pixmap: QPixmap,
    over_pixmap: QPixmap,
    overlay_color: str | tuple[int, int, int] | QColor,
    align: Qt.AlignmentFlag = Qt.AlignCenter,
):
    """
    Overlays one pixmap over the other.

    :param pixmap: base pixmap to overlay over_pixmap on top.
    :param over_pixmap: pixmap to overlay on top of pixmap.
    :param overlay_color: overlay color in tuple format (255, 255, 255).
    :param align: overlay alignment mode.
    .. note:: no new pixmap is generated, source pixmap is modified
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
