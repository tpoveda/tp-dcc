from __future__ import annotations

from .. import dpi
from ..uiconsts import DEFAULT_SPACING
from ...externals.Qt.QtCore import Qt
from ...externals.Qt.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout


def vertical_layout(
        spacing: int = DEFAULT_SPACING, margins: tuple[int, int, int, int] = (2, 2, 2, 2),
        alignment: Qt.AlignmentFlag | None = None, parent: QWidget | None = None) -> QVBoxLayout:
    """
    Returns a new vertical layout that automatically handles DPI stuff.

    :param spacing: layout spacing
    :param margins: layout margins.
    :param alignment: optional layout alignment.
    :param parent: optional layout parent.
    :return: new vertical layout instance.
    """

    new_layout = VerticalLayout(parent=parent)
    new_layout.setContentsMargins(*margins)
    new_layout.setSpacing(spacing)
    if alignment is not None:
        new_layout.setAlignment(alignment)

    return new_layout


def horizontal_layout(
        spacing: int = DEFAULT_SPACING, margins: tuple[int, int, int, int] = (0, 0, 0, 0),
        alignment: Qt.AlignmentFlag | None = None, parent: QWidget | None = None) -> QHBoxLayout:
    """
    Returns a new horizontal layout that automatically handles DPI stuff.

    :param spacing: layout spacing
    :param margins: layout margins.
    :param alignment: optional layout alignment.
    :param parent: optional layout parent.
    :return: new horizontal layout instance.
    """

    new_layout = HorizontalLayout(parent)
    new_layout.setContentsMargins(*margins)
    new_layout.setSpacing(spacing)
    if alignment is not None:
        new_layout.setAlignment(alignment)

    return new_layout


def grid_layout(
        spacing: int = DEFAULT_SPACING, margins: tuple[int, int, int, int] = (0, 0, 0, 0),
        column_min_width: list[int, int] | None = None, column_min_width_b: list[int, int] | None = None,
        vertical_spacing: int | None = None, horizontal_spacing: int | None = None,
        parent: QWidget | None = None) -> QGridLayout:
    """
    Returns a new grid layout that automatically handles DPI stuff.

    :param spacing: layout spacing
    :param margins: layout margins.
    :param column_min_width: optional colum minimum width.
    :param column_min_width_b: optional colum secondary minimum width.
    :param vertical_spacing: optional vertical spacing.
    :param horizontal_spacing: optional horizontal spacing.
    :param parent: optional layout parent.
    :return: new grid layout instance.
    """

    new_layout = GridLayout(parent)
    new_layout.setContentsMargins(*margins)
    if not vertical_spacing and not horizontal_spacing:
        new_layout.setHorizontalSpacing(spacing)
        new_layout.setVerticalSpacing(spacing)
    elif vertical_spacing and not horizontal_spacing:
        new_layout.setHorizontalSpacing(horizontal_spacing)
        new_layout.setVerticalSpacing(vertical_spacing)
    elif horizontal_spacing and not vertical_spacing:
        new_layout.setHorizontalSpacing(horizontal_spacing)
        new_layout.setVerticalSpacing(spacing)
    else:
        new_layout.setHorizontalSpacing(horizontal_spacing)
        new_layout.setVerticalSpacing(vertical_spacing)

    if column_min_width:
        new_layout.setColumnMinimumWidth(column_min_width[0], dpi.dpi_scale(column_min_width[1]))
    if column_min_width_b:
        new_layout.setColumnMinimumWidth(column_min_width_b[0], dpi.dpi_scale(column_min_width_b[1]))

    return new_layout


class VerticalLayout(QVBoxLayout):
    """
    Custom vertical layout that automatically handles DPI when setting margins and space.
    """

    def setContentsMargins(self, left: int, top: int, right: int, bottom: int):
        super().setContentsMargins(*dpi.margins_dpi_scale(*(left, top, right, bottom)))

    def setSpacing(self, spacing: int):
        super().setSpacing(dpi.dpi_scale(spacing))


class HorizontalLayout(QHBoxLayout):
    """
    Custom horizontal layout that automatically handles DPI when setting margins and space.
    """

    def setContentsMargins(self, left: int, top: int, right: int, bottom: int):
        super().setContentsMargins(*dpi.margins_dpi_scale(*(left, top, right, bottom)))

    def setSpacing(self, spacing: int):
        super().setSpacing(dpi.dpi_scale(spacing))


class GridLayout(QGridLayout):
    """
    Custom grid layout that automatically handles DPI when setting margins and space.
    """

    def setContentsMargins(self, left: int, top: int, right: int, bottom: int):
        super().setContentsMargins(*dpi.margins_dpi_scale(*(left, top, right, bottom)))

    def setSpacing(self, spacing: int):
        super().setSpacing(dpi.dpi_scale(spacing))

    def setVerticalSpacing(self, spacing: int):
        super().setVerticalSpacing(dpi.dpi_scale(spacing))

    def setHorizontalSpacing(self, spacing: int):
        super().setHorizontalSpacing(dpi.dpi_scale(spacing))

    def setColumnMinimumWidth(self, column: int, min_size: int):
        super().setColumnMinimumWidth(column, dpi.dpi_scale(min_size))
