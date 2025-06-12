from __future__ import annotations

from Qt.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout

from .. import dpi


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

    def addSpacing(self, size: int):
        super().addSpacing(dpi.dpi_scale(size))


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
