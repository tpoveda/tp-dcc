from __future__ import annotations

import typing
from typing import Union
from functools import partial

from overrides import override

from tp.common.qt import api as qt
from tp.preferences.interfaces import noddle

if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.graph.core.node import Node


class GraphicsNode(qt.QGraphicsItem):

    FONT_NAME: str | None = None
    FONT_SIZE: int | None = None
    TEXT_ZOOM_OUT_LIMIT = 2

    def __init__(self, node: Node, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        if GraphicsNode.FONT_NAME is None or GraphicsNode.FONT_SIZE is None:
            prefs = noddle.noddle_interface()
            GraphicsNode.FONT_NAME, GraphicsNode.FONT_SIZE = prefs.builder_node_title_font()

        self._node = node
        self._was_moved = False

        self._width = self.node.MIN_WIDTH
        self._height = self.node.MIN_HEIGHT
        self._one_side_horizontal_padding = 20.0
        self._edge_roundness = 10.0
        self._edge_padding = 10.0
        self._title_horizontal_padding = 4.0
        self._title_vertical_padding = 4.0
        self._lower_padding = 8.0

        self._title_color = qt.Qt.white
        self._title_font = qt.QFont(GraphicsNode.FONT_NAME, GraphicsNode.FONT_SIZE)
        self._title_font.setBold(True)

        self._pen_default = qt.QPen(qt.QColor('#7F000000'))
        self._pen_selected = qt.QPen(qt.QColor('#FFA637'))
        self._brush_background = qt.QBrush(qt.QColor('#E3212121'))
        self._brush_title = qt.QBrush(self._title_color)

        self._setup_ui()

    @property
    def node(self) -> Node:
        return self._node

    @property
    def title(self) -> str:
        return self._title_item.toPlainText()

    @title.setter
    def title(self, value: str):
        self._title_item.setPlainText(value)

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int):
        self._width = value

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int):
        self._height = value

    @property
    def title_width(self) -> float:
        return self._title_item.width

    @property
    def title_height(self) -> float:
        return self._title_item.height

    @property
    def title_color(self) -> qt.QColor:
        return qt.QColor(self.node.TITLE_COLOR) if not isinstance(
            self.node.TITLE_COLOR, qt.QColor) else self.node.TITLE_COLOR

    @property
    def title_item(self) -> GraphicsNodeTitle:
        return self._title_item

    @property
    def edge_roundness(self) -> float:
        return self._edge_roundness

    @property
    def edge_padding(self) -> float:
        return self._edge_padding

    @property
    def lower_padding(self) -> float:
        return self._lower_padding

    @property
    def title_horizontal_padding(self) -> float:
        return self._title_horizontal_padding

    @property
    def title_vertical_padding(self) -> float:
        return self._title_vertical_padding

    @property
    def one_side_horizontal_padding(self) -> float:
        return self._one_side_horizontal_padding

    @override
    def boundingRect(self) -> qt.QRectF:
        return qt.QRectF(0, 0, self.width, self.height).normalized()

    @override
    def mouseMoveEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)
        for node in self.scene().scene.selected_nodes:
            node.update_connected_edges()
        self._was_moved = True

    @override
    def mouseReleaseEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if self._was_moved:
            self._was_moved = False
            self.node.scene.history.store_history('Node moved', set_modified=True)

    @override
    def paint(
            self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
            widget: Union[qt.QWidget, None] = ...) -> None:

        self._title_item.setVisible(self.node.scene.view.zoom > self.TEXT_ZOOM_OUT_LIMIT)

        # Title
        path_title = qt.QPainterPath()
        path_title.setFillRule(qt.Qt.WindingFill)
        path_title.addRoundedRect(0, 0, self.width, self.title_height, self._edge_roundness, self._edge_roundness)
        path_title.addRect(0, self.title_height - self._edge_roundness, self._edge_roundness, self._edge_roundness)
        path_title.addRect(
            self.width - self._edge_roundness, self.title_height - self._edge_roundness,
            self._edge_roundness, self._edge_roundness)
        painter.setPen(qt.Qt.NoPen)
        painter.setBrush(self._brush_title)
        painter.drawPath(path_title.simplified())

        # Content
        path_content = qt.QPainterPath()
        path_content.setFillRule(qt.Qt.WindingFill)
        path_content.addRoundedRect(
            0, self.title_height, self.width, self.height - self.title_height,
            self._edge_roundness, self._edge_roundness)
        path_content.addRect(0, self.title_height, self._edge_roundness, self._edge_roundness)
        path_content.addRect(
            self.width - self._edge_roundness, self.title_height, self._edge_roundness, self._edge_roundness)
        painter.setPen(qt.Qt.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(path_content.simplified())

        # Outline
        # TODO: Paint prominent outline if exec input is connected
        path_outline = qt.QPainterPath()
        path_outline.addRoundedRect(
            -1, -1, self.width + 2, self.height + 2, self._edge_roundness, self._edge_roundness)
        painter.setPen(self._pen_default if not self.isSelected() else self._pen_selected)
        painter.setBrush(qt.Qt.NoBrush)
        painter.drawPath(path_outline.simplified())

    def _setup_ui(self):
        """
        Internal function that creates graphics node widgets.
        """

        self.setFlag(qt.QGraphicsItem.ItemIsSelectable)
        self.setFlag(qt.QGraphicsItem.ItemIsMovable)

        self._setup_title()
        self._setup_content()

    def _setup_title(self):
        """
        Internal function that setup graphics node title.
        """

        self._title_item = GraphicsNodeTitle(self, is_editable=self.node.TITLE_EDITABLE)
        self._title_item.setDefaultTextColor(qt.Qt.black)
        self._title_item.setFont(self._title_font)
        self._title_item.setPos(self._title_horizontal_padding, 0)

    def _setup_content(self):
        """
        Internal function that setup graphics node content.
        """

        pass


class GraphicsNodeTitle(qt.QGraphicsTextItem):

    def __init__(self, graphics_node: GraphicsNode, text: str = '', is_editable: bool = False):
        super().__init__(text, graphics_node)

        self._graphics_node = graphics_node
        self._is_editable = is_editable

    @property
    def width(self) -> float:
        return self.boundingRect().width()

    @property
    def height(self) -> float:
        return self.boundingRect().height()

    def edit(self):
        """
        Enables title edit mode.
        """

        def _apply_edit(_new_text):
            _new_text = _new_text.strip()
            if _new_text == self._graphics_node.title:
                return
            self._graphics_node.node.signals.titleEdited.emit(_new_text)

        line_edit = qt.QLineEdit()
        line_edit_proxy = qt.QGraphicsProxyWidget(self)
        line_edit_proxy.setWidget(line_edit)
        line_edit.editingFinished.connect(partial(_apply_edit, line_edit.text()))
        line_edit.editingFinished.connect(line_edit_proxy.deleteLater)
        line_edit.setFont(self.font())
        line_edit.setMaximumWidth(self._graphics_node.width)
        line_edit.setText(self.toPlainText())
        line_edit.setFocus(qt.Qt.MouseFocusReason)
