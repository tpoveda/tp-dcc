from __future__ import annotations

import platform
from typing import Tuple, Iterable

from Qt.QtCore import QPoint, QSize
from Qt.QtWidgets import QApplication


if platform.system().lower() == "windows":
    DPI = 72.0
elif platform.system().lower() == "darwin":
    DPI = 96.0
else:
    DPI = 72.0

# global UI scale value. This should correspond to any UI scaling in the host DCC. In standalone mode, the app factors
# in the current DPI scales the UI accordingly.
UI_SCALE = 1.0
SCALE_FACTORS = (0.7, 0.8, 0.9, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0)


def init_ui_scale(value: int | float | None = None):
    """
    Loads the current user-set UI scale value.

    :param value: optional UI scale value.
    """

    global UI_SCALE

    value = ui_scale_value(value)

    UI_SCALE = value


def ui_scale_value(value: int | float | None = None) -> float:
    """
    Returns the current user-set UI scale value.

    :param value: optional UI scale value.
    :return: UI scale value.
    """

    if value is None:
        value = 1.0
    if isinstance(value, str):
        if "%" not in value:
            value = 1.0
        else:
            value = value.strip("%")
        # noinspection PyBroadException
        try:
            value = float(value) * 0.01
        except Exception:
            return 1.0
        if value not in SCALE_FACTORS:
            value = 1.0
    else:
        value = 1.0

    return value


def dpi_multiplier() -> float:
    """
    Returns current application DPI multiplier.

    :return: DPI multiplier value
    """

    desktop = QApplication.primaryScreen()
    logical_y = desktop.logicalDotsPerInchY() if desktop is not None else DPI

    return max(1, int(float(logical_y) / float(DPI))) * float(UI_SCALE)


def dpi_scale(value: int | float) -> int | float:
    """
    Resizes by value based on current DPI.

    :param value: value default 2k size in pixels/
    :return: size in pixels now DPI monitor is (4k, 2k, ...).
    """

    return value * dpi_multiplier()


def dpi_scale_divide(value: int) -> float:
    """
    Inverse resize by value based on current DPI, for values that may get resized twice.

    :param value: size in pixels
    :return: divided size in pixels
    """

    mult = dpi_multiplier()
    if value != 0:
        return float(value) / float(mult)

    return value


def margins_dpi_scale(
    left: int | Iterable[int],
    top: int | None = None,
    right: int | None = None,
    bottom: int | None = None,
) -> Tuple[int, int, int, int]:
    """
    Returns proper margins with DPI taking into account

    :param left: left margin value.
    :param top: top margin value.
    :param right: right margin value.
    :param bottom: bottom margin value.
    :return: Tuple containing left, top, right, bottom values taking into account current app DPI
    """

    if isinstance(left, (tuple, list)):
        margins = left
        return (
            dpi_scale(margins[0]),
            dpi_scale(margins[1]),
            dpi_scale(margins[2]),
            dpi_scale(margins[3]),
        )

    return dpi_scale(left), dpi_scale(top), dpi_scale(right), dpi_scale(bottom)


def point_by_dpi(point: QPoint) -> QPoint:
    """
    Scales given QPoint by the current DPI scaling.

    :param point: point to scale by current DPI scaling
    :return: Newly scaled QPoint.
    """

    return QPoint(dpi_scale(point.x()), dpi_scale(point.y()))


def size_by_dpi(size: QSize) -> QSize:
    """
    Scales given QSize by the current DPI scaling value.

    :param size: size to scale by current DPI scaling.
    :return: newly scaled QSize.
    """

    return QSize(dpi_scale(size.width()), dpi_scale(size.height()))


# noinspection PyPep8Naming,PyUnresolvedReferences
class DPIScaling:
    """
    Mixin class that can be used in any QWidget to add DPI scaling functionality to it
    """

    # Necessary to avoid multiple inheritance issues.
    def __init__(self, *args, **kwargs):
        pass

    def setFixedSize(self, size):
        return super(DPIScaling, self).setFixedSize(dpi_scale(size))

    def setFixedHeight(self, height):
        return super(DPIScaling, self).setFixedHeight(dpi_scale(height))

    def setFixedWidth(self, width):
        return super(DPIScaling, self).setFixedWidth(dpi_scale(width))

    def setMaximumWidth(self, width):
        return super(DPIScaling, self).setMaximumWidth(dpi_scale(width))

    def setMinimumWidth(self, width):
        return super(DPIScaling, self).setMinimumWidth(dpi_scale(width))

    def setMaximumHeight(self, height):
        return super(DPIScaling, self).setMaximumHeight(dpi_scale(height))

    def setMinimumHeight(self, height):
        return super(DPIScaling, self).setMinimumHeight(dpi_scale(height))
