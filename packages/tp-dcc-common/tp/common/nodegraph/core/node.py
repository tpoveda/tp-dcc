from __future__ import annotations

import typing
from collections import deque
from typing import Iterable, Any

from overrides import override

from tp.core import log
from tp.common.qt import api as qt
from tp.common.python import decorators
from tp.common.nodegraph import datatypes
from tp.common.nodegraph.core import consts, socket, commands
from tp.common.nodegraph.models import node as node_model
from tp.common.nodegraph.graphics import node as node_graphics
from tp.common.nodegraph.widgets import attributes

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.graph import NodeGraph

logger = log.rigLogger


class BaseNode:

    NODE_NAME: str | None = None
    GRAPHICS_CLASS = node_graphics.BaseGraphicsNode

    ID: int | None = None
    IS_EXEC = True
    AUTO_INIT_EXECS = True
    DEFAULT_TITLE = 'Custom Node'
    TITLE_EDITABLE = False
    TITLE_COLOR = '#FF313131'
    MIN_WIDTH = consts.NODE_MIN_WIDTH
    MIN_HEIGHT = consts.NODE_MIN_HEIGHT
    MAX_TEXT_WIDTH = 200
    COMPILABLE = False
    IS_INPUT = False

    def __init__(self, graph: NodeGraph):
        super().__init__()

        self._graph = graph
        self._model = node_model.NodeModel()
        self._model.graph_model = self._graph.model
        self._title = ''

        self._graphics_node = self.GRAPHICS_CLASS(self)

        self.title = self.__class__.NODE_NAME or self.__class__.DEFAULT_TITLE

        self._graph.add_node(self)

    def __repr__(self):
        return '<{}("{}") object at {}>'.format(self.__class__.__name__, self.ID, hex(id(self)))

    @decorators.classproperty
    def type(cls) -> str:
        """
        Returns the node  following by the class name.

        :return: node type.
        :rtype: int or str
        """

        return f'{cls.ID}.{cls.__name__}'

    @classmethod
    def as_str(cls, name_only: bool = False) -> str:
        """
        Returns a string representation of the class.

        :param bool name_only: whether to return the name of the class only.
        :return: class as a string.
        """

        return cls.__name__ if name_only else '.'.join([cls.__module__, cls.__name__])

    @property
    def graph(self) -> NodeGraph | None:
        """
        Getter method that returns the parent node graph this node belongs to.

        :return: parent node graph.
        :rtype: NodeGraph or None
        """

        return self._graph

    @property
    def model(self) -> node_model.NodeModel:
        """
        Getter method that returns node model.

        :return: node model.
        :rtype: node_model.NodeModel
        """

        return self._model

    @model.setter
    def model(self, value: node_model.NodeModel):
        """
        Setter method that sets the node model.

        :param node_model.NodeModel value: node model.
        """

        self._model = value

        self.update()

    @property
    def uuid(self) -> str:
        """
        Getter method that returns node unique ID.

        :return: node unique identifier.
        :rtype: str
        """

        return self.model.uuid

    @uuid.setter
    def uuid(self, value: str):
        """
        Setter method that sets node unique ID.

        :param str value: node unique identifier.
        """

        if self.graph:
            self.graph.model.nodes[value] = self.graph.model.nodes.pop(self.uuid)

        self.model.uuid = value

    @property
    def view(self) -> node_graphics.BaseGraphicsNode:
        """
        Getter method that returns node view instance.

        :return: node view.
        :rtype: node_graphics.BaseGraphicsNode
        """

        return self._graphics_node

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value
        try:
            self._graphics_node.title = self._title
        except AttributeError:
            # Node graphics do not need to have title in all scenarios
            # TODO: Improve this
            pass

    def add_property(
            self, name: str, value: Any, items: list[str] | None = None, value_range: tuple[int, int] | None = None,
            widget_type: int | None = None, widget_tooltip: str | None = None, tab: str | None = None):
        """
        Adds a custom property to the node.

        :param str name: name of the property.
        :param Any value: property value to set.
        :param list[str] or None items: list of items (used by NODE_PROPERTY_COMBOBOX).
        :param tuple[int, int] or None value_range: minimum and maximum values (used by NODE_PROPERTY_SLIDER).
        :param str or None widget_type: widget type flag.
        :param str or None widget_tooltip: custom tooltip for the property widget.
        :param str or None tab: widget tab name.
        """

        self._model.add_property(
            name, value, items=items, value_range=value_range, widget_type=widget_type,
            widget_tooltip=widget_tooltip, tab=tab)

    def properties(self) -> dict[str, dict]:
        """
        Generator function that yields all node properties.

        :return: iterated node properties.
        :rtype: dict[str, dict]]
        """

        props = self.model.to_dict()[self.uuid].copy()
        props['uuid'] = self.uuid
        return props

    def property(self, name: str) -> Any:
        """
        Returns the node custom property value.

        :param str name: name of the property whose value we want to retrieve.
        :return: property value.
        :rtype: Any
        """

        if self.graph and name == 'selected':
            self.model.set_property(name, self.view.selected)

        return self.model.property(name)

    def set_property(self, name, value, push_undo: bool = False):
        """
        Sets the value on the node custom property.

        :param str name: name of the property to set.
        :param Any value: node value.
        :param bool push_undo: whether to register the command to the undo stack.
        """

        if push_undo:
            undo_command = commands.PropertyChangedCommand(self, name, value)
            self.graph.undo_stack.push(undo_command)

        if self.property(name) == value:
            return

        # Prevent nodes from having the same name.
        if self.graph and name == 'name':
            value = self.graph.unique_node_name(value)
            self.NODE_NAME = value

        # Make sure that view widgets values match new property value
        if hasattr(self.view, 'widgets') and name in self.view.widgets.keys():
            if self.view.widgets[name].value() != value:
                self.view.widgets[name].set_value(value)

        if name in self.view.properties:
            name = 'xy_pos' if name == 'pos' else name
            setattr(self.view, name, value)

        self.graph.propertyChanged.emit(self, name, value)

    def name(self) -> str:
        """
        Returns name of the node.

        :return: name of the node.
        :rtype: str
        """

        return self.model.name

    def set_name(self, name: str = ''):
        """
        Sets the name of the node.

        :param str name: new node name.
        """

        self.set_property('name', name)

    def update(self):
        """
        Updates the node view based on current node model data.
        """

        print('Updating view ...')

    def pre_serialization(self):
        """
        Function that is called before node serialization process starts.
        This function can be overriden by custom node classes.
        """

        pass

    def post_serialization(self, data: dict):
        """
        Function that is called before node serialization process starts.
        This function can be overriden by custom node classes.

        :param dict data: node deserialized data.
        """

        pass

    def pre_deserialization(self, data: dict):
        """
        Function that is called before node deserialization process starts.
        This function can be overriden by custom node classes.

        :param dict data: node serialized data.
        """

        pass

    def post_deserialization(self, data: dict):
        """
        Function that is called after node deserialization process ends.
        This function can be overriden by custom node classes.

        :param dict data: node serialized data.
        """

        pass

    def set_position(self, x: float, y: float):
        """
        Sets node position within scene.

        :param float x: X coordinate.
        :param float y: Y coordinate.
        """

        self._graphics_node.setPos(x, y)

    def position(self) -> list[float, float]:
        """
        Returns node position within scene.

        :return: node position.
        :rtype: list[float, float]
        """

        if self.view.xy_pos and self.view.xy_pos != self.model.pos:
            self.model.pos = self.view.xy_pos

        return self.model.pos

    def x_position(self) -> float:
        """
        Returns the node X position in the node graph.

        :return: node X position.
        :rtype: float
        """

        return self.position()[0]

    def y_position(self) -> float:
        """
        Returns the node Y position in the node graph.

        :return: node Y position.
        :rtype: float
        """

        return self.position()[1]

    def set_position(self, x: float, y: float):
        """
        Sets the node X and Y position in the node graph.

        :param float x: X position of the node in the node graph.
        :param float y: Y position of the node in the node graph.
        """

        self.set_property('pos', [float(x), float(y)])

    def append_tooltip(self, text: str):
        """
        Appends given text to node tooltip.

        :param str text: tooltip to append.
        """

        self._graphics_node.setToolTip(self._graphics_node.toolTip() + text)

    def remove(self, silent: bool = False):
        """
        Removes node from scene.

        :param bool silent: whether to emit remove signals, so listeners are notified.
        """

        try:
            self.graph.remove_node(self)
            self.graph.graphics_scene.removeItem(self._graphics_node)
            self._graphics_node = None
        except Exception:
            logger.exception(f'Failed to delete node {self}', exc_info=True)


