from __future__ import annotations

import typing
from typing import Callable, Any

from Qt.QtCore import Qt, QRectF, QSizeF
from Qt.QtWidgets import (
    QWidget,
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsTextItem,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
)
from Qt.QtGui import (
    QFont,
    QFontMetrics,
    QColor,
    QPixmap,
    QPen,
    QPainter,
    QKeyEvent,
    QFocusEvent,
)


from . import uiconsts
from .port import PortView, CustomPortView
from ..painters.node import NodePainter
from ..core import consts, exceptions, datatypes
from ...python import paths

if typing.TYPE_CHECKING:
    from .graph import NodeGraphView
    from .scene import NodeGraphScene
    from ..widgets.node import AbstractNodeWidget


class AbstractNodeView(QGraphicsItem):
    """
    Abstract class that defines the interface for a node view.
    """

    def __init__(self, name: str = "node", parent: QGraphicsItem | None = None):
        super().__init__(parent=parent)

        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self.setCacheMode(uiconsts.ITEM_CACHE_MODE)
        self.setZValue(uiconsts.Z_VALUE_NODE)

        self._properties: dict[str, Any] = {
            "id": None,
            "node_type": "AbstractNodeView",
            "name": name.strip(),
            "color": (13, 18, 23, 255),
            "border_color": (255, 0, 0, 255),
            "text_color": (255, 255, 255, 180),
            "selected": False,
            "disabled": False,
            "visible": False,
            "layout_direction": consts.LayoutDirection.Horizontal.value,
        }
        self._width: int = uiconsts.NODE_WIDTH
        self._height: int = uiconsts.NODE_HEIGHT

    def __repr__(self) -> str:
        """
        Returns a string representation of the node view.

        :return: string representation.
        """

        return f'{self.__module__}.{self.__class__.__name__}("{self.name}")'

    @property
    def id(self) -> str:
        """
        Getter method that returns the id of the node view.

        :return: id of the node view.
        """

        return self._properties["id"]

    @id.setter
    def id(self, value: str):
        """
        Setter method that sets the id of the node view.

        :param value: id of the node view.
        """

        self._properties["id"] = value

    @property
    def node_type(self) -> str:
        """
        Getter method that returns the type of the node view.

        :return: type of the node view.
        """

        return self._properties["node_type"]

    @node_type.setter
    def node_type(self, value: str):
        """
        Setter method that sets the type of the node view.

        :param value: type of the node view.
        """

        self._properties["node_type"] = value

    @property
    def name(self) -> str:
        """
        Getter method that returns the name of the node view.

        :return: name of the node view.
        """

        return self._properties["name"]

    @name.setter
    def name(self, value: str):
        """
        Setter method that sets the name of the node view.

        :param value: name of the node view.
        """

        self._properties["name"] = value
        self.setToolTip(f"node: {value}")

    @property
    def color(self) -> tuple[int, int, int, int]:
        """
        Getter method that returns the color of the node view.

        :return: color of the node view.
        """

        return self._properties["color"]

    @color.setter
    def color(self, value: tuple[int, int, int, int]):
        """
        Setter method that sets the color of the node view.

        :param value: color of the node view.
        """

        self._properties["color"] = value

    @property
    def border_color(self) -> tuple[int, int, int, int]:
        """
        Getter method that returns the border color of the node view.

        :return: border color of the node view.
        """

        return self._properties["border_color"]

    @border_color.setter
    def border_color(self, value: tuple[int, int, int, int]):
        """
        Setter method that sets the border color of the node view.

        :param value: border color of the node view.
        """

        self._properties["border_color"] = value

    @property
    def text_color(self) -> tuple[int, int, int, int]:
        """
        Getter method that returns the text color of the node view.

        :return: text color of the node view.
        """

        return self._properties["text_color"]

    @text_color.setter
    def text_color(self, value: tuple[int, int, int, int]):
        """
        Setter method that sets the text color of the node view.

        :param value: text color of the node view.
        """

        self._properties["text_color"] = value

    @property
    def selected(self) -> bool:
        """
        Getter method that returns the selected state of the node view.

        :return: selected state of the node view.
        """

        self._properties["selected"] = self.isSelected()
        return self._properties["selected"]

    @selected.setter
    def selected(self, flag: bool):
        """
        Setter method that sets the selected state of the node view.

        :param flag: selected state of the node view.
        """

        self.setSelected(flag)

    @property
    def disabled(self) -> bool:
        """
        Getter method that returns the disabled state of the node view.

        :return: disabled state of the node view.
        """

        return self._properties["disabled"]

    @disabled.setter
    def disabled(self, flag: bool):
        """
        Setter method that sets the disabled state of the node view.

        :param flag: disabled state of the node view.
        """

        self._properties["disabled"] = flag

    @property
    def visible(self) -> bool:
        """
        Getter method that returns the visible state of the node view.

        :return: visible state of the node view.
        """

        return self._properties["visible"]

    @visible.setter
    def visible(self, flag: bool):
        """
        Setter method that sets the visible state of the node view.

        :param flag: visible state of the node view.
        """

        self.setVisible(flag)
        self._properties["visible"] = self.isVisible()

    @property
    def width(self) -> int:
        """
        Getter method that returns the width of the node view.

        :return: width of the node view.
        """

        return self._width

    @width.setter
    def width(self, value: int):
        """
        Setter method that sets the width of the node view.

        :param value: width of the node view.
        """

        self._width = value

    @property
    def height(self) -> int:
        """
        Getter method that returns the height of the node view.

        :return: height of the node view.
        """

        return self._height

    @height.setter
    def height(self, value: int):
        """
        Setter method that sets the height of the node view.

        :param value: height of the node view.
        """

        self._height = value

    @property
    def size(self) -> tuple[int, int]:
        """
        Getter method that returns the size of the node view.

        :return: size of the node view.
        """

        return self._width, self._height

    @property
    def xy_pos(self) -> tuple[float, float]:
        """
        Getter method that returns the position of the node view.

        :return: position of the node view.
        """

        return float(self.scenePos().x()), float(self.scenePos().y())

    @xy_pos.setter
    def xy_pos(self, value: tuple[float, float]):
        """
        Setter method that sets the position of the node view.

        :param value: position of the node view.
        """

        self.setPos(value[0], value[1])

    @property
    def layout_direction(self) -> int:
        """
        Getter method that returns the layout direction of the node view.

        :return: layout direction of the node view.
        """

        return self._properties["layout_direction"]

    @layout_direction.setter
    def layout_direction(self, value: int):
        """
        Setter method that sets the layout direction of the node view.

        :param value: layout direction of the node view.
        """

        self._properties["layout_direction"] = value
        self.draw()

    def boundingRect(self) -> QRectF:
        """
        Returns the bounding rectangle of the node view.

        :return: bounding rectangle.
        """

        return QRectF(0, 0, self._width, self._height)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Event triggered when the mouse is pressed over the node view.

        :param event: mouse event.
        """

        self._properties["selected"] = True
        super().mousePressEvent(event)

    def setSelected(self, selected: bool):
        """
        Sets the selected state of the node view.

        :param selected: selected state.
        """

        self._properties["selected"] = selected
        super().setSelected(selected)

    def pre_init(self, viewer: NodeGraphView, pos: tuple[float, float] | None = None):
        """
        Function that is called before the node is added into the graph scene.

        :param viewer: graph node view.
        :param pos: position where node was added.
        """

        pass

    def post_init(
        self,
        viewer: NodeGraphView | None = None,
        pos: tuple[float, float] | None = None,
    ):
        """
        Function that is called after the node is added into the graph scene.

        :param viewer: graph node view.
        :param pos: position where node was added.
        """

        pass

    def draw(self):
        """
        Forces the redraw of the node within the graph view.
        """

        pass

    def properties(self) -> dict[str, Any]:
        """
        Returns all node properties.

        :return: all node properties.
        """

        properties = self._properties.copy()
        properties.update(
            {"width": self.width, "height": self.height, "xy_pos": self.xy_pos}
        )

        return properties

    def viewer(self) -> NodeGraphView | None:
        """
        Returns the node graph view.

        :return: node graph view.
        """

        # noinspection PyTypeChecker
        scene: NodeGraphScene = self.scene()
        if not scene:
            return None

        return scene.viewer()

    def from_dict(self, data: dict[str, Any]):
        """
        Updates the view from given node data.

        :param data: node data to update from.
        """

        node_attributes = list(self.properties().keys())
        for name, value in data.items():
            if name not in node_attributes:
                continue
            setattr(self, name, value)

    def delete(self):
        """
        Deletes the node view from the scene.
        """

        # noinspection PyTypeChecker
        scene: NodeGraphScene = self.scene()
        if not scene:
            return None

        scene.removeItem(self)


class NodeView(AbstractNodeView):
    """
    Class that defines a node view.
    """

    def __init__(
        self,
        name: str = "node",
        parent: QGraphicsItem | None = None,
    ):
        super().__init__(name=name, parent=parent)

        self._default_icon_path = paths.canonical_path(
            "../resources/icons/node_base.png"
        )
        pixmap = QPixmap(self._default_icon_path)
        if pixmap.size().height() > uiconsts.NODE_ICON_SIZE:
            pixmap = pixmap.scaledToHeight(
                uiconsts.NODE_ICON_SIZE, Qt.SmoothTransformation
            )

        self._input_port_views: dict[PortView, QGraphicsTextItem] = {}
        self._output_port_views: dict[PortView, QGraphicsTextItem] = {}
        self._widgets: dict[str, AbstractNodeWidget] = {}
        self._proxy_mode: bool = False
        self._proxy_mode_bias: int = 70

        self._properties.update(
            {
                "title_font_name": "Roboto",
                "title_font_size": 10,
                "title_color": (30, 30, 30, 200),
                "title_text_color": (255, 255, 255, 180),
                "icon_path": self._default_icon_path,
            }
        )

        self._painter = NodePainter(self)
        self._icon_item = QGraphicsPixmapItem(pixmap, parent=self)
        self._icon_item.setTransformationMode(Qt.SmoothTransformation)
        self._title_item = NodeViewTitle(
            self,
            self.name,
            color=self.title_text_color,
            font_name=self.title_font_name,
            font_size=self.title_font_size,
        )
        self._x_item = NodeDisabledViewItem("DISABLED", parent=self)

    @AbstractNodeView.name.setter
    def name(self, value: str):
        """
        Setter method that sets the name of the node view.

        :param value: name of the node view.
        """

        AbstractNodeView.name.fset(self, value)
        if value == self._title_item.toPlainText():
            return
        self._title_item.setPlainText(value)
        if self.scene():
            self._align_label()
        self.update()

    @AbstractNodeView.layout_direction.setter
    def layout_direction(self, value: int):
        """
        Setter method that sets the layout direction of the node view.

        :param value: layout direction of the node view.
        """

        AbstractNodeView.layout_direction.fset(self, value)
        self.draw()

    @AbstractNodeView.width.setter
    def width(self, value: int):
        """
        Setter method that sets the width of the node view.

        :param value: width of the node view.
        """

        w, _ = self.calculate_size()
        width = value if value > w else w
        AbstractNodeView.width.fset(self, width)

    @AbstractNodeView.height.setter
    def height(self, value: int):
        """
        Setter method that sets the height of the node view.

        :param value: height of the node view.
        """

        _, h = self.calculate_size()
        # TODO: Define minimum node width in constants.
        height = 70 if h < 70 else h
        height = height if height > h else h
        AbstractNodeView.height.fset(self, height)

    @AbstractNodeView.disabled.setter
    def disabled(self, flag: bool):
        """
        Setter method that sets the disabled state of the node view.

        :param flag: disabled state of the node view.
        """

        AbstractNodeView.disabled.fset(self, flag)
        for property_widget in self._widgets.values():
            property_widget.widget().setDisabled(flag)
        self._update_tooltip_state(flag)
        self._x_item.setVisible(flag)

    @AbstractNodeView.selected.setter
    def selected(self, flag: bool):
        """
        Setter method that sets the selected state of the node view.

        :param flag: selected state of the node view.
        """

        AbstractNodeView.selected.fset(self, flag)
        if flag:
            self.highlight_connectors()

    @AbstractNodeView.color.setter
    def color(self, value: tuple[int, int, int, int]):
        """
        Setter method that sets the color of the node view.

        :param value: color of the node view.
        """

        AbstractNodeView.color.fset(self, value)
        if self.scene():
            self.scene().update()
        self.update()

    @AbstractNodeView.text_color.setter
    def text_color(self, value: tuple[int, int, int, int]):
        """
        Setter method that sets the text color of the node view.

        :param value: text color of the node view.
        """

        AbstractNodeView.text_color.fset(self, value)
        self._update_text_color(value)
        self.update()

    @property
    def title_font_name(self) -> str:
        """
        Getter method that returns the font name of the node view.

        :return: font name of the node view.
        """

        return self._properties["title_font_name"]

    @title_font_name.setter
    def title_font_name(self, value: str):
        """
        Setter method that sets the font name of the node view.

        :param value: font name of the node view.
        """

        self._properties["title_font_name"] = value
        self._title_item.font_name = value

    @property
    def title_font_size(self) -> int:
        """
        Getter method that returns the font size of the node view.

        :return: font size of the node view.
        """

        return self._properties["title_font_size"]

    @title_font_size.setter
    def title_font_size(self, value: int):
        """
        Setter method that sets the font size of the node view.

        :param value: font size of the node view.
        """

        self._properties["title_font_size"] = value
        self._title_item.font_size = value

    @property
    def title_color(self) -> tuple[int, int, int, int]:
        """
        Getter method that returns the color of the node view title.

        :return: color of the node view title.
        """

        return self._properties["title_color"]

    @title_color.setter
    def title_color(self, value: tuple[int, int, int, int]):
        """
        Setter method that sets the color of the node view title.

        :param value: color of the node view title.
        """

        self._properties["title_color"] = value

    @property
    def title_text_color(self) -> tuple[int, int, int, int]:
        """
        Getter method that returns the text color of the node view title.

        :return: text color of the node view title.
        """

        return self._properties["title_text_color"]

    @title_text_color.setter
    def title_text_color(self, value: tuple[int, int, int, int]):
        """
        Setter method that sets the text color of the node view title.

        :param value: text color of the node view title.
        """

        self._properties["title_text_color"] = value
        self._title_item.setDefaultTextColor(QColor(*value))

    @property
    def title_width(self) -> float:
        """
        Getter method that returns the width of the title.

        :return: width of the title.
        """

        return self._title_item.width

    @property
    def title_height(self) -> float:
        """
        Getter method that returns the height of the title.

        :return: height of the title.
        """

        return self._title_item.height

    @property
    def icon(self) -> str:
        """
        Getter method that returns the icon path of the node view.

        :return: icon path of the node view.
        """

        return self._properties["icon_path"]

    @icon.setter
    def icon(self, value: str):
        """
        Setter method that sets the icon path of the node view.

        :param value: icon path of the node view.
        """

        self._properties["icon_path"] = value
        value = value or self._default_icon_path
        pixmap = QPixmap(value)
        if pixmap.size().height() > uiconsts.NODE_ICON_SIZE:
            pixmap = pixmap.scaledToHeight(
                uiconsts.NODE_ICON_SIZE, Qt.SmoothTransformation
            )
        self._icon_item.setPixmap(pixmap)
        if self.scene():
            self.post_init()
        self.update()

    @property
    def inputs(self) -> list[PortView]:
        """
        Getter method that returns the input port views.

        :return: input port views.
        """

        return list(self._input_port_views.keys())

    @property
    def outputs(self) -> list[PortView]:
        """
        Getter method that returns the output port views.

        :return: output port views.
        """

        return list(self._output_port_views.keys())

    @property
    def widgets(self) -> dict[str, AbstractNodeWidget]:
        """
        Getter method that returns the widgets of the node view.

        :return: widgets of the node view.
        """

        return self._widgets.copy()

    @property
    def title_item(self) -> NodeViewTitle:
        """
        Getter method that returns the title item of the node view.

        :return: title item of the node view.
        """

        return self._title_item

    @property
    def icon_item(self) -> QGraphicsPixmapItem:
        """
        Getter method that returns the icon item of the node view.

        :return: icon item of the node view.
        """

        return self._icon_item

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """
        Event triggered when an item change occurs.

        :param change: change type.
        :param value: value of the change.
        """

        if change == QGraphicsItem.ItemSelectedChange and self.scene():
            self.reset_connectors()
            if value:
                self.highlight_connectors()
            self.setZValue(uiconsts.Z_VALUE_NODE)
            if not self.selected:
                self.setZValue(uiconsts.Z_VALUE_NODE + 1)

        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Event triggered when the mouse is pressed over the node view.

        :param event: mouse event.
        """

        # Ignore event if left mouse button is over port collision area.
        if event.button() == Qt.LeftButton:
            for port_view in self._input_port_views.keys():
                if port_view.hovered:
                    event.ignore()
                    return
            for port_view in self._output_port_views.keys():
                if port_view.hovered:
                    event.ignore()
                    return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Event triggered when the mouse is released over the node view.

        :param event: mouse event.
        """

        if event.modifiers() == Qt.AltModifier:
            event.ignore()
            return

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Event triggered when the mouse is double-clicked over the node view.

        :param event: mouse event.
        """

        if event.button() == Qt.LeftButton:
            if not self.disabled:
                items = self.scene().items(event.scenePos())
                if self._title_item in items:
                    self._title_item.editable = True
                    self._title_item.setFocus()
                    event.ignore()
                    return
            viewer = self.viewer()
            if viewer:
                viewer.nodeDoubleClicked.emit(self.id)

        super().mouseDoubleClickEvent(event)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Paints the node view.

        :param painter: painter object.
        :param option: style option.
        :param widget: widget object.
        """

        self.auto_switch_proxy_mode()

        if self.layout_direction == consts.LayoutDirection.Horizontal.value:
            self._paint_horizontal(painter, option, widget)
        elif self.layout_direction == consts.LayoutDirection.Vertical.value:
            self._paint_vertical(painter, option, widget)
        else:
            raise RuntimeError("Invalid node graph layout direction value.")

    def from_dict(self, data: dict[str, Any]):
        """
        Updates the view from given node data.

        :param data: node data to update from.
        """

        super().from_dict(data)

        custom_properties = data.get("custom") or {}
        for property_name, property_value in custom_properties.items():
            property_widget = self._widgets.get(property_name)
            if not property_widget:
                continue
            property_widget.value = property_value

    def auto_switch_proxy_mode(self):
        """
        Automatically switches the node view to proxy mode if needed.
        """

        if uiconsts.ITEM_CACHE_MODE is QGraphicsItem.ItemCoordinateCache:
            return

        rect = self.sceneBoundingRect()
        left = self.viewer().mapToGlobal(self.viewer().mapFromScene(rect.topLeft()))
        right = self.viewer().mapToGlobal(self.viewer().mapFromScene(rect.topRight()))
        width = right.x() - left.x()

        self.set_proxy_mode(width < self._proxy_mode_bias)

    def set_proxy_mode(self, flag: bool):
        """
        Sets the node view to proxy mode.

        :param flag: whether to set the node view to proxy mode.
        """

        if flag == self._proxy_mode:
            return

        self._proxy_mode = flag

        visible = not flag
        port_text_visible = (
            False
            if self.layout_direction == consts.LayoutDirection.Horizontal.value
            else visible
        )

        # Disable disabled overlay item.
        self._x_item.proxy_mode = self._proxy_mode

        # Set node widget, port text and ports visibility
        for widget in self._widgets.values():
            widget.widget().setVisible(visible)
        for port_view, text_view in self._input_port_views.items():
            if port_view.display_name:
                text_view.setVisible(port_text_visible)
        for port_view, text_view in self._output_port_views.items():
            if port_view.display_name:
                text_view.setVisible(port_text_visible)

        # Set title and icon visibility.
        self._title_item.setVisible(visible)
        self._icon_item.setVisible(visible)

    def add_input(
        self,
        data_type: datatypes.DataType,
        name: str = "input",
        display_name: bool = True,
        multi_port: bool = True,
        locked: bool = False,
        painter_function: Callable = None,
    ) -> PortView:
        """
        Adds an input port view to the node view.

        :param data_type: data type of the input port.
        :param name: name of the input port.
        :param display_name: whether to display the name of the input port.
        :param multi_port: whether to allow port to have more than one connection.
        :param locked: whether the port is locked.
        :param painter_function: optional painter function to use for the port.
        :return: input port view.
        """

        port = (
            CustomPortView(painter_function, parent=self)
            if painter_function
            else PortView(parent=self)
        )
        port.port_type = consts.PortType.Input.value
        port.data_type = data_type
        port.name = name
        port.display_name = display_name
        port.multi_connection = multi_port
        port.locked = locked

        self._add_port(port)

        return port

    def add_output(
        self,
        data_type: datatypes.DataType,
        name: str = "output",
        display_name: bool = True,
        multi_port: bool = False,
        locked: bool = False,
        painter_function: Callable = None,
    ):
        """
        Adds an output port view to the node view.

        :param data_type: data type of the output port.
        :param name: name of the output port.
        :param display_name: whether to display the name of the output port.
        :param multi_port: whether to allow port to have more than one connection.
        :param locked: whether the port is locked.
        :param painter_function: optional painter function to use for the port.
        :return: output port view.
        """

        port = (
            CustomPortView(painter_function, parent=self)
            if painter_function
            else PortView(parent=self)
        )
        port.port_type = consts.PortType.Output.value
        port.data_type = data_type
        port.name = name
        port.display_name = display_name
        port.multi_connection = multi_port
        port.locked = locked

        self._add_port(port)

        return port

    def input_text_item(self, port_view: PortView) -> QGraphicsTextItem:
        """
        Returns the text item for the given input port view.

        :param port_view: input port view.
        :return: text item for the given input port view.
        """

        return self._input_port_views[port_view]

    def output_text_item(self, port_view: PortView) -> QGraphicsTextItem:
        """
        Returns the text item for the given output port view.

        :param port_view: output port view.
        :return: text item for the given output port view.
        """

        return self._output_port_views[port_view]

    def delete_input(self, port_view: PortView):
        """
        Deletes the given input port view from the node view.

        :param port_view: input port view to delete.
        """

        self._delete_port(port_view, self._input_port_views.pop(port_view))

    def delete_output(self, port_view: PortView):
        """
        Deletes the given output port view from the node view.

        :param port_view: output port view to delete.
        """

        self._delete_port(port_view, self._output_port_views.pop(port_view))

    def calculate_size(
        self, add_width: float = 0.0, add_height: float = 0.0
    ) -> tuple[float, float]:
        """
        Internal function that calculates the minimum size of the node view.

        :param add_width: additional width.
        :param add_height: additional height.
        """

        if self.layout_direction == consts.LayoutDirection.Horizontal.value:
            width, height = self._calculate_size_horizontal()
        elif self.layout_direction == consts.LayoutDirection.Vertical.value:
            width, height = self._calculate_size_vertical()
        else:
            raise RuntimeError("Invalid node graph layout direction value.")

        width += add_width
        height += add_height

        return width, height

    def draw(self):
        """
        Forces the redraw of the node within the graph view.
        """

        if self.layout_direction == consts.LayoutDirection.Horizontal.value:
            self._draw_horizontal()
        elif self.layout_direction == consts.LayoutDirection.Vertical.value:
            self._draw_vertical()
        else:
            raise RuntimeError("Invalid node graph layout direction value.")

    def post_init(
        self,
        viewer: NodeGraphView | None = None,
        pos: tuple[float, float] | None = None,
    ):
        """
        Function that is called after the node is added into the graph scene.

        :param viewer: graph node view.
        :param pos: position where node was added.
        """

        self.draw()

        if pos:
            self.xy_pos = pos

        if self.layout_direction == consts.LayoutDirection.Vertical.value:
            font = QFont()
            font.setPointSize(15)
            self._title_item.setFont(font)
            # Hide port text views.
            for text_item in self._input_port_views.values():
                text_item.setVisible(False)
            for text_item in self._output_port_views.values():
                text_item.setVisible(False)

    def activate_connectors(self):
        """
        Activates connector colors.
        """

        port_views = self.inputs + self.outputs
        for port_view in port_views:
            for connector_view in port_view.connected_connectors:
                connector_view.activate()

    def highlight_connectors(self):
        """
        Highlights connectors colors.
        """

        port_views = self.inputs + self.outputs
        for port_view in port_views:
            for connector_view in port_view.connected_connectors:
                connector_view.highlight()

    def reset_connectors(self):
        """
        Resets connectors colors.
        """

        port_views = self.inputs + self.outputs
        for port_view in port_views:
            for connector_view in port_view.connected_connectors:
                connector_view.reset()

    def has_widget(self, name: str) -> bool:
        """
        Returns whether the node view has a widget with the given name.

        :param name: name of the widget.
        :return: whether the node view has a widget with the given name.
        """

        return name in self._widgets

    def add_widget(self, widget: AbstractNodeWidget):
        """
        Adds a widget to the node view.

        :param widget: widget to add.
        """

        self._widgets[widget.name] = widget

    def widget(self, name: str) -> AbstractNodeWidget:
        """
        Returns the widget with the given name.

        :param name: name of the widget.
        :return: widget with the given name.
        """

        widget = self._widgets.get(name)
        if not widget:
            raise exceptions.NodePropertyWidgetErrror(name)

        return self._widgets[name]

    def _add_port(self, port_view: PortView):
        """
        Internal function that adds a port view to the node view.

        :param port_view: port view to add.
        """

        text = QGraphicsTextItem(port_view.name, parent=self)
        text.font().setPointSize(8)
        text.setFont(text.font())
        text.setVisible(port_view.display_name)
        text.setCacheMode(uiconsts.ITEM_CACHE_MODE)
        if port_view.port_type == consts.PortType.Input.value:
            self._input_port_views[port_view] = text
        elif port_view.port_type == consts.PortType.Output.value:
            self._output_port_views[port_view] = text
        if self.scene():
            self.post_init()

    def _delete_port(self, port_view: PortView, text: QGraphicsTextItem):
        """
        Internal function that deletes a port view from the node view.

        :param port_view: port view to delete.
        :param text: text item to delete.
        """

        # noinspection PyTypeChecker
        port_view.setParentItem(None)
        # noinspection PyTypeChecker
        text.setParentItem(None)

        scene = self.scene()
        if scene:
            scene.removeItem(port_view)
            scene.removeItem(text)
        del port_view
        del text

    def _paint_horizontal(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Internal function that paints the node view in horizontal layout.

        :param painter: painter object.
        :param option: style option.
        :param widget: widget object.
        """

        self._painter.paint_horizontal(painter, option, widget)

    def _paint_vertical(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Internal function that paints the node view in vertical layout.

        :param painter: painter object.
        :param option: style option.
        :param widget: widget object.
        """

        raise NotImplementedError("Vertical layout painting is not implemented yet.")

    def _calculate_size_horizontal(self) -> tuple[float, float]:
        """
        Internal function that calculates the minimum size of the node view in horizontal layout.
        """

        text_width = self._title_item.width
        text_height = self._title_item.height

        # Calculate necessary height and width for the ports
        port_width: float = 0.0
        port_input_text_width: float = 0.0
        port_output_text_width: float = 0.0
        port_input_height: float = 0.0
        port_output_height: float = 0.0
        for port_view, text_view in self._input_port_views.items():
            if not port_view.isVisible():
                continue
            if not port_width:
                port_width = port_view.boundingRect().width()
            text_view_width = text_view.boundingRect().width()
            if text_view.isVisible() and text_view_width > port_input_text_width:
                port_input_text_width = text_view_width
            port_input_height += port_view.boundingRect().height()
        for port_view, text_view in self._output_port_views.items():
            if not port_view.isVisible():
                continue
            if not port_width:
                port_width = port_view.boundingRect().width()
            text_view_width = text_view.boundingRect().width()
            if text_view.isVisible() and text_view_width > port_output_text_width:
                port_output_text_width = text_view.boundingRect().width()
            port_output_height += port_view.boundingRect().height()
        port_text_width = port_input_text_width + port_output_text_width

        widget_width: float = 0.0
        widget_height: float = 0.0
        for widget in self._widgets.values():
            if not widget.isVisible():
                continue
            w_width = widget.boundingRect().width()
            w_height = widget.boundingRect().height()
            if w_width > widget_width:
                widget_width = w_width
            widget_height += w_height

        side_padding: float = 0.0
        if all([widget_width, port_input_text_width, port_output_text_width]):
            port_text_width = max([port_input_text_width, port_output_text_width])
            port_text_width *= 2
        elif widget_width:
            side_padding = 10.0

        width = port_width + max([text_width, port_text_width]) + side_padding
        height = max(
            [text_height, port_input_height, port_output_height, widget_height]
        )
        if widget_width:
            width += widget_width
        if widget_height:
            height += 4.0
        height *= 1.1
        height += text_height + 4.0

        return width, height

    def _calculate_size_vertical(self) -> tuple[float, float]:
        """
        Internal function that calculates the minimum size of the node view in vertical layout.
        """

        pass

    def _update_ports_text_visibility(self):
        """
        Internal function that updates the visibility of the ports text.
        """

        for port_view, text_view in self._input_port_views.items():
            if port_view.isVisible():
                text_view.setVisible(port_view.display_name)
        for port_view, text_view in self._output_port_views.items():
            if port_view.isVisible():
                text_view.setVisible(port_view.display_name)

    # noinspection PyUnusedLocal
    def _update_size(self, add_width: float = 0.0, add_height: float = 0.0):
        """
        Internal function that updates the size of the node view.

        :param add_width: additional width.
        :param add_height: additional height.
        """

        self._width, self._height = self.calculate_size()
        if self._width < uiconsts.NODE_WIDTH:
            self._width = uiconsts.NODE_WIDTH
        if self._height < uiconsts.NODE_HEIGHT:
            self._height = uiconsts.NODE_HEIGHT

    def _update_text_color(self, color: tuple[int, int, int, int] | None = None):
        """
        Internal function that updates the text color of the node view.

        :param color: text color.
        """

        text_color = QColor(*color or self.text_color)
        for text_view in self._input_port_views.values():
            text_view.setDefaultTextColor(text_color)
        for text_view in self._output_port_views.values():
            text_view.setDefaultTextColor(text_color)
        self._title_item.setDefaultTextColor(text_color)

    def _update_tooltip_state(self, state: bool | None = None):
        """
        Internal function that updates whether node tooltip is enabled/disabled.

        :param state: node tooltip state.
        """

        state = state if state is not None else self.disabled
        tooltip = f"<b>{self.name}</b>"
        if state:
            tooltip += ' <font color="red"><b>(DISABLED)</b></font>'
        tooltip += f"<b>{self.node_type}</b>"
        self.setToolTip(tooltip)

    def _align_label(
        self, horizontal_offset: float = 0.0, vertical_offset: float = 0.0
    ):
        """
        Internal function that aligns the node view label.

        :param horizontal_offset: optional horizontal offset for the label.
        :param vertical_offset: optional vertical offset for the label.
        """

        if self.layout_direction == consts.LayoutDirection.Horizontal.value:
            self._align_label_horizontal(horizontal_offset, vertical_offset)
        elif self.layout_direction == consts.LayoutDirection.Vertical.value:
            self._align_label_vertical(horizontal_offset, vertical_offset)
        else:
            raise RuntimeError("Invalid node graph layout direction value.")

    def _align_label_horizontal(self, horizontal_offset: float, vertical_offset: float):
        """
        Internal function that aligns the node view label in horizontal layout.

        :param horizontal_offset: optional horizontal offset for the label.
        :param vertical_offset: optional vertical offset for the label.
        """

        rect = self.boundingRect()
        text_rect = self._title_item.boundingRect()
        x = rect.center().x() - (text_rect.width() / 2)
        self._title_item.setPos(x + horizontal_offset, rect.y() + vertical_offset)

    def _align_label_vertical(self, horizontal_offset: float, vertical_offset: float):
        """
        Internal function that aligns the node view label in vertical layout.

        :param horizontal_offset: optional horizontal offset for the label.
        :param vertical_offset: optional vertical offset for the label.
        """

        rect = self._title_item.boundingRect()
        x = self.boundingRect().right() + horizontal_offset
        y = self.boundingRect().center().y() - (rect.height() / 2) + vertical_offset
        self._title_item.setPos(x, y)

    def _align_icon(self, horizontal_offset: float = 0.0, vertical_offset: float = 0.0):
        """
        Internal function that aligns node view icon.

        :param horizontal_offset: optional horizontal offset for the icon.
        :param vertical_offset: optional vertical offset for the icon.
        """

        if self.layout_direction == consts.LayoutDirection.Horizontal.value:
            self._align_icon_horizontal(horizontal_offset, vertical_offset)
        elif self.layout_direction == consts.LayoutDirection.Vertical.value:
            self._align_icon_vertical(horizontal_offset, vertical_offset)
        else:
            raise RuntimeError("Invalid node graph layout direction value.")

    def _align_icon_horizontal(
        self, horizontal_offset: float = 0.0, vertical_offset: float = 0.0
    ):
        """
        Internal function that aligns node view icon in horizontal layout.

        :param horizontal_offset: optional horizontal offset for the icon.
        :param vertical_offset: optional vertical offset for the icon.
        """

        icon_rect = self._icon_item.boundingRect()
        text_rect = self._title_item.boundingRect()
        x = self.boundingRect().left() + 2.0
        y = text_rect.center().y() - (icon_rect.height() / 2)
        self._icon_item.setPos(x + horizontal_offset, y + vertical_offset)

    def _align_icon_vertical(
        self, horizontal_offset: float = 0.0, vertical_offset: float = 0.0
    ):
        """
        Internal function that aligns node view icon in vertical layout.

        :param horizontal_offset: optional horizontal offset for the icon.
        :param vertical_offset: optional vertical offset for the icon.
        """

        center_y = self.boundingRect().center().y()
        icon_rect = self._icon_item.boundingRect()
        text_rect = self._title_item.boundingRect()
        x = self.boundingRect().right() + horizontal_offset
        y = center_y - text_rect.height() - (icon_rect.height() / 2) + vertical_offset
        self._icon_item.setPos(x, y)

    def _align_ports(self, vertical_offset: float = 0.0):
        """
        Internal function that aligns the node view ports.

        :param vertical_offset: optional vertical offset for the ports.
        """

        if self.layout_direction == consts.LayoutDirection.Horizontal.value:
            self._align_ports_horizontal(vertical_offset)
        elif self.layout_direction == consts.LayoutDirection.Vertical.value:
            self._align_ports_vertical(vertical_offset)
        else:
            raise RuntimeError("Invalid node graph layout direction value.")

    def _align_ports_horizontal(self, vertical_offset: float = 0.0):
        """
        Internal function that aligns the node view ports in horizontal layout.

        :param vertical_offset: optional vertical offset for the ports.
        """

        width = self._width
        text_offset = uiconsts.PORT_CLICK_FALLOFF - 2
        spacing: int = 1

        # Adjust input port views position and text positions.
        input_port_views = [
            port_view for port_view in self.inputs if port_view.isVisible()
        ]
        if input_port_views:
            port_width = input_port_views[0].boundingRect().width()
            port_height = input_port_views[0].boundingRect().height()
            port_x = (port_width / 2) * -1
            port_y = vertical_offset
            for input_port_view in input_port_views:
                input_port_view.setPos(port_x, port_y)
                port_y += port_height + spacing
        for port_view, text_view in self._input_port_views.items():
            if not port_view.isVisible():
                continue
            text_x = port_view.boundingRect().width() / 2 - text_offset
            text_view.setPos(text_x, port_view.y() - 1.5)

        # Adjust output port views position and text positions.
        output_port_views = [
            port_view for port_view in self.outputs if port_view.isVisible()
        ]
        if output_port_views:
            port_width = output_port_views[0].boundingRect().width()
            port_height = output_port_views[0].boundingRect().height()
            port_x = width - (port_width / 2)
            port_y = vertical_offset
            for output_port_view in output_port_views:
                output_port_view.setPos(port_x, port_y)
                port_y += port_height + spacing
        for port_view, text_view in self._output_port_views.items():
            if not port_view.isVisible():
                continue
            text_width = text_view.boundingRect().width() - text_offset
            text_x = port_view.x() - text_width
            text_view.setPos(text_x, port_view.y() - 1.5)

    def _align_ports_vertical(self, vertical_offset: float = 0.0):
        """
        Internal function that aligns the node view ports in vertical layout.

        :param vertical_offset: optional vertical offset for the ports.
        """

        pass

    def _align_widgets(self, vertical_offset: float = 0.0):
        """
        Internal function that aligns the node view widgets.

        :param vertical_offset: optional vertical offset for the widgets.
        """

        if self.layout_direction == consts.LayoutDirection.Horizontal.value:
            self._align_widgets_horizontal(vertical_offset)
        elif self.layout_direction == consts.LayoutDirection.Vertical.value:
            self._align_widgets_vertical(vertical_offset)
        else:
            raise RuntimeError("Invalid node graph layout direction value.")

    def _align_widgets_horizontal(self, vertical_offset: float = 0.0):
        """
        Internal function that aligns the node view widgets in horizontal layout.

        :param vertical_offset: optional vertical offset for the widgets.
        """

        if not self._widgets:
            return

        rect = self.boundingRect()
        y = rect.y() + vertical_offset
        inputs = [p for p in self.inputs if p.isVisible()]
        outputs = [p for p in self.outputs if p.isVisible()]
        for widget in self._widgets.values():
            if not widget.isVisible():
                continue
            widget_rect = widget.boundingRect()
            if not inputs:
                x = rect.left() + 10
                # noinspection PyUnresolvedReferences
                widget.widget().set_title_align("left")
            elif not outputs:
                x = rect.right() - widget_rect.width() - 10
                # noinspection PyUnresolvedReferences
                widget.widget().set_title_align("right")
            else:
                x = rect.center().x() - (widget_rect.width() / 2)
                # noinspection PyUnresolvedReferences
                widget.widget().set_title_align("center")
            widget.setPos(x, y)
            y += widget_rect.height()

    def _align_widgets_vertical(self, vertical_offset: float = 0.0):
        """
        Internal function that aligns the node view widgets in vertical layout.

        :param vertical_offset: optional vertical offset for the widgets.
        """

        pass

    def _draw_horizontal(self):
        """
        Internal function that draws the node view in horizontal layout.
        """

        self._update_ports_text_visibility()

        height = self._title_item.height + 4.0
        self._update_size(add_height=height)
        self._update_text_color()
        self._update_tooltip_state()

        self._align_label()
        self._align_icon(horizontal_offset=2.0, vertical_offset=1.0)
        self._align_ports(vertical_offset=height)
        self._align_widgets(vertical_offset=height)

        self.update()

    def _draw_vertical(self):
        """
        Internal function that draws the node view in vertical layout.
        """

        raise NotImplementedError("Vertical layout drawing is not implemented yet.")


class NodeViewTitle(QGraphicsTextItem):
    """
    Class that defines the title of a node view.
    """

    def __init__(
        self,
        node_view: NodeView,
        text: str = "",
        color: tuple[int, int, int, int] | None = None,
        font_name: str = "Robot",
        font_size: int = 10,
        horizontal_padding: float = 4.0,
        vertical_padding: float = 4.0,
        locked: bool = False,
        editable: bool = True,
    ):
        super().__init__(text, parent=node_view)

        self._locked = False
        self._horizontal_padding = horizontal_padding
        self._vertical_padding = vertical_padding
        self._font_name = font_name
        self._font_size = font_size
        self._font = QFont(font_name, font_size)
        self._font.setBold(True)

        if color is not None:
            self.setDefaultTextColor(QColor(*color))
        self.setFont(self._font)
        self.setPos(self._horizontal_padding, 0)

        self.locked = locked
        self.editable = editable

    @property
    def node_view(self) -> NodeView:
        """
        Getter method that returns the node view.

        :return: node view.
        """

        # noinspection PyTypeChecker
        return self.parentItem()

    @property
    def width(self) -> float:
        """
        Getter method that returns the width of the title.

        :return: width of the title.
        """

        return self.boundingRect().width()

    @property
    def height(self) -> float:
        """
        Getter method that returns the height of the title.

        :return: height of the title.
        """

        return self.boundingRect().height()

    @property
    def locked(self) -> bool:
        """
        Getter method that returns whether the title is locked or not.

        :return: locked state.
        """

        return self._locked

    @locked.setter
    def locked(self, flag: bool):
        """
        Setter method that sets whether the title is locked or not.

        :param flag: locked state.
        """

        self._locked = flag

        if self._locked:
            self.setFlag(QGraphicsItem.ItemIsFocusable, False)
            self.setCursor(Qt.ArrowCursor)
            self.setToolTip("")
        else:
            self.setFlag(QGraphicsItem.ItemIsFocusable, True)
            self.setToolTip("Double-click to edit node name.")
            self.setCursor(Qt.IBeamCursor)

    @property
    def editable(self) -> bool:
        """
        Getter method that returns whether the title is editable or not.

        :return: editable state.
        """

        if self.locked:
            return False

        return False if self.textInteractionFlags() & Qt.NoTextInteraction else True

    @editable.setter
    def editable(self, flag: bool):
        """
        Setter method that sets whether the title is editable or not.

        :param flag: editable state.
        """

        if self.locked:
            return

        if flag:
            self.setTextInteractionFlags(
                Qt.TextEditable | Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
            )
        else:
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            cursor = self.textCursor()
            cursor.clearSelection()
            self.setTextCursor(cursor)

    @property
    def font_name(self) -> str:
        """
        Getter method that returns the font name of the node view.

        :return: font name of the node view.
        """

        return self._font_name

    @font_name.setter
    def font_name(self, value: str):
        """
        Setter method that sets the font name of the node view.

        :param value: font name of the node view.
        """

        self._font_name = value
        self._font = QFont(value, self.font_size)
        self._font.setBold(True)
        self.setFont(self._font)

    @property
    def font_size(self) -> int:
        """
        Getter method that returns the font size of the node view.

        :return: font size of the node view.
        """

        return self._font_size

    @font_size.setter
    def font_size(self, value: int):
        """
        Setter method that sets the font size of the node view.

        :param value: font size of the node view.
        """

        self._font_size = value
        self._font = QFont(self.font_name, value)
        self._font.setBold(True)
        self.setFont(self._font)

    def focusOutEvent(self, event: QFocusEvent):
        """
        Event triggered when the title loses focus.

        :param event: focus event.
        """

        current_text = self.toPlainText()
        self._set_node_name(current_text)
        self.editable = False

        super().focusOutEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Event triggered when the title is double-clicked.

        :param event: mouse event.
        """

        if self.locked:
            super().mouseDoubleClickEvent(event)
            return
        if event.button() == Qt.LeftButton:
            self.editable = True
            event.ignore()
            return

        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """
        Event triggered when a key is pressed.

        :param event: key event.
        """

        if event.key() == Qt.Key_Return:
            current_text = self.toPlainText()
            self._set_node_name(current_text)
            self.editable = False
        elif event.key() == Qt.Key_Escape:
            self.setPlainText(self.node_view.name)
            self.editable = True

        super().keyPressEvent(event)

    def _set_node_name(self, name: str):
        """
        Internal function that sets the name of the node view.

        :param name: name of the node view.
        """

        name = name.strip()
        if name == self.node_view.name:
            return

        # We update the name through nodeNameChanged to ensure the renaming is done as an undo command.
        self.node_view.viewer().nodeNameChanged.emit(self.node_view.id, name)


class NodeDisabledViewItem(QGraphicsItem):
    """
    Class that defines a node disabled view item.
    """

    def __init__(self, text: str | None = None, parent: NodeView | None = None):
        super().__init__(parent=parent)

        self._proxy_mode: bool = False
        self._color: tuple[int, int, int, int] = (0, 0, 0, 255)
        self._text: str = text

        self.setZValue(uiconsts.Z_VALUE_NODE_WIDGET + 2)
        self.setVisible(False)

    @property
    def proxy_mode(self) -> bool:
        """
        Getter method that returns whether the node view is in proxy mode or not.

        :return: proxy mode state.
        """

        return self._proxy_mode

    @proxy_mode.setter
    def proxy_mode(self, flag: bool):
        """
        Setter method that sets whether the node view is in proxy mode or not.

        :param flag: proxy mode state.
        """

        self._proxy_mode = flag

    def boundingRect(self) -> QRectF:
        """
        Returns the bounding rectangle of the node disabled view item.

        :return: bounding rectangle.
        """

        return self.parentItem().boundingRect()

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Paints the node disabled view item.

        :param painter: painter object.
        :param option: style option.
        :param widget: widget object.
        """

        painter.save()
        try:
            margin: int = 20
            rect = self.boundingRect()
            distance_rect = QRectF(
                rect.left() - (margin / 2),
                rect.top() - (margin / 2),
                rect.width() + margin,
                rect.height() + margin,
            )
            if not self._proxy_mode:
                pen = QPen(QColor(*self._color), 8)
                pen.setCapStyle(Qt.RoundCap)
                painter.drawLine(distance_rect.topLeft(), distance_rect.bottomRight())
                painter.drawLine(distance_rect.topRight(), distance_rect.bottomLeft())
            background_color = QColor(*self._color)
            background_color.setAlpha(100)
            background_margin = -0.5
            background_rect = QRectF(
                distance_rect.left() - (background_margin / 2),
                distance_rect.top() - (background_margin / 2),
                distance_rect.width() + background_margin,
                distance_rect.height() + background_margin,
            )
            painter.setPen(QPen(QColor(0, 0, 0, 0)))
            painter.setBrush(background_color)
            painter.drawRoundedRect(background_rect, 5, 5)
            if not self._proxy_mode:
                point_size = 4.0
                pen = QPen(QColor(155, 0, 0, 255), 0.7)
            else:
                point_size = 8.0
                pen = QPen(QColor(155, 0, 0, 255), 4.0)
            painter.setPen(pen)
            painter.drawLine(distance_rect.topLeft(), distance_rect.bottomRight())
            painter.drawLine(distance_rect.topRight(), distance_rect.bottomLeft())
            point_pos = (
                distance_rect.topLeft(),
                distance_rect.topRight(),
                distance_rect.bottomLeft(),
                distance_rect.bottomRight(),
            )
            painter.setBrush(QColor(255, 0, 0, 255))
            for p in point_pos:
                p.setX(p.x() - (point_size / 2))
                p.setY(p.y() - (point_size / 2))
                point_rect = QRectF(p, QSizeF(point_size, point_size))
                painter.drawEllipse(point_rect)
            if self._text and not self._proxy_mode:
                font = painter.font()
                font.setPointSize(10)
                painter.setFont(font)
                font_metrics = QFontMetrics(font)
                font_width = font_metrics.horizontalAdvance(self._text)
                font_height = font_metrics.height()
                txt_w = font_width * 1.25
                txt_h = font_height * 2.25
                text_bg_rect = QRectF(
                    (rect.width() / 2) - (txt_w / 2),
                    (rect.height() / 2) - (txt_h / 2),
                    txt_w,
                    txt_h,
                )
                painter.setPen(QPen(QColor(255, 0, 0), 0.5))
                painter.setBrush(QColor(*self._color))
                painter.drawRoundedRect(text_bg_rect, 2, 2)

                text_rect = QRectF(
                    (rect.width() / 2) - (font_width / 2),
                    (rect.height() / 2) - (font_height / 2),
                    txt_w * 2,
                    font_height * 2,
                )
                painter.setPen(QPen(QColor(255, 0, 0), 1))
                painter.drawText(text_rect, self._text)
        finally:
            painter.restore()
