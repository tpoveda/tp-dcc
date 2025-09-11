from __future__ import annotations

from Qt import QtCompat
from Qt.QtCore import Qt, QObject, QPoint, QRect, QSize
from Qt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLayout,
    QWidgetItem,
)

from .. import dpi


class VerticalLayout(QVBoxLayout):
    """Custom vertical layout that automatically handles DPI when setting
    margins and space.
    """

    def setContentsMargins(self, left: int, top: int, right: int, bottom: int):
        super().setContentsMargins(*dpi.margins_dpi_scale(*(left, top, right, bottom)))

    def setSpacing(self, spacing: int):
        super().setSpacing(dpi.dpi_scale(spacing))


class HorizontalLayout(QHBoxLayout):
    """Custom horizontal layout that automatically handles DPI when setting
    margins and space.
    """

    def setContentsMargins(self, left: int, top: int, right: int, bottom: int):
        super().setContentsMargins(*dpi.margins_dpi_scale(*(left, top, right, bottom)))

    def setSpacing(self, spacing: int):
        super().setSpacing(dpi.dpi_scale(spacing))

    def addSpacing(self, size: int):
        super().addSpacing(dpi.dpi_scale(size))


class GridLayout(QGridLayout):
    """Custom grid layout that automatically handles DPI when setting margins
    and space.
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


class FlowLayout(QLayout):
    """Flow layout that automatically arranges child widgets horizontally or
    vertically and wraps them as needed. It also handles DPI scaling for
    margins and spacing.
    """

    def __init__(
        self,
        margin: int = 0,
        spacing_x: int = 2,
        spacing_y: int = 2,
        parent: QObject | None = None,
    ):
        super().__init__(parent=parent)

        self._spacing_x = spacing_x
        self._spacing_y = spacing_y
        self._orientation = Qt.Horizontal
        self._items: list[QWidgetItem] = []
        self._overflow = False

        if parent is not None:
            self.setMargin(margin)
        self.setSpacing(spacing_x)
        self.set_spacing_x(spacing_x)
        self.set_spacing_y(spacing_y)

        self._size_hint_layout = self.minimumSize()

    def itemAt(self, index: int) -> QWidgetItem | None:
        """Return the item at the given index.

        Args:
            index: The index of the item to return.

        Returns:
            The item at the given index or None if the index is out of range.
        """

        if 0 <= index < len(self._items):
            return self._items[index]

        return None

    def takeAt(self, index: int) -> QWidgetItem | None:
        """Remove and return the item at the given index.

        Args:
            index: The index of the item to remove.

        Returns:
            The item at the given index or None if the index is out of range.
        """

        if 0 <= index < len(self._items):
            return self._items.pop(index)

        return None

    def expandingDirections(self) -> Qt.Orientations:
        """Return the expanding directions of the layout.

        Returns:
            The expanding directions of the layout.
        """

        return Qt.Orientations(self.orientation())

    def hasHeightForWidth(self) -> bool:
        """Return whether the layout has height for width.

        Returns:
            True if the layout has height for width, False otherwise.
        """

        return self.orientation() == Qt.Horizontal

    def heightForWidth(self, width: int) -> int:
        """Return the height for the given width.

        Args:
            width: The width to calculate the height for.

        Returns:
            The height for the given width.
        """

        height = self._do_layout(QRect(0, 0, width, 0), True)
        self._size_hint_layout = QSize(width, height)

        return height

    def setGeometry(self, rect: QRect) -> None:
        """Set the geometry of the layout.

        Args:
            rect: The rectangle to set the geometry to.
        """

        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self) -> QSize:
        """Return the size hint of the layout.

        Returns:
            The size hint of the layout.
        """

        return self._size_hint_layout

    def minimumSize(self) -> QSize:
        """Return the minimum size of the layout.

        Returns:
            The minimum size of the layout.
        """

        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())

        size += QSize(2, 2)

        return size

    def addItem(self, item: QWidgetItem) -> None:
        """Add an item to the layout.

        Args:
            item: The item to add.
        """

        self._items.append(item)

    def orientation(self) -> Qt.Orientation:
        """Return the layout orientation.

        Returns:
            The layout orientation.
        """

        return self._orientation

    def set_orientation(self, orientation: Qt.Orientation) -> None:
        """Set the layout orientation.

        Args:
            orientation: The layout orientation to set.
        """

        self._orientation = orientation
        self.update()

    def count(self) -> int:
        """Return the number of items in the layout.

        Returns:
            The number of items in the layout.
        """

        return len(self._items)

    def add_spacing(self, spacing: int) -> None:
        """Add spacing to the layout.

        Args:
            spacing: The spacing to add.
        """

        space_widget = QWidget()
        space_widget.setFixedSize(QSize(spacing, spacing))
        self.addWidget(space_widget)

    def set_spacing_x(self, spacing: int) -> None:
        """Set the horizontal spacing of the layout.

        Args:
            spacing: The horizontal spacing to set.
        """

        self._spacing_x = dpi.dpi_scale(spacing)
        self.update()

    def set_spacing_y(self, spacing: int) -> None:
        """Set the vertical spacing of the layout.

        Args:
            spacing: The vertical spacing to set.
        """

        self._spacing_y = dpi.dpi_scale(spacing)
        self.update()

    def insert_widget(self, index: int, widget: QWidget) -> None:
        """Insert a widget at the given index.

        Args:
            index: The index to insert the widget at.
            widget: The widget to insert.
        """

        self._items.insert(index, QWidgetItem(widget))
        self.update()

    def items(self) -> list[QWidgetItem]:
        """Return the list of items in the layout.

        Returns:
            The list of items in the layout.
        """

        invalid_items: list[QWidgetItem] = []
        for item in self._items:
            if not QtCompat.isValid(item):
                invalid_items.append(item)

        [self._items.remove(item) for item in invalid_items]

        return self._items

    def allow_overflow(self) -> None:
        """Allow items to overflow the layout boundaries."""

        self._overflow = True

    def clear(self) -> None:
        """Clear all items in the layout."""

        item = self.takeAt(0)
        while item:
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            item = self.takeAt(0)

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        """Perform the layout of the items in the layout.

        Args:
            rect: The rectangle to lay out the items in.
            test_only: Whether to only test the layout without actually
                setting the geometry of the items.

        Returns:
            The height of the layout.
        """

        x = rect.x()
        y = rect.y()
        line_height = 0
        orientation = self.orientation()

        for item in self._items:
            wid = item.widget()
            if wid is not None and wid.isHidden():
                continue

            space_x = self._spacing_x
            space_y = self._spacing_y

            if orientation == Qt.Horizontal:
                next_x = x + item.sizeHint().width() + space_x
                if next_x - space_x > rect.right() and line_height > 0:
                    if not self._overflow:
                        x = rect.x()
                        y = y + line_height + (space_y * 2)
                        next_x = x + item.sizeHint().width() + space_x
                        line_height = 0

                if not test_only:
                    item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
                x = next_x
                line_height = max(line_height, item.sizeHint().height())
            else:
                next_y = y + item.sizeHint().height() + space_y
                if next_y - space_y > rect.bottom() and line_height > 0:
                    if not self._overflow:
                        y = rect.y()
                        x = x + line_height + (space_x * 2)
                        next_y = y + item.sizeHint().height() + space_y
                        line_height = 0

                if not test_only:
                    item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
                x = next_y
                line_height = max(line_height, item.sizeHint().height())

        if orientation == Qt.Horizontal:
            return y + line_height - rect.y()

        return x + line_height - rect.x()