class Node(BaseNode):

    GRAPHICS_CLASS = node_graphics.GraphicsNode
    ATTRIBUTES_WIDGET = attributes.AttributesWidget

    class Signals(qt.QObject):
        compiledChanged = qt.Signal(bool)
        invalidChanged = qt.Signal(bool)
        titleEdited = qt.Signal(str)
        numSocketsChanged = qt.Signal()

    COMPILABLE = True
    INPUT_POSITION = socket.Socket.Position.LeftTop.value
    OUTPUT_POSITION = socket.Socket.Position.RightTop.value

    def __init__(self, graph: NodeGraph):
        super().__init__(graph=graph)

        self._signals = Node.Signals()

        self._is_compiled = False
        self._is_invalid = False
        self._is_executing = False

        self._inputs: list[socket.InputSocket] = []
        self._outputs: list[socket.OutputSocket] = []
        self._required_inputs: deque[socket.InputSocket] = deque()
        self._exec_in_socket: socket.InputSocket | None = None
        self._exec_out_socket: socket.OutputSocket | None = None

        self._setup_settings()

        self.signals.numSocketsChanged.connect(self._on_num_sockets_changed)
        self._setup_sockets()
        self._setup_signals()

    @property
    def signals(self) -> Signals:
        return self._signals

    @property
    def inputs(self) -> list[socket.InputSocket]:
        return self._inputs

    @property
    def outputs(self) -> list[socket.OutputSocket]:
        return self._outputs

    @property
    def required_inputs(self) -> deque[socket.InputSocket]:
        return self._required_inputs

    @property
    def exec_in_socket(self) -> socket.InputSocket | None:
        return self._exec_in_socket

    @property
    def exec_out_socket(self) -> socket.OutputSocket | None:
        return self._exec_out_socket

    @property
    def is_executing(self) -> bool:
        return self._is_executing

    @override
    def post_deserialization(self, data: dict):
        self.signals.numSocketsChanged.emit()

    @override
    def remove(self, silent: bool = False):
        try:
            self.remove_all_connections(include_exec=True, silent=silent)
        except Exception:
            logger.exception(f'Failed to delete node {self}', exc_info=True)
            return
        super().remove(silent=silent)

    def setup_sockets(self):
        """
        Creates all custom sockets for this node instance.
        This function can be overriden by custom node classes.
        """

        pass

    def exec_queue(self) -> deque[Node]:
        """
        Recursive function that returns executable queue, that defines the order of execution for nodes.

        :return: nodes executable queue.
        :rtype: deque[Node]
        """

        exec_queue = deque([self])
        for exec_output in self.list_exec_outputs():
            if not exec_output.list_connections():
                continue
            exec_queue.extend(exec_output.list_connections()[0].node.exec_queue())

        return exec_queue

    def execute(self) -> Any:
        """
        Executes node logic.
        """

        return 0

    def execute_children(self):
        """
        Executes children nodes.
        """

        for child_node in self.list_exec_children():
            child_node._exec()

    def value(self, socket_name: str) -> Any:
        """
        Returns the internal value of given socket name.

        :param str socket_name: socket name to get value of.
        :return: socket value.
        :rtype: Any
        :raises AttributeError: if socket with given name does not exist.
        """

        found_socket = getattr(self, socket_name)
        if not found_socket or not isinstance(found_socket, socket.Socket):
            logger.error(f'Socket "{socket_name}" does not exist!')
            raise AttributeError

        return found_socket.value()

    def verify_inputs(self) -> bool:
        """
        Verifies that input sockets are valid for this node.

        :return: True if inputs are valid; False otherwise.
        :rtype: bool
        """

        invalid_inputs: deque[socket.Socket] = deque()
        for input_socket in self._required_inputs:
            if not input_socket.has_edge() and not input_socket.value():
                invalid_inputs.append(input_socket)

        if invalid_inputs:
            tooltip = ''
            for invalid_input in invalid_inputs:
                tooltip += f'Invalid input: {invalid_input.label}\n'
            self.append_tooltip(tooltip)
            return False

        return True

    def verify(self) -> bool:
        """
        Verifies whether node can be compiled.

        :return: True if node can be compiled; False otherwise.
        :rtype: bool
        """

        self._graphics_node.setToolTip('')
        result = self.verify_inputs()

        return result

    def socket_position(
            self, index: int, position: socket.Socket.Position, count_on_this_side: int = 1) -> list[int, int]:
        """
        Returns the position of the socket at given index.

        :param int index: socket index.
        :param socket.Socket.Position position: socket position.
        :param int count_on_this_side: number of sockets on the side.
        :return: socket position relative to this node graphics.
        :rtype: list[int, int]
        """

        if position in (
                socket.Socket.Position.LeftTop, socket.Socket.Position.LeftCenter, socket.Socket.Position.LeftBottom):
            x = 0
        else:
            x = self.view.width

        if position in (socket.Socket.Position.LeftBottom, socket.Socket.Position.RightBottom):
            # start from top
            y = self.view.height - self.view.edge_roundness - self.view.title_horizontal_padding - index * self._socket_spacing
        elif position in (socket.Socket.Position.LeftCenter, socket.Socket.Position.RightCenter):
            num_sockets = count_on_this_side
            node_height = self.view.height
            top_offset = self.view.title_height + 2 * self.view.title_vertical_padding + self.view.edge_padding
            available_height = node_height - top_offset

            y = top_offset + available_height / 2.0 + (index - 0.5) * self._socket_spacing
            if num_sockets > 1:
                y -= self._socket_spacing * (num_sockets - 1) / 2

        elif position in (socket.Socket.Position.LeftTop, socket.Socket.Position.RightTop):
            # start from bottom
            y = self.view.title_height + self.view.title_horizontal_padding + self.view.edge_roundness + index * self._socket_spacing
        else:
            y = 0

        return [x, y]

    def add_input(
            self, data_type: dict, label: str | None = None, value: Any = None, *args, **kwargs) -> socket.InputSocket:
        """
        Adds a new input socket to this node.

        :param dict data_type: data type of the socket.
        :param str or None label: optional input socket label.
        :param Any value: optional default input socket value.
        :return: newly created input socket.
        :rtype: socket.InputSocket
        """

        def _new_input_index() -> int:
            return len(self._inputs)

        new_socket = socket.InputSocket(
            self, index=_new_input_index(), position=self.__class__.INPUT_POSITION, data_type=data_type, label=label,
            max_connections=1, value=value, count_on_this_side=_new_input_index(), *args, **kwargs)
        self._inputs.append(new_socket)
        self.signals.numSocketsChanged.emit()

        return new_socket

    def mark_input_as_required(self, input_socket_to_mark_as_required: socket.InputSocket):
        """
        Marks given input socket as a required socket for the node to be executed.

        :param socket.InputSocket input_socket_to_mark_as_required: input socket to mark as required.
        """

        if isinstance(input_socket_to_mark_as_required, socket.InputSocket):
            self._required_inputs.append(input_socket_to_mark_as_required)
        elif isinstance(input_socket_to_mark_as_required, str):
            input_socket_to_mark_as_required = self.find_first_input_with_label(input_socket_to_mark_as_required)
            if not input_socket_to_mark_as_required:
                logger.error(
                    f'Can not mark input {input_socket_to_mark_as_required} as required. '
                    f'Failed to find socket from label.')
                return
            self._required_inputs.append(input_socket_to_mark_as_required)
        else:
            logger.error(f'Invalid required "input socket" argument {input_socket_to_mark_as_required}')

    def mark_inputs_as_required(self, input_sockets: Iterable[socket.InputSocket]):
        """
        Marks given input sockets as required sockets for the node to be executed.

        :param Iterable[socket.InputSocket] input_sockets: list of input sockets to mark as required.
        """

        for input_socket in input_sockets:
            self.mark_input_as_required(input_socket)

    def add_output(
            self, data_type: dict, label: str | None = None, max_connections: int = 0, value: Any = None, *args,
            **kwargs) -> socket.OutputSocket:
        """
        Adds a new output socket to this node.

        :param dict data_type: data type of the socket.
        :param str or None label: optional input socket label.
        :param int max_connections: maximum number of connections this socket will accept.
        :param Any value: optional default input socket value.
        :return: newly created input socket.
        :rtype: socket.OutputSocket
        """

        def _new_output_index() -> int:
            return len(self._outputs)

        max_connections = 1 if data_type == datatypes.Exec else max_connections
        new_socket = socket.OutputSocket(
            self, index=_new_output_index(), position=self.__class__.OUTPUT_POSITION, data_type=data_type, label=label,
            max_connections=max_connections, value=value, count_on_this_side=_new_output_index(), *args, **kwargs)
        self._outputs.append(new_socket)
        self.signals.numSocketsChanged.emit()

        return new_socket

    def find_first_input_with_label(self, text: str) -> socket.InputSocket | None:
        """
        Returns first input socket with given label.

        :param str text: label to find input socket by.
        :return: found input socket instance.
        :rtype: socket.InputSocket or None
        """

        found_input_socket = None
        for input_socket in self._inputs:
            if input_socket.label == text:
                found_input_socket = input_socket
                break
        return found_input_socket

    def find_first_input_of_datatype(self, datatype: dict) -> socket.InputSocket | None:
        """
        Returns first input socket with given data type.

        :param dict datatype: data type to find input socket by.
        :return: found input socket instance.
        :rtype: socket.InputSocket or None
        """

        found_input_socket = None
        for input_socket in self._inputs:
            if issubclass(datatype.get('class', type(None)), input_socket.data_class):
                found_input_socket = input_socket
                break
        return found_input_socket

    def find_first_output_with_label(self, text) -> socket.OutputSocket | None:
        """
        Returns output input socket with given label.

        :param str text: label to find output socket by.
        :return: found output socket instance.
        :rtype: socket.OutputSocket or None
        """

        found_output_socket = None
        for output_socket in self._outputs:
            if output_socket.label == text:
                found_output_socket = output_socket
                break
        return found_output_socket

    def list_exec_outputs(self) -> list[socket.OutputSocket]:
        """
        Returns list of executable output sockets.

        :return: executable output sockets.
        :rtype: list[socket.OutputSocket]
        """

        return [found_socket for found_socket in self.outputs if found_socket.data_type == datatypes.Exec]

    def list_non_exec_inputs(self) -> list[socket.InputSocket]:
        """
        Returns list of non executable input sockets.

        :return: nont executable input sockets.
        :rtype: list[socket.InputSocket]
        """

        return [found_socket for found_socket in self.inputs if found_socket.data_type != datatypes.Exec]

    def list_non_exec_outputs(self) -> list[socket.OutputSocket]:
        """
        Returns list of non executable outputs sockets.

        :return: nont executable outputs sockets.
        :rtype: list[socket.OutputSocket]
        """

        return [found_socket for found_socket in self.outputs if found_socket.data_type != datatypes.Exec]

    def find_first_output_of_datatype(self, datatype: dict):
        """
        Returns first output socket with given data type.

        :param dict datatype: data type to find output socket by.
        :return: found output socket instance.
        :rtype: socket.OutputSocket or None
        """

        found_output_socket = None
        for output_socket in self._outputs:
            if issubclass(output_socket.data_class, datatype.get('class', type(None))):
                found_output_socket = output_socket
                break
        return found_output_socket

    def is_invalid(self) -> bool:
        """
        Returns whether node is invalid.

        :return: True if node is invalid; False otherwise.
        :rtype: bool
        """

        return self._is_invalid

    def set_invalid(self, flag: bool = True):
        """
        Sets node invalid status.

        :param bool flag: True to set node as invalid; False otherwise.
        """

        self._is_invalid = flag
        self.signals.invalidChanged.emit(self._is_invalid)

    def is_compiled(self) -> bool:
        """
        Returns whether this node is already compiled.

        :return: True if node is compiled; False otherwise.
        :rtype: bool
        """

        return self._is_compiled

    def set_compiled(self, flag: bool = False, emit_signal: bool = True):
        """
        Sets node compile status.

        :param bool flag: True to set node as compiled; False otherwise.
        :param bool emit_signal: whether to notify that compile status changed.
        """

        if self._is_compiled == flag:
            return
        self._is_compiled = flag
        self.signals.compiledChanged.emit(self._is_compiled)

    def mark_children_compiled(self, state: bool):
        """
        Marks all children nodes with given compile status.

        :param bool state: compile status.
        """

        if state:
            return

        for child_node in self.list_children():
            child_node.set_compiled(state)
            child_node.mark_children_compiled(state)

    def remove_socket(self, name: str, is_input: bool = True):
        """
        Removes socket with given name from node.

        :param str name: name of the socket to remove.
        :param bool is_input: whether the input to remove is an input one or an output one.
        """

        try:
            if is_input:
                socket_to_remove = [socket for socket in self.inputs if socket.label == name][0]
                self.inputs.remove(socket_to_remove)
                if socket_to_remove in self._required_inputs:
                    self._required_inputs.remove(socket_to_remove)
                for index, socket in enumerate(self.inputs):
                    socket.index = index
            else:
                socket_to_remove = [socket for socket in self.outputs if socket.label == name][0]
                self.outputs.remove(socket_to_remove)
                for index, socket in enumerate(self.outputs):
                    socket.index = index
            socket_to_remove.remove()
            self.signals.numSocketsChanged.emit()
        except Exception:
            logger.exception('Failed to delete socket {}'.format(name), exc_info=True)

    def remove_existing_sockets(self):
        """
        Deletes all sockets that already exist for this node.
        """

        for socket_to_delete in self._inputs + self._outputs:
            self.graph.graphics_scene.removeItem(socket_to_delete.graphics_socket)
        self._inputs.clear()
        self._outputs.clear()

    def remove_all_connections(self, include_exec: bool = False, silent: bool = False):
        """
        Deletes all edges connected to this node sockets.

        :param bool include_exec: whether to delete edges connected to executable sockets.
        :param bool silent: whether to emit remove signals, so listeners are notified.
        """

        for input_socket in self.inputs:
            if not include_exec and input_socket.data_type == datatypes.Exec:
                continue
            input_socket.remove_all_edges(silent=silent)
        for output_socket in self.outputs:
            if not include_exec and output_socket.data_type == datatypes.Exec:
                continue
            output_socket.remove_all_edges(silent=silent)

    def list_children(self, recursive: bool = False) -> list[Node]:
        """
        Recursive function that return a list with all connected children nodes.

        :param bool recursive: whether to return children recursively.
        :return: children nodes.
        :rtype: list[Node]
        """

        children: list[Node] = []
        for output in self.outputs:
            for child_socket in output.list_connections():
                children.append(child_socket.node)
        if recursive:
            for child_node in children:
                children += child_node.list_children(recursive=True)

        return children

    def list_exec_children(self) -> list[Node]:
        """
        Returns list with all connected executable children.

        :return: children executable nodes.
        :rtype: list[Node]
        """

        executable_children: list[Node] = []
        for exec_output in self.list_exec_outputs():
            executable_children += [child_socket.node for child_socket in exec_output.list_connections()]

        return executable_children

    def update_affected_outputs(self):
        """Updates affected output sockets for each one of the inputs.
        """

        for input_socket in self.inputs:
            input_socket.update_affected()

    def edit_title(self):
        """
        Enables node title edit mode.
        """

        if not self.TITLE_EDITABLE:
            logger.warning(f'Title for node {self.title} is not editable')
            return

        self.view.title_item.edit()

    def attributes_widget(self) -> attributes.AttributesWidget:
        """
        Returns attribute editor widget for this node.

        :return: attribute editor widget.
        :rtype: attributes.AttributesWidget
        """

        return self.ATTRIBUTES_WIDGET(self)

    def _exec(self) -> int:
        """
        Internal function that handles node execution logic shared by all nodes.

        :return: execution code.
        :rtype: int
        """

        logger.debug(f'Executing {self}....')
        self._is_executing = True

        qt.QApplication.processEvents()
        self._graphics_node.update()

        try:
            self.execute()
            self.update_affected_outputs()
            self.set_compiled(True)
            self.set_invalid(False)
        except Exception:
            logger.exception(f'Failed to execute {self.title} {self}')
            self.append_tooltip('Execution error (Check script editor for details)\n')
            self.set_invalid(True)
            raise
        finally:
            self._is_executing = False
            self._graphics_node.update()

        return 0

    def _setup_settings(self):
        """
        Internal function that initializes node settings.
        """

        self._socket_spacing = 32

    def _setup_sockets(self, reset: bool = True):
        """
        Internal function that creates default sockets for this node.

        :param bool reset: whehther to remove already existing sockets.
        """

        self._required_inputs.clear()
        self._exec_in_socket = None
        self._exec_out_socket = None
        if reset:
            self.remove_existing_sockets()

        if self.__class__.IS_EXEC and self.__class__.AUTO_INIT_EXECS:
            self._exec_in_socket = self.add_input(datatypes.Exec)
            self._exec_out_socket = self.add_output(datatypes.Exec, max_connections=1)

        self.setup_sockets()

    def _setup_signals(self):
        """
        Internal function that setup node signals.
        """

        self.signals.compiledChanged.connect(self._on_compiled_changed)
        self.signals.invalidChanged.connect(self._on_invalid_change)
        self.signals.titleEdited.connect(self._on_title_edited)

    def _on_num_sockets_changed(self):
        """
        Internal callback function that is called each time number of sockets for this node changes.
        """

        self._graphics_node.update_size()

    def _on_compiled_changed(self, state: bool):
        """
        Internal callback function that is called each time node compile status changes.

        :param bool state: node compile status.
        """

        self.mark_children_compiled(state)

    def _on_invalid_change(self, state: bool):
        """
        Internal callback function that is called each time node invalid status changes.

        :param bool state: node invalid status.
        """

        if state:
            logger.warning(f'{self} marked as invalid')

    def _on_title_edited(self, new_title: str):
        """
        Internal callback function that is called each time node title changes.

        :param str new_title: new node title.
        """

        new_title = new_title or self.DEFAULT_TITLE
        old_title = self.title
        self.title = new_title
        self.graph.history.store_history(f'Renamed Node {old_title} -> {new_title}')
