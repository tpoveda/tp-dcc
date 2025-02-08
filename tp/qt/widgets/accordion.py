from __future__ import annotations

__author__ = "Tomi Poveda <tpoveda@thatsnomoon.com>"
__email__ = "tpoveda@thatsnomoon.com"
__copyright__ = "That's No Moon Entertainment Inc."
__maintainers__ = ["Tomi Poveda <tpoveda@thatsnomoon.com>"]

from typing import Any

import enum
import logging

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

logger = logging.getLogger(__name__)


class AccordionItem(QGroupBox):
    """
    Class that represents an expandable group that can contain multiple accordion item within it.
    Collapsible accordion widget similar to Maya Attribute Editor
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
        layout.setSpacing(0)
        layout.setContentsMargins(6, 12, 6, 6)
        layout.addWidget(widget)

        self.setAcceptDrops(True)
        self.setLayout(layout)
        self.setTitle(title)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_show_menu)

    @property
    def accordion_widget(self) -> Accordion:
        """
        Getter method that returns the accordion widget that contains this item.

        :return: accordion widget.
        """

        return self._accordion_widget

    @property
    def widget(self) -> QWidget:
        """
        Getter method that returns the widget wrapped by this accordion item.

        :return: widget.
        """

        return self._widget

    @property
    def rollout_style(self) -> Accordion.Style:
        """
        Getter method that returns the rollout style of this accordion item.

        :return: accordion style.
        """

        return self._rollout_style

    @rollout_style.setter
    def rollout_style(self, value: Accordion.Style):
        """
        Setter method that sets the rollout style of this accordion item.

        :param value: accordion style to set.
        """

        self._rollout_style = value

    @property
    def drag_drop_mode(self) -> Accordion.DragDrop:
        """
        Getter method that returns the drag and drop mode of this accordion item.

        :return: drag and drop mode.
        """

        return self._drag_drop_mode

    @drag_drop_mode.setter
    def drag_drop_mode(self, value: Accordion.DragDrop):
        """
        Setter method that sets the drag and drop mode of this accordion item.

        :param value: drag and drop mode to set.
        """

        self._drag_drop_mode = value

    @property
    def collapsible(self) -> bool:
        """
        Getter method that returns whether this accordion item is collapsible.

        :return: True if accordion item is collapsible; False otherwise.
        """

        return self._collapsible

    @collapsible.setter
    def collapsible(self, flag: bool):
        """
        Setter method that sets whether this accordion item is collapsible.

        :param flag: flag to set.
        """

        self._collapsible = flag

    def enterEvent(self, event: QEvent):
        """
        Overrides base QGroupBox enterEvent function.

        :param event: Qt event.
        """

        self.accordion_widget.leaveEvent(event)
        event.accept()

    def leaveEvent(self, event: QEvent):
        """
        Overrides base QGroupBox leaveEvent function.

        :param event: Qt event.
        """

        self.accordion_widget.enterEvent(event)
        event.accept()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Overrides base QGroupBox dragEnterEvent function.

        :param event: Qt drag enter event.
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
        """
        Overrides base QGroupBox dragMoveEvent function.

        :param event: Qt drag move event.
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
        """
        Overrides base QGroupBox dropEvent function.

        :param event: Qt drop event.
        """

        widget = event.source()
        layout = self.parent().layout()
        # noinspection PyUnresolvedReferences
        layout.insertWidget(layout.indexOf(self), widget)
        self._accordion_widget.emit_items_reordered()

    def mousePressEvent(self, event: QMouseEvent):
        """
        Overrides base QGroupBox mousePressEvent function.

        :param event: Qt mouse press event.
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
        """
        Overrides base QGroupBox mouseMoveEvent function.

        :param event: Qt mouse move event.
        """

        event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Overrides base QGroupBox mouseReleaseEvent function.

        :param event: Qt mouse release event.
        """

        if self._clicked and self.expand_collapse_rect().contains(event.pos()):
            self.toggle_collapsed()
            event.accept()
        else:
            event.ignore()
        self._clicked = False

    def paintEvent(self, event: QPaintEvent):
        """
        Overrides base QGroupBox paintEvent function.

        :param event: Qt paint event.
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
        _rect = 5

        if self.rollout_style == Accordion.Style.Rounded:
            header_color = QColor("#242424")
            background_color = QColor("#242424")
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(background_color))
            painter.drawRoundedRect(x, y, w, h - 1, _rect, _rect)
            path = QPainterPath()
            path.setFillRule(Qt.WindingFill)

            path.addRoundedRect(x + 1, y + 1, w - 1, 20, _rect, _rect)
            if not self.is_collapsed():
                path.addRect(x + 1, y + 16, w - 1, 5)
            painter.setBrush(QBrush(header_color))
            painter.drawPath(path.simplified())
            painter.restore()

            painter.drawText(
                x + 33 if not self._icon else 40,
                y + 3,
                w,
                16,
                Qt.AlignLeft | Qt.AlignTop,
                self.title(),
            )
            self._draw_triangle(painter, x, y)
            self._draw_icon(painter, x + 22, y + 3)

        elif self.rollout_style == Accordion.Style.Square:
            painter.drawText(
                x + 33 if not self._icon else 40,
                y + 3,
                w,
                16,
                Qt.AlignLeft | Qt.AlignTop,
                self.title(),
            )
            self._draw_triangle(painter, x, y)
            self._draw_icon(painter, x + 22, y + 3)
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.15)
            painter.setPen(pen)
            painter.drawRect(x + 1, y + 1, w - 1, h - 1)
            pen.setColor(self.palette().color(QPalette.Shadow))
            painter.setPen(pen)
        elif self.rollout_style == Accordion.Style.Maya:
            painter.drawText(
                x + 33 if not self._icon else 40,
                y + 3,
                w,
                16,
                Qt.AlignLeft | Qt.AlignTop,
                self.title(),
            )
            painter.setRenderHint(QPainter.Antialiasing, False)
            self._draw_triangle(painter, x, y)
            self._draw_icon(painter, x + 22, y + 3)
            header_height = 20
            header_rect = QRect(x + 1, y + 1, w - 1, header_height)
            header_rect_shadow = QRect(x - 1, y - 1, w + 1, header_height + 2)
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.4)
            painter.setPen(Qt.NoPen)
            painter.drawRect(header_rect)
            painter.fillRect(header_rect, QColor(255, 255, 255, 18))
            pen.setColor(self.palette().color(QPalette.Dark))
            painter.setPen(pen)
            painter.drawRect(header_rect_shadow)
            if not self.is_collapsed():
                offset = header_height + 3
                body_rect = QRect(x, y + offset, w, h - offset)
                painter.drawRect(body_rect)
        elif self.rollout_style == Accordion.Style.Boxed:
            if self.is_collapsed():
                a_rect = QRect(x + 1, y + 9, w - 1, 4)
                b_rect = QRect(x, y + 8, w - 1, 4)
                text = "+"
            else:
                a_rect = QRect(x + 1, y + 9, w - 1, h - 9)
                b_rect = QRect(x, y + 8, w - 1, h - 9)
                text = "-"

            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.6)
            painter.setPen(pen)
            painter.drawRect(a_rect)
            painter.drawRect(b_rect)
            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.setBrush(self.palette().color(QPalette.Window).darker(120))
            painter.drawRect(x + 10, y + 1, w - 20, 16)
            painter.drawText(
                x + 16, y + 1, w - 32, 16, Qt.AlignLeft | Qt.AlignVCenter, text
            )
            painter.drawText(x + 10, y + 1, w - 20, 16, Qt.AlignCenter, self.title())

        if self.drag_drop_mode:
            rect = self.drag_drop_rect()
            _layout = rect.left()
            _rect = rect.right()
            center_y = rect.center().y()
            for y in (center_y - 3, center_y, center_y + 3):
                painter.drawLine(_layout, y, _rect, y)

        painter.end()

    def custom_data(self, key: str, default: Any = None) -> Any:
        """
        Returns a custom pointer to information stored with this item.

        :param key: data key to retrieve.
        :param default: default value.
        :return: custom data.
        """

        return self._custom_data.get(str(key), default)

    def set_custom_data(self, key: str, value: Any):
        """
        Sets a custom pointer to information stored on this item.

        :param key: data key to set.
        :param value: data value to set.
        """

        self._custom_data[str(key)] = value

    def drag_drop_rect(self) -> QRect:
        """
        Returns default drag and drop rectangle.

        :return: drag and drop rectangle.
        """

        return QRect(25, 7, 10, 6)

    def expand_collapse_rect(self) -> QRect:
        """
        Returns the expanded drag and drop rectangle.

        :return: expanded drag and drop rectangle.
        """

        return QRect(0, 0, self.width(), 20)

    def is_collapsed(self) -> bool:
        """
        Returns whether accordion is collapsed.

        :return: True if accordion is collapsed; False otherwise.
        """

        return self._collapsed

    def set_collapsed(self, state: bool = True):
        """
        Sets whether accordion is collapsed.

        :param state: True to collapse accordion; False to expand it.
        """

        if self.collapsible:
            accord = self.accordion_widget
            accord.setUpdatesEnabled(True)
            self._collapsed = state
            if state:
                self.setMinimumHeight(22)
                self.setMaximumHeight(22)
                self.widget.setVisible(False)
            else:
                self.setMinimumHeight(0)
                self.setMaximumHeight(1000000)
                self.widget.setVisible(True)

            self._accordion_widget.emit_item_collapsed(self)
            accord.setUpdatesEnabled(True)

    def toggle_collapsed(self) -> bool:
        """
        Toggles current accordion collapse status.

        :return: True if accordion was collapsed; False otherwise.
        """

        collapsed_state = not self.is_collapsed()
        self.set_collapsed(collapsed_state)
        return collapsed_state

    def _on_show_menu(self):
        """
        Internal function that requests to show the current accordion widget item contextual menu.
        """

        if QRect(0, 0, self.width(), 20).contains(self.mapFromGlobal(QCursor.pos())):
            self._accordion_widget.emit_item_menu_requested(self)

    def _draw_triangle(self, painter: QPainter, x: int, y: int):
        """
        Internal function that handles the painting of the triangle icon.

        :param painter: painter instance used to handle the painting operation.
        :param x: X position.
        :param y: Y position.
        """

        if self.rollout_style == Accordion.Style.Maya:
            brush = QBrush(QColor(255, 0, 0, 160), Qt.SolidPattern)
        else:
            brush = QBrush(QColor(255, 255, 255, 160), Qt.SolidPattern)
        if not self.is_collapsed():
            tl, tr, tp = (
                QPoint(x + 9, y + 8),
                QPoint(x + 19, y + 8),
                QPoint(x + 14, int(y + 13.0)),
            )
            points = [tl, tr, tp]
            triangle = QPolygon(points)
        else:
            tl, tr, tp = (
                QPoint(x + 11, y + 6),
                QPoint(x + 16, y + 11),
                QPoint(x + 11, int(y + 16.0)),
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
        """
        Internal function that handles the painting of the icon.

        :param painter: painter instance used to handle the painting operation.
        :param x: X position.
        :param y: Y position.
        """

        if not self._icon:
            return
        self._icon.paint(painter, x, y, 16, 16)


class Accordion(QScrollArea):
    """
    Class that represents an accordion widget that can contain multiple accordion item groups.
    """

    itemCollapsed = Signal(AccordionItem)
    itemMenuRequested = Signal(AccordionItem)
    itemDragFailed = Signal(AccordionItem)
    itemsReordered = Signal()

    class Style(enum.IntEnum):
        """
        Enumerator class that defines the different types of accordion styles available.
        """

        Boxed = 1
        Rounded = 2
        Square = 3
        Maya = 4

    class DragDrop(enum.IntEnum):
        """
        Enumerator class that defines drag drop operations for accordion items.
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
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)
        if stretch_layout:
            layout.addStretch(1)
        widget.setLayout(layout)
        self.setWidget(widget)

    @property
    def drag_drop_mode(self) -> Accordion.DragDrop:
        """
        Getter method that returns the drag and drop mode of this accordion.

        :return: drag and drop mode.
        """

        return self._drag_drop_mode

    @drag_drop_mode.setter
    def drag_drop_mode(self, value: Accordion.DragDrop):
        """
        Setter method that sets the drag and drop mode of this accordion.

        :param value: drag and drop mode to set.
        """

        self._drag_drop_mode = value
        for item in self.findChildren(AccordionItem):
            item.drag_drop_mode = self._drag_drop_mode

    @property
    def rollout_style(self) -> Accordion.Style:
        """
        Getter method that returns the rollout style of this accordion.

        :return: accordion style.
        """

        return self._rollout_style

    @rollout_style.setter
    def rollout_style(self, value: Accordion.Style):
        """
        Setter method that sets the rollout style of this accordion.

        :param value: accordion style to set.
        """

        self._rollout_style = value
        for item in self.findChildren(AccordionItem):
            item.rollout_style = self._rollout_style

    @property
    def item_class(self) -> type:
        """
        Getter method that returns the item class used by this accordion.

        :return: item class.
        """

        return self._item_class

    @item_class.setter
    def item_class(self, value: type):
        """
        Setter method that sets the item class used by this accordion.

        :param value: item class to set.
        """

        self._item_class = value

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """
        Overrides base QScrollArea eventFilter function.

        :param watched: widget that is being watched.
        :param event: Qt event.
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
        """
        Overrides base QScrollArea enterEvent function.

        :param event: Qt event.
        """

        if self.can_scroll():
            QApplication.setOverrideCursor(Qt.OpenHandCursor)

    def leaveEvent(self, event: QEvent):
        """
        Overrides base QScrollArea leaveEvent function.

        :param event: Qt event.
        """

        if self.can_scroll():
            QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Overrides base QScrollArea mouseMoveEvent function.

        :param event: Qt mouse move event.
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
        """
        Overrides base QScrollArea mousePressEvent function.

        :param event: Qt mouse press event.
        """

        if event.button() == Qt.LeftButton and self.can_scroll():
            self._scrolling = True
            self._scroll_init_y = event.globalY()
            self._scroll_init_val = self.verticalScrollBar().value()
            QApplication.setOverrideCursor(Qt.ClosedHandCursor)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Overrides base QScrollArea mouseReleaseEvent function.

        :param event: Qt mouse release event.
        """

        if self._scrolling:
            QApplication.restoreOverrideCursor()
        self._scrolling = False
        self._scroll_init_y = 0
        self._scroll_init_val = 0
        event.accept()

    def can_scroll(self) -> bool:
        """
        Returns whether accordion item scroll bar can roll.

        :return: True if scroll bar can roll; False otherwise.
        """

        return self.verticalScrollBar().maximum() > 0

    def count(self) -> int:
        """
        Returns the total amount of items.

        :return: total amount of items.
        """

        return self.widget().layout().count() - -1

    def set_spacing(self, value: int):
        """
        Sets the spacing between items.

        :param value: spacing value.
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
        """
        Adds a new accordion item.

        :param title: item title.
        :param widget: widget wrapped by the new accordion item.
        :param collapsible: whether accordion item can be collapsed.
        :param collapsed: whether accordion item is collapsed by default.
        :param icon: optional accordion item icon.
        :return: AccordionItem or None: newly created accordion item.
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
            logger.exception(
                f"Error while adding item to accordion: {err}", exc_info=True
            )
            return None

    def clear(self):
        """
        Clears all accordion items.
        """

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
        """
        Searches for widget (without including child layouts) and returns the index of widget or -1 if the widget is
        not found.

        :param widget: widget to find accordion item of.
        :return: widget index.
        """

        layout = self.widget().layout()
        for index in range(layout.count()):
            # noinspection PyUnresolvedReferences
            if layout.itemAt(index).widget().widget() == widget:
                return index

        return -1

    def is_box_mode(self) -> bool:
        """
        Returns whether box rollout style is enabled.

        :return: True if box rollout style is enabled; False otherwise.
        """

        return self._rollout_style == Accordion.Style.Maya

    def set_box_mode(self, flag: bool):
        """
        Sets whether box rollout style or rounded rollout style are enabled.

        :param flag: True to enable boxed rollout style; False to enable rounded rollout style.
        """

        if flag:
            self._rollout_style = Accordion.Style.Boxed
        else:
            self._rollout_style = Accordion.Style.Rounded

    def item_at(self, index: int) -> AccordionItem | None:
        """
        Returns the accordion item at the given index.

        :param index: accordion item layout index to find item of.
        :return: found accordion item.
        """

        found_layout_item = None
        layout = self.widget().layout()
        if 0 <= index < layout.count() - 1:
            found_layout_item = layout.itemAt(index).widget()

        return found_layout_item

    def move_item_down(self, index: int):
        """
        Move the accordion at given index down by one.

        :param index: accordion item layout index.
        """

        layout = self.widget().layout()
        if (layout.count() - 1) > (index + 1):
            widget = layout.takeAt(index).widget()
            # noinspection PyUnresolvedReferences
            layout.insertWidget(index + 1, widget)

    def move_item_up(self, index: int):
        """Move the accordion at given index up by one.

        :param index: accordion item layout index.
        """

        if index > 0:
            layout = self.widget().layout()
            widget = layout.takeAt(index).widget()
            # noinspection PyUnresolvedReferences
            layout.insertWidget(index - 1, widget)

    def take_at(self, index: int) -> AccordionItem | None:
        """
        Returns the accordion item at the given index and removes it.

        :param index: accordion item layout index to find item of.

        :return: found accordion item.
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
        """
        Returns the accordion item wrapped widget at given index.

        :param index: accordion item layout index to find item of.
        :return: widget instance.
        """

        item = self.item_at(index)
        if item:
            return item.widget
        return None

    def emit_item_collapsed(self, item: AccordionItem):
        """
        Function that emits itemCollapsed signal with the given item.

        Args:
            item (AccordionItem): item to send with the signal.
        """

        if not self.signalsBlocked():
            self.itemCollapsed.emit(item)

    def emit_item_menu_requested(self, item: AccordionItem):
        """
        Function that emits itemMenuRequested signal with the given item.

        :param item: item to send with the signal.
        """

        if not self.signalsBlocked():
            self.itemMenuRequested.emit(item)

    def emit_item_drag_failed(self, item: AccordionItem):
        """
        Function that emits itemDragFailed signal with the given item.

        :param item: item to send with the signal.
        """

        if not self.signalsBlocked():
            self.itemDragFailed.emit(item)

    def emit_items_reordered(self):
        """
        Function that emits itemsReordered signal with the given item.
        """

        if not self.signalsBlocked():
            self.itemsReordered.emit()
