from __future__ import annotations

from typing import Callable

from overrides import override

from tp.core import log
from tp.tools.rig.noddle.builder import api

logger = log.tpLogger


class ConstantNode(api.NoddleNode):
    IS_EXEC = False
    DEFAULT_TITLE = 'Constant'
    STATUS_ICON = False
    ICON = None
    CATEGORY = 'Constants'
    MIN_WIDTH = 100
    CONSTANT_DATA_TYPE = None

    def __init__(self, graph: api.NodeGraph):
        self._data_type = getattr(api.DataType, self.CONSTANT_DATA_TYPE)
        super().__init__(graph)
        self.update_title()

    @override
    def setup_sockets(self):
        self.out_value = self.add_output(self._data_type, label='Value', value=None)

    @override
    def _setup_signals(self):
        super()._setup_signals()

        self.out_value.signals.valueChanged.connect(self.update_title)

    def update_title(self):
        """
        Updates constant node title.
        """

        self.title = f'{self.DEFAULT_TITLE}: {self.out_value.value()}'


class ConstantBoolNode(ConstantNode):
    ID = 12
    CONSTANT_DATA_TYPE = 'BOOLEAN'
    DEFAULT_TITLE = 'Boolean'


class ConstantFloatNode(ConstantNode):
    ID = 13
    CONSTANT_DATA_TYPE = 'NUMERIC'
    DEFAULT_TITLE = 'Number'


class ConstantStringNode(ConstantNode):
    ID = 14
    CONSTANT_DATA_TYPE = 'STRING'
    DEFAULT_TITLE = 'String'


def register_plugin(register_node: Callable, register_function: Callable, register_data_type: Callable):
    register_node(ConstantBoolNode.ID, ConstantBoolNode)
    register_node(ConstantStringNode.ID, ConstantFloatNode)
    register_node(ConstantFloatNode.ID, ConstantStringNode)
