from __future__ import annotations

from typing import Any

from overrides import override

from tp.core import log
from tp.libs.rig.noddle.core import asset
from tp.tools.rig.noddle.builder import api

logger = log.tpLogger


class GraphInputNode(api.NoddleNode):

    ID = 101
    IS_EXEC = True
    AUTO_INIT_EXECS = False
    ICON = 'input.png'
    DEFAULT_TITLE = 'Input'
    CATEGORY = 'Utils'
    UNIQUE = True

    @property
    def out_asset_name(self) -> api.OutputSocket:
        return self._out_asset_name

    @override
    def setup_sockets(self):
        self._exec_out_socket = self.add_output(api.dt.Exec)
        self._out_asset_name = self.add_output(api.dt.String, label='Asset Name', value='')

    @override
    def execute(self) -> Any:
        if not asset.Asset.get():
            logger.error('Asset is not set')
            raise ValueError

        self.out_asset_name.set_value(asset.Asset.get().name)


class GraphOutputNode(api.NoddleNode):

    ID = 102
    IS_EXEC = True
    AUTO_INIT_EXECS = False
    ICON = 'output.png'
    DEFAULT_TITLE = 'Output'
    CATEGORY = 'Utils'
    UNIQUE = True

    @property
    def in_character(self) -> api.InputSocket:
        return self._in_character

    @override
    def setup_sockets(self):
        self._exec_in_socket = self.add_output(api.dt.Exec)
        self._in_character = self.add_input(api.dt.Character, label='Character')
        self.mark_input_as_required(self._in_character)


def register_plugin(register_node: callable, register_function: callable, register_data_type: callable):
    register_node(GraphInputNode.ID, GraphInputNode)
    register_node(GraphOutputNode.ID, GraphOutputNode)
