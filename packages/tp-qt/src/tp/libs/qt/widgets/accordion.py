from __future__ import annotations

from typing import Any

import enum

from loguru import logger
from Qt.QtCore import Qt, Signal, QObject, QPoint, QRect, QMimeData, QEvent
from Qt.QtWidgets import QApplication, QWidget, QVBoxLayout, QGroupBox, QScrollArea
from Qt.QtGui import (
    QCursor,
    QColor,
    QPixmap,
    QPalette,
    QIcon,
    QPen,
    QBrush,
    QPainter,
    QDrag,
    QPolygon,
    QPainterPath,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QMouseEvent,
    QPaintEvent,
)

from tp import dcc

from .. import dpi


class AccordionItem(QGroupBox):
    """Class that represents an expandable group that can contain multiple
    accordion item within it. Collapsible accordion widget similar to Maya
    Attribute Editor.
    """

    trigger = Signal(bool)

    def __init__(
        self,
        accordion: Accordion,
        title: str,
        widget: QWidget,
        icon: QIcon | None = None,
    ):
        super().__init__(parent=accordion)

        self._accordion_widget = accordion
        self._widget = widget
        self._icon = icon
        self._rollout_style = Accordion.Style.Rounded
        self._drag_drop_mode = Accordion.DragDrop.NoDragDrop
        self._collapsed = False
        self._collapsible = True
        self._clicked = False
        self._custom_data = {}

        layout = QVBoxLayout()
        layout.setSpacing(dpi.dpi_scale(0))
        layout.setContentsMargins(*dpi.margins_dpi_scale(6, 12, 6, 6))
        layout.addWidget(widget)

        self.setAcceptDrops(True)
        self.setLayout(layout)
        self.setTitle(title)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_show_menu)

    @property
    def accordion_widget(self) -> Accordion:
        """The accordion widget that contains this item."""

        return self._accordion_widget

    @property
    def widget(self) -> QWidget:
        """The widget wrapped by this accordion item."""

        return self._widget

    @property
    def rollout_style(self) -> Accordion.Style:
        """The rollout style of this accordion item."""

        return self._rollout_style

    @rollout_style.setter
    def rollout_style(self, value: Accordion.Style):
        """The rollout style of this accordion item."""

        self._rollout_style = value

    @property
    def drag_drop_mode(self) -> Accordion.DragDrop:
        """The drag and drop mode of this accordion item."""

        return self._drag_drop_mode

    @drag_drop_mode.setter
    def drag_drop_mode(self, value: Accordion.DragDrop):
        """Sets the drag and drop mode of this accordion item."""

        self._drag_drop_mode = value

    @property
    def collapsible(self) -> bool:
        """Whether this accordion item is collapsible."""

        return self._collapsible

    @collapsible.setter
    def collapsible(self, flag: bool):
        """Sets whether this accordion item is collapsible."""

        self._collapsible = flag

    def enterEvent(self, event: QEvent):
        """Override base QGroupBox enterEvent function.

        Args:
            event: The Qt event that triggered this method.
        """

        self.accordion_widget.leaveEvent(event)
        event.accept()

    def leaveEvent(self, event: QEvent):
        """Override base QGroupBox leaveEvent function.

        Args:
            event: The Qt event that triggered this method.
        """

        self.accordion_widget.enterEvent(event)
        event.accept()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Override base QGroupBox dragEnterEvent function.

        Args:
            event: The Qt drag enter event that triggered this method.
        """

        if not self._drag_drop_mode:
            return
        source = event.source()
        if (
            source != self
            and source.parent() == self.parent()
            and isinstance(source, AccordionItem)
        ):
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Override base QGroupBox dragMoveEvent function.

        Args:
            event: The Qt drag move event that triggered this method.
        """

        if not self._drag_drop_mode:
            return
        source = event.source()
        if (
            source != self
            and source.parent() == self.parent()
            and isinstance(source, AccordionItem)
        ):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Override base QGroupBox dropEvent function.

        Args:
            event: The Qt drop event that triggered this method.
        """

        widget = event.source()
        layout = self.parent().layout()
        # noinspection PyUnresolvedReferences
        layout.insertWidget(layout.indexOf(self), widget)
        self._accordion_widget.emit_items_reordered()

    def mousePressEvent(self, event: QMouseEvent):
        """Override base QGroupBox mousePressEvent function.

        Args:
            event: The Qt mouse press event that triggered this method.
        """

        if event.button() == Qt.LeftButton and self.drag_drop_rect().contains(
            event.pos()
        ):
            try:
                pixmap = QPixmap.grabWidget(self, self.rect())
            except AttributeError:
                pixmap = self.grab(self.rect())
            mime_data = QMimeData()
            mime_data.setText("ItemTitle::{}".format(self.title()))
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            if not drag.exec_():
                self._accordion_widget.emit_item_drag_failed(self)
            event.accept()
        # Check if the expand/collapse should happen
        elif event.button() == Qt.LeftButton and self.expand_collapse_rect().contains(
            event.pos()
        ):
            self._clicked = True
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Override base QGroupBox mouseMoveEvent function.

        Args:
            event: The Qt mouse move event that triggered this method.
        """

        event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Override base QGroupBox mouseReleaseEvent function.

        Args:
            event: The Qt mouse release event that triggered this method.
        """

        if self._clicked and self.expand_collapse_rect().contains(event.pos()):
            self.toggle_collapsed()
            event.accept()
        else:
            event.ignore()
        self._clicked = False

    def paintEvent(self, event: QPaintEvent):
        """Override base QGroupBox paintEvent function.

        Args:
            event: The Qt paint event that triggered this method.
        """

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)

        x = self.rect().x()
        y = self.rect().y()
        w = self.rect().width() - 1
        h = self.rect().height() - 1
        _rect = dpi.dpi_scale(5)

        if self.rollout_style == Accordion.Style.Rounded:
            header_color = QColor("#242424")
            background_color = QColor("#242424")
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(background_color))
            painter.drawRoundedRect(x, y, w, h - 1, _rect, _rect)
            path = QPainterPath()
            path.setFillRule(Qt.WindingFill)

            path.addRoundedRect(x + 1, y + 1, w - 1, dpi.dpi_scale(20), _rect, _rect)
            if not self.is_collapsed():
                path.addRect(x + 1, y + dpi.dpi_scale(22), w - 1, dpi.dpi_scale(5))
            painter.setBrush(QBrush(header_color))
            painter.drawPath(path.simplified())
            painter.restore()

            painter.drawText(
                x + dpi.dpi_scale(33) if not self._icon else dpi.dpi_scale(40),
                y + dpi.dpi_scale(0),
                w,
                dpi.dpi_scale(22),
                Qt.AlignLeft | Qt.AlignTop,
                self.title(),
            )
            self._draw_triangle(painter, x, y)
            self._draw_icon(painter, x + dpi.dpi_scale(22), y + dpi.dpi_scale(3))

        elif self.rollout_style == Accordion.Style.Square:
            painter.drawText(
                x + dpi.dpi_scale(33) if not self._icon else dpi.dpi_scale(40),
                y + dpi.dpi_scale(3),
                w,
                dpi.dpi_scale(22),
                Qt.AlignLeft | Qt.AlignTop,
                self.title(),
            )
            self._draw_triangle(painter, x, y)
            self._draw_icon(painter, x + dpi.dpi_scale(22), y + dpi.dpi_scale(3))
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.15)
            painter.setPen(pen)
            painter.drawRect(x + 1, y + 1, w - 1, h - 1)
            pen.setColor(self.palette().color(QPalette.Shadow))
            painter.setPen(pen)
        elif self.rollout_style == Accordion.Style.Maya:
            painter.drawText(
                x + dpi.dpi_scale(33) if not self._icon else dpi.dpi_scale(40),
                y + dpi.dpi_scale(3),
                w,
                dpi.dpi_scale(22),
                Qt.AlignLeft | Qt.AlignTop,
                self.title(),
            )
            painter.setRenderHint(QPainter.Antialiasing, False)
            self._draw_triangle(painter, x, y)
            self._draw_icon(painter, x + dpi.dpi_scale(22), y + dpi.dpi_scale(3))
            header_height = dpi.dpi_scale(26)
            header_rect = QRect(x + 1, y + 1, w - 1, header_height)
            header_rect_shadow = QRect(
                x - 1, y - 1, w + 1, header_height + dpi.dpi_scale(2)
            )
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.4)
            painter.setPen(Qt.NoPen)
            painter.drawRect(header_rect)
            painter.fillRect(header_rect, QColor(255, 255, 255, 18))
            pen.setColor(self.palette().color(QPalette.Dark))
            painter.setPen(pen)
            painter.drawRect(header_rect_shadow)
            if not self.is_collapsed():
                offset = header_height + dpi.dpi_scale(3)
                body_rect = QRect(x, y + offset, w, h - offset)
                painter.drawRect(body_rect)
        elif self.rollout_style == Accordion.Style.Boxed:
            if self.is_collapsed():
                a_rect = QRect(x + 1, y + dpi.dpi_scale(9), w - 1, dpi.dpi_scale(4))
                b_rect = QRect(x, y + dpi.dpi_scale(8), w - 1, dpi.dpi_scale(4))
                text = "+"
            else:
                a_rect = QRect(x + 1, y + dpi.dpi_scale(9), w - 1, h - dpi.dpi_scale(9))
                b_rect = QRect(x, y + dpi.dpi_scale(8), w - 1, h - dpi.dpi_scale(9))
                text = "-"

            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.6)
            painter.setPen(pen)
            painter.drawRect(a_rect)
            painter.drawRect(b_rect)
            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.setBrush(self.palette().color(QPalette.Window).darker(120))
            painter.drawRect(
                x + dpi.dpi_scale(10), y + 1, w - dpi.dpi_scale(20), dpi.dpi_scale(24)
            )
            painter.drawText(
                x + dpi.dpi_scale(16),
                y + 1,
                w - dpi.dpi_scale(32),
                dpi.dpi_scale(22),
                Qt.AlignLeft | Qt.AlignVCenter,
                text,
            )
            painter.drawText(
                x + dpi.dpi_scale(10),
                y + 1,
                w - dpi.dpi_scale(20),
                dpi.dpi_scale(22),
                Qt.AlignCenter,
                self.title(),
            )

        if self.drag_drop_mode:
            rect = self.drag_drop_rect()
            _layout = rect.left()
            _rect = rect.right()
            center_y = rect.center().y()
            for y in (
                center_y - dpi.dpi_scale(3),
                center_y,
                center_y + dpi.dpi_scale(3),
            ):
                painter.drawLine(_layout, y, _rect, y)

        painter.end()

    def custom_data(self, key: str, default: Any = None) -> Any:
        """Return a custom pointer to information stored with this item.

        Args:
            key: Data key to retrieve.
            default: Default value to return if key is not found.

        Returns:
            The custom data associated with the key, or the default value
            if not found.
        """

        return self._custom_data.get(str(key), default)

    def set_custom_data(self, key: str, value: Any):
        """Set a custom pointer to information stored on this item.

        Args:
            key: Data key to set.
            value: Data value to associate with the key.
        """

        self._custom_data[str(key)] = value

    # noinspection PyMethodMayBeStatic
    def drag_drop_rect(self) -> QRect:
        """Return default drag and drop rectangle.

        Returns:
            A QRect representing the drag and drop area.
        """

        return QRect(
            dpi.dpi_scale(25), dpi.dpi_scale(7), dpi.dpi_scale(10), dpi.dpi_scale(6)
        )

    def expand_collapse_rect(self) -> QRect:
        """Return the expanded drag and drop rectangle.

        Returns:
            A QRect representing the expand/collapse area.
        """

        return QRect(0, 0, self.width(), dpi.dpi_scale(20))

    def is_collapsed(self) -> bool:
        """Return whether accordion is collapsed.

        Returns:
            True if accordion is collapsed, False otherwise.
        """

        return self._collapsed

    def set_collapsed(self, state: bool = True):
        """Set whether accordion is collapsed.

        Args:
            state: True to collapse accordion, False to expand it.
        """

        if self.collapsible:
            accord = self.accordion_widget
            accord.setUpdatesEnabled(True)
            self._collapsed = state
            if state:
                self.setMinimumHeight(dpi.dpi_scale(22))
                self.setMaximumHeight(dpi.dpi_scale(22))
                self.widget.setVisible(False)
            else:
                self.setMinimumHeight(0)
                self.setMaximumHeight(1000000)
                self.widget.setVisible(True)

            self._accordion_widget.emit_item_collapsed(self)
            accord.setUpdatesEnabled(True)

    def toggle_collapsed(self) -> bool:
        """Toggle current accordion collapse status.

        Returns:
            True if accordion was collapsed, False otherwise.
        """

        collapsed_state = not self.is_collapsed()
        self.set_collapsed(collapsed_state)
        return collapsed_state

    def _on_show_menu(self):
        """Request to show the current accordionwidget item contextual menu."""

        if QRect(0, 0, self.width(), 20).contains(self.mapFromGlobal(QCursor.pos())):
            self._accordion_widget.emit_item_menu_requested(self)

    def _draw_triangle(self, painter: QPainter, x: int, y: int):
        """Handle the painting of the triangle icon.

        Args:
            painter: Painter instance used to handle the painting operation.
            x: X position for the triangle.
            y: Y position for the triangle.
        """

        if self.rollout_style == Accordion.Style.Maya:
            brush = QBrush(QColor(255, 0, 0, 160), Qt.SolidPattern)
        else:
            brush = QBrush(QColor(255, 255, 255, 160), Qt.SolidPattern)
        if not self.is_collapsed():
            tl, tr, tp = (
                dpi.point_by_dpi(QPoint(x + 9, y + 8)),
                dpi.point_by_dpi(QPoint(x + 19, y + 8)),
                dpi.point_by_dpi(QPoint(x + 14, int(y + 13.0))),
            )
            points = [tl, tr, tp]
            triangle = QPolygon(points)
        else:
            tl, tr, tp = (
                dpi.point_by_dpi(QPoint(x + 11, y + 6)),
                dpi.point_by_dpi(QPoint(x + 16, y + 11)),
                dpi.point_by_dpi(QPoint(x + 11, int(y + 16.0))),
            )
            points = [tl, tr, tp]
            triangle = QPolygon(points)

        current_pen = painter.pen()
        current_brush = painter.brush()
        painter.setPen(Qt.NoPen)
        painter.setBrush(brush)
        painter.drawPolygon(triangle)
        painter.setPen(current_pen)
        painter.setBrush(current_brush)

    def _draw_icon(self, painter: QPainter, x: int, y: int):
        """Handle the painting of the icon.

        Args:
            painter: Painter instance used to handle the painting operation.
            x: X position for the icon.
            y: Y position for the icon.
        """

        if not self._icon:
            return
        self._icon.paint(painter, x, y, dpi.dpi_scale(16), dpi.dpi_scale(16))


class Accordion(QScrollArea):
    """Class that represents an accordion widget that can contain multiple
    accordion item groups.
    """

    itemCollapsed = Signal(AccordionItem)
    itemMenuRequested = Signal(AccordionItem)
    itemDragFailed = Signal(AccordionItem)
    itemsReordered = Signal()

    class Style(enum.IntEnum):
        """Enumerator class that defines the different types of accordion
        styles available.
        """

        Boxed = 1
        Rounded = 2
        Square = 3
        Maya = 4

    class DragDrop(enum.IntEnum):
        """Enumerator class that defines drag drop operations for
        accordion items.
        """

        NoDragDrop = 0
        InternalMove = 1

    def __init__(self, stretch_layout: bool = True, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._rollout_style = (
            Accordion.Style.Rounded if not dcc.is_maya() else Accordion.Style.Maya
        )
        self._drag_drop_mode = Accordion.DragDrop.NoDragDrop
        self._scrolling = False
        self._scroll_init_y = 0
        self._scroll_init_val = 0
        self._item_class = AccordionItem

        self.setFrameShape(QScrollArea.NoFrame)
        self.setAutoFillBackground(False)
        self.setWidgetResizable(True)
        self.setMouseTracking(True)
        self.verticalScrollBar().setMaximumWidth(10)

        widget = QWidget(self)
        layout = QVBoxLayout()
        layout.setSpacing(dpi.dpi_scale(2))
        layout.setContentsMargins(*dpi.margins_dpi_scale(2, 2, 2, 2))
        if stretch_layout:
            layout.addStretch(1)
        widget.setLayout(layout)
        self.setWidget(widget)

    @property
    def drag_drop_mode(self) -> Accordion.DragDrop:
        """The drag and drop mode of this accordion."""

        return self._drag_drop_mode

    @drag_drop_mode.setter
    def drag_drop_mode(self, value: Accordion.DragDrop):
        """Set the drag and drop mode of this accordion."""

        self._drag_drop_mode = value
        for item in self.findChildren(AccordionItem):
            item.drag_drop_mode = self._drag_drop_mode

    @property
    def rollout_style(self) -> Accordion.Style:
        """Getter method that returns the rollout style of this accordion.

        :return: accordion style.
        """

        return self._rollout_style

    @rollout_style.setter
    def rollout_style(self, value: Accordion.Style):
        """The rollout style of this accordion."""

        self._rollout_style = value
        for item in self.findChildren(AccordionItem):
            item.rollout_style = self._rollout_style

    @property
    def item_class(self) -> type:
        """The item class used by this accordion."""

        return self._item_class

    @item_class.setter
    def item_class(self, value: type):
        """Set the item class used by this accordion."""

        self._item_class = value

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Override base QScrollArea eventFilter function.

        Args:
            watched: Widget that is being watched.
            event: The Qt event to be filtered.

        Returns:
            True if the event was handled and should not be processed further,
            False otherwise.
        """

        if event.type() == QEvent.MouseButtonPress:
            # noinspection PyTypeChecker
            super().mousePressEvent(event)
            return True
        elif event.type() == QEvent.MouseMove:
            # noinspection PyTypeChecker
            super().mouseMoveEvent(event)
            return True
        elif event.type() == QEvent.MouseButtonRelease:
            # noinspection PyTypeChecker
            super().mouseReleaseEvent(event)
            return True
        return False

    def enterEvent(self, event: QEvent):
        """Override base QScrollArea enterEvent function.

        Args:
            event: The Qt event that triggered this method.
        """

        if self.can_scroll():
            QApplication.setOverrideCursor(Qt.OpenHandCursor)

    def leaveEvent(self, event: QEvent):
        """Override base QScrollArea leaveEvent function.

        Args:
            event: The Qt event that triggered this method.
        """

        if self.can_scroll():
            QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Override base QScrollArea mouseMoveEvent function.

        Args:
            event: The Qt mouse move event that triggered this method.
        """

        if self._scrolling:
            vertical_scrollbar = self.verticalScrollBar()
            smax = vertical_scrollbar.maximum()
            # Calculate the distance moved for the mouse point
            dy = event.globalY() - self._scroll_init_y
            # Calculate the percentage that is on the scroll bar
            scrollbar_value = smax * (dy / float(vertical_scrollbar.height()))
            # Calculate the new value
            vertical_scrollbar.setValue(int(self._scroll_init_val - scrollbar_value))
        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        """Override base QScrollArea mousePressEvent function.

        Args:
            event: The Qt mouse press event that triggered this method.
        """

        if event.button() == Qt.LeftButton and self.can_scroll():
            self._scrolling = True
            self._scroll_init_y = event.globalY()
            self._scroll_init_val = self.verticalScrollBar().value()
            QApplication.setOverrideCursor(Qt.ClosedHandCursor)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Override base QScrollArea mouseReleaseEvent function.

        Args:
            event: The Qt mouse release event that triggered this method.
        """

        if self._scrolling:
            QApplication.restoreOverrideCursor()
        self._scrolling = False
        self._scroll_init_y = 0
        self._scroll_init_val = 0
        event.accept()

    def can_scroll(self) -> bool:
        """Return whether accordion item scroll bar can roll.

        Returns:
            True if the scroll bar can roll; False otherwise.
        """

        return self.verticalScrollBar().maximum() > 0

    def count(self) -> int:
        """Return the total amount of items in the accordion.

        Returns:
            The total amount of items in the accordion.
        """

        return self.widget().layout().count() - -1

    def set_spacing(self, value: int):
        """Sets the spacing between items.

        Args:
            value: The spacing value to set in pixels.
        """

        self.widget().layout().setSpacing(value)

    def add_item(
        self,
        title: str,
        widget: QWidget,
        collapsible: bool = True,
        collapsed: bool = False,
        icon: QIcon | None = None,
    ) -> AccordionItem | None:
        """Add a new accordion item.

        Args:
            title: The title of the accordion item.
            widget: The widget to wrap inside the accordion item.
            collapsible: Whether the accordion item can be collapsed.
            collapsed: Whether the accordion item is collapsed by default.
            icon: Optional icon for the accordion item.

        Returns:
            The newly created `AccordionItem` instance; None if an error
                occurred.
        """

        self.setUpdatesEnabled(False)
        try:
            item = self._item_class(self, title, widget, icon=icon)
            item.rollout_style = self.rollout_style
            item.drag_drop_mode = self.drag_drop_mode
            item.collapsible = collapsible
            layout = self.widget().layout()
            # noinspection PyUnresolvedReferences
            layout.insertWidget(layout.count() - 1, item)
            # noinspection PyUnresolvedReferences
            layout.setStretchFactor(item, 0)
            if collapsed:
                item.set_collapsed(state=collapsed)
            self.setUpdatesEnabled(True)
            return item
        except Exception as err:
            self.setUpdatesEnabled(True)
            logger.exception(f"Error while adding item to accordion: {err}")
            return None

    def clear(self):
        """Clears all accordion items."""

        self.setUpdatesEnabled(False)
        try:
            layout = self.widget().layout()
            while layout.count() > 1:
                item = layout.itemAt(0)

                # First we remove the item from the layout
                w = item.widget()
                layout.removeItem(item)

                # Second, close the widget and delete it
                w.close()
                w.deleteLater()
            self.setUpdatesEnabled(True)
        except Exception:
            self.setUpdatesEnabled(True)

    def index_of(self, widget: QWidget) -> int:
        """Searches for the widget (without including child layouts) and
        returns the index of widget or -1 if the widget is not found.

        Args:
            widget: The widget to find the index of.

        Returns:
            The index of the widget in the accordion layout, or -1
            if not found.
        """

        layout = self.widget().layout()
        # noinspection PyTypeChecker
        for index in range(layout.count()):
            # noinspection PyUnresolvedReferences
            if layout.itemAt(index).widget().widget() == widget:
                return index

        return -1

    def is_box_mode(self) -> bool:
        """Returns whether box rollout style is enabled.

        Returns:
            True if the box rollout style is enabled; False otherwise.
        """

        return self._rollout_style == Accordion.Style.Maya

    def set_box_mode(self, flag: bool):
        """Sets whether box rollout style or rounded rollout style are enabled.

        Args:
            flag: True to enable boxed rollout style, False to enable
                rounded rollout style.
        """

        if flag:
            self._rollout_style = Accordion.Style.Boxed
        else:
            self._rollout_style = Accordion.Style.Rounded

    def item_at(self, index: int) -> AccordionItem | None:
        """Returns the accordion item at the given index.

        Args:
            index: Accordion item layout index to find and remove.

        Returns:
            The accordion item that was removed, or None if not found.
        """

        found_layout_item = None
        layout = self.widget().layout()
        if 0 <= index < layout.count() - 1:
            found_layout_item = layout.itemAt(index).widget()

        return found_layout_item

    def move_item_down(self, index: int):
        """Move the accordion at the given index down by one.

        :param index: Accordion item layout index.
        """

        layout = self.widget().layout()
        if (layout.count() - 1) > (index + 1):
            widget = layout.takeAt(index).widget()
            # noinspection PyUnresolvedReferences
            layout.insertWidget(index + 1, widget)

    def move_item_up(self, index: int):
        """Moves the accordion item at the given index up by one position.

        Args:
            index: Accordion item layout index to move.
        """

        if index > 0:
            layout = self.widget().layout()
            widget = layout.takeAt(index).widget()
            # noinspection PyUnresolvedReferences
            layout.insertWidget(index - 1, widget)

    def take_at(self, index: int) -> AccordionItem | None:
        """Returns the accordion item at the given index and removes it.

        Args:
            index: Accordion item layout index to find item of.

        Returns:
            The accordion item at the specified index, or None if not found.
        """

        self.setUpdatesEnabled(False)
        try:
            layout = self.widget().layout()
            widget = None
            if 0 < index < layout.count() - 1:
                item = layout.itemAt(index)
                widget = item.widget()
                layout.removeItem(item)
                widget.close()
            self.setUpdatesEnabled(True)
            return widget
        except Exception:
            self.setUpdatesEnabled(True)
        return None

    def widget_at(self, index: int) -> QWidget | None:
        """Return the accordion item wrapped widget at the given index.

        Args:
            index: The accordion item layout index to find the widget of.

        Returns:
            The widget instance at the specified index, or None if not found.
        """

        item = self.item_at(index)
        if item:
            return item.widget
        return None

    def emit_item_collapsed(self, item: AccordionItem):
        """Emit `itemCollapsed` signal with the given item.

        Args:
            item: item to send with the signal.
        """

        if not self.signalsBlocked():
            self.itemCollapsed.emit(item)

    def emit_item_menu_requested(self, item: AccordionItem):
        """Emit `itemMenuRequested` signal with the given item.

        Args:
            item: Item to send with the signal.
        """

        if not self.signalsBlocked():
            self.itemMenuRequested.emit(item)

    def emit_item_drag_failed(self, item: AccordionItem):
        """Emit `itemDragFailed` signal with the given item.

        Args:
            item: item to send with the signal.
        """

        if not self.signalsBlocked():
            self.itemDragFailed.emit(item)

    def emit_items_reordered(self):
        """Emit `itemsReordered` signal with the given item."""

        if not self.signalsBlocked():
            self.itemsReordered.emit()
