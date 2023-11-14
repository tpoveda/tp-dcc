from __future__ import annotations

import typing
from typing import Union
from functools import partial

from overrides import override

from tp.common.qt import api as qt
from tp.common.python import helpers
from tp.preferences.interfaces import noddle

from tp.tools.rig.noddle.builder.graph.core import consts
from tp.tools.rig.noddle.builder.graph.painters import node as node_painters

if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.graph.core.node import Node
    from tp.tools.rig.noddle.builder.graph.graphics.view import GraphicsView
    from tp.tools.rig.noddle.builder.graph.graphics.scene import GraphicsScene


class BaseGraphicsNode(qt.QGraphicsItem):

    FONT_NAME: str | None = None
    FONT_SIZE: int | None = None

    def __init__(self, node: Node, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        if GraphicsNode.FONT_NAME is None or GraphicsNode.FONT_SIZE is None:
            prefs = noddle.noddle_interface()
            GraphicsNode.FONT_NAME, GraphicsNode.FONT_SIZE = prefs.builder_node_title_font()

        self._node = node
        self._width = self.node.MIN_WIDTH
        self._height = self.node.MIN_HEIGHT

        self._properties = {
            'color': consts.NODE_COLOR,
            'border_color': consts.NODE_BORDER_COLOR,
            'text_color': consts.NODE_TEXT_COLOR,
            'header_color': consts.NODE_HEADER_COLOR
        }

        self._setup_ui()

    @property
    def node(self) -> Node:
        return self._node

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
    def properties(self) -> dict:
        props = dict(
            width=self.width,
            height=self.height,
            pos=self.xy_pos
        )
        props.update(self._properties)

        return props

    @property
    def size(self) -> tuple[int, int]:
        return self._width, self._height

    @property
    def xy_pos(self) -> list[float, float]:
        return [float(self.scenePos().x()), float(self.scenePos().y())]

    @xy_pos.setter
    def xy_pos(self, pos: list[float, float]):
        pos = pos or [0.0, 0.0]
        self.setPos(pos[0], pos[1])

    @property
    def color(self) -> tuple[int, int, int, int]:
        return self._properties['color']

    @color.setter
    def color(self, value: tuple[int, int, int, int]):
        self._properties['color'] = helpers.force_list(value)

    @property
    def text_color(self) -> tuple[int, int, int, int]:
        return self._properties['text_color']

    @text_color.setter
    def text_color(self, value: tuple[int, int, int, int]):
        self._properties['text_color'] = helpers.force_list(value)

    @property
    def border_color(self) -> tuple[int, int, int, int]:
        return self._properties['border_color']

    @border_color.setter
    def border_color(self, value: tuple[int, int, int, int]):
        self._properties['border_color'] = helpers.force_list(value)

    @property
    def header_color(self) -> tuple[int, int, int, int]:
        return self._properties['header_color']

    @header_color.setter
    def header_color(self, value: tuple[int, int, int, int]):
        self._properties['header_color'] = helpers.force_list(value)

    def viewer(self) -> GraphicsView | None:
        """
        Returns graph viewer this node belongs to.

        :return: node graph viewer.
        :rtype: GraphicsView or None
        """

        current_scene = self.scene()        # type: GraphicsScene
        return current_scene.viewer() if current_scene else None

    def _setup_ui(self):
        """
        Internal function that creates graphics node widgets.
        """

        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        # self.setCacheMode(consts.ITEM_CACHE_MODE)
        self.setZValue(consts.NODE_Z_VALUE)


class GraphicsNode(BaseGraphicsNode):

    TEXT_ZOOM_OUT_LIMIT = 2

    def __init__(self, node: Node, parent: qt.QWidget | None = None):
        super().__init__(node, parent=parent)

        self._was_moved = False

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

        self._setup_title()
        self._setup_content()

    @property
    def title(self) -> str:
        return self._title_item.toPlainText()

    @title.setter
    def title(self, value: str):
        self._title_item.setPlainText(value)

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

        node_painters.node_painter(self, painter, option, widget)

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
