from __future__ import annotations

import typing
from typing import Union, Any

from overrides import override

from tp.common.qt import api as qt
from tp.common.python import helpers
from tp.preferences.interfaces import noddle

from tp.common.nodegraph.core import consts
from tp.common.nodegraph.painters import node as node_painters

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.node import BaseNode
    from tp.common.nodegraph.graphics.view import GraphicsView
    from tp.common.nodegraph.graphics.scene import GraphicsScene


class BaseGraphicsNode(qt.QGraphicsItem):

    FONT_NAME: str | None = None
    FONT_SIZE: int | None = None

    def __init__(self, node: BaseNode, name: str = 'node', parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        if GraphicsNode.FONT_NAME is None or GraphicsNode.FONT_SIZE is None:
            prefs = noddle.noddle_interface()
            GraphicsNode.FONT_NAME, GraphicsNode.FONT_SIZE = prefs.builder_node_title_font()

        self._node = node
        self._width = self.node.MIN_WIDTH
        self._height = self.node.MIN_HEIGHT

        self._one_side_horizontal_padding = 20.0
        self._edge_roundness = 10.0
        self._edge_padding = 10.0
        self._lower_padding = 8.0

        self._properties = {
            'id': None,
            'type': 'BaseGraphicsNode',
            'name': name.strip(),
            'color': consts.NODE_COLOR,
            'border_color': consts.NODE_BORDER_COLOR,
            'text_color': consts.NODE_TEXT_COLOR,
            'header_color': consts.NODE_HEADER_COLOR,
            'selected': False,
            'disabled': False,
            'visible': False,
            'layout_direction': consts.LayoutDirection.Horizontal.value
        }

        self._setup_ui()

    def __repr__(self):
        return '{}.{}(\'{}\')'.format(self.__module__, self.__class__.__name__, self.name)

    @property
    def name(self):
        return self._properties['name']

    @name.setter
    def name(self, value):
        self._properties['name'] = value
        self.setToolTip('node: {}'.format(value))

    @property
    def properties(self) -> dict[str, Any]:
        props = {'width': self.width, 'height': self.height, 'pos': self.xy_pos}
        props.update(self._properties)

        return props

    @property
    def node(self) -> BaseNode:
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
    def size(self) -> tuple[int, int]:
        return self._width, self._height

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
    def one_side_horizontal_padding(self) -> float:
        return self._one_side_horizontal_padding

    @property
    def disabled(self):
        return self._properties['disabled']

    @disabled.setter
    def disabled(self, flag):
        self._properties['disabled'] = flag

    @property
    def selected(self):
        if self._properties['selected'] != self.isSelected():
            self._properties['selected'] = self.isSelected()
        return self._properties['selected']

    @selected.setter
    def selected(self, flag=False):
        self.setSelected(flag)

    @property
    def visible(self):
        return self._properties['visible']

    @visible.setter
    def visible(self, visible=False):
        self._properties['visible'] = visible
        self.setVisible(visible)

    @override
    def boundingRect(self) -> qt.QRectF:
        # return qt.QRectF(0.0, 0.0, self.width, self.height)
        return qt.QRectF(0.0, 0.0, self.width, self.height).normalized()

    @override
    def mousePressEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
        self._properties['selected'] = True
        super().mousePressEvent(event)

    @override
    def setSelected(self, selected: bool) -> None:
        self._properties['selected'] = selected
        super().setSelected(selected)

    def viewer(self) -> GraphicsView | None:
        """
        Returns graph viewer this node belongs to.

        :return: node graph viewer.
        :rtype: GraphicsView or None
        """

        current_scene: GraphicsScene = self.scene()
        return current_scene.viewer() if current_scene else None

    def pre_init(self, graph_view: GraphicsView, pos: tuple[int, int] | None = None):
        """
        Called beefore node has been added into the scene.

        :param GraphicsView graph_view: graph viewer.
        :param tuple[int, int] pos: cursor position where node was added into the viewer.
        """

        pass

    def post_init(self, graph_view: GraphicsView, pos: tuple[int, int] | None = None):
        """
        Called after node has been added into the scene.

        :param GraphicsView graph_view: graph viewer.
        :param tuple[int, int] pos: cursor position where node was added into the viewer.
        """

        pass

    def delete(self):
        """
        Removes node view from the scene.
        """

        if self.scene():
            self.scene().removeItem(self)

    def _setup_ui(self):
        """
        Internal function that creates graphics node widgets.
        """

        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        # self.setCacheMode(consts.ITEM_CACHE_MODE)
        self.setZValue(consts.NODE_Z_VALUE)


class GraphicsNode(BaseGraphicsNode):

    TEXT_ZOOM_OUT_LIMIT = 2

    def __init__(self, node: BaseNode, parent: qt.QWidget | None = None):
        super().__init__(node, parent=parent)

        self._was_moved = False

        self._title_horizontal_padding = 4.0
        self._title_vertical_padding = 4.0

        self._title_color = qt.Qt.white
        self._title_font = qt.QFont(GraphicsNode.FONT_NAME, GraphicsNode.FONT_SIZE)
        self._title_font.setBold(True)

        self._setup_title()
        self._setup_content()

    @property
    def title(self) -> str:
        return self._title_item.toPlainText()

    @title.setter
    def title(self, value: str):
        old_height = self.title_height
        old_width = self.title_width
        self._title_item.setPlainText(value)
        new_width = self.title_width
        new_height = self.title_height
        if old_height != new_height or old_width != new_width:
            self.update_size()

    @property
    def title_width(self) -> float:
        return self._title_item.width

    @property
    def title_height(self) -> float:
        return self._title_item.height

    @property
    def title_horizontal_padding(self) -> float:
        return self._title_horizontal_padding

    @property
    def title_vertical_padding(self) -> float:
        return self._title_vertical_padding

    @property
    def title_color(self) -> qt.QColor:
        return qt.QColor(self.node.TITLE_COLOR) if not isinstance(
            self.node.TITLE_COLOR, qt.QColor) else self.node.TITLE_COLOR

    @property
    def title_item(self) -> GraphicsNodeTitle:
        return self._title_item

    @override
    def mouseMoveEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)
        self._was_moved = True

    @override
    def mouseReleaseEvent(self, event: qt.QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if self._was_moved:
            self._was_moved = False
            self.node.graph.history.store_history('Node moved', set_modified=True)

    @override
    def paint(
            self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
            widget: Union[qt.QWidget, None] = ...) -> None:

        node_painters.node_painter(self, painter, option, widget)

    def update_size(self):
        """
        Function that updates node graphics size.
        """

        self._recalculate_width()
        self._recalculate_height()
        self.update_socket_positions()
        self.update_connected_edges()

    def update_socket_positions(self):
        """
        Updates the position of the graphic sockets.
        """

        for node_socket in self.node.outputs + self.node.inputs:
            node_socket.update_positions()

    def update_connected_edges(self):
        """
        Updates the edges connected to this node.
        """

        for node_socket in self.node.inputs + self.node.outputs:
            node_socket.update_edges()

    def _setup_title(self):
        """
        Internal function that setup graphics node title.
        """

        self._title_item = GraphicsNodeTitle(self, is_editable=self.node.TITLE_EDITABLE)
        self._title_item.setDefaultTextColor(qt.Qt.white)
        self._title_item.setFont(self._title_font)
        self._title_item.setPos(self._title_horizontal_padding, 0)

    def _setup_content(self):
        """
        Internal function that setup graphics node content.
        """

        pass

    def _recalculate_width(self):
        """
        Internal function that recalculates and updates node graphics width.
        """

        # Labels max width
        input_widths = [input_socket.label_width() for input_socket in self.node.inputs] or [0, 0]
        output_widths = [output_socket.label_width() for output_socket in self.node.outputs] or [0, 0]

        max_label_width = max(input_widths + output_widths)

        # Calculate clamped title text width
        self.title_item.setTextWidth(-1)
        if self.title_width > self.node.MAX_TEXT_WIDTH:
            self.title_item.setTextWidth(self.node.MAX_TEXT_WIDTH)
            title_with_padding = self.node.MAX_TEXT_WIDTH + self.title_horizontal_padding * 2
        else:
            title_with_padding = self.title_width + self.title_horizontal_padding * 2

        # Use the max value between widths of label, allowed min width, clamped text width
        # Sockets on both sides or only one side
        if self.node.inputs and self.node.outputs:
            self.width = max(max_label_width * 2, self.node.MIN_WIDTH, int(title_with_padding))
        else:
            self.width = max(
                max_label_width + self.one_side_horizontal_padding, self.node.MIN_WIDTH, title_with_padding)

    def _recalculate_height(self):
        """
        Internal function that recalculates and updates node graphics height.
        """

        max_inputs = len(self.node.inputs) * self.node._socket_spacing
        max_outputs = len(self.node.outputs) * self.node._socket_spacing
        total_socket_height = max(max_inputs, max_outputs, self.node.MIN_HEIGHT)
        self.height = total_socket_height + self.title_height + self.lower_padding


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
        line_edit.editingFinished.connect(lambda: _apply_edit(line_edit.text()))
        line_edit.editingFinished.connect(line_edit_proxy.deleteLater)
        line_edit.setFont(self.font())
        line_edit.setMaximumWidth(self._graphics_node.width)
        line_edit.setText(self.toPlainText())
        line_edit.setFocus(qt.Qt.MouseFocusReason)
