from __future__ import annotations

from typing import Any

from overrides import override

from tp.libs.rig.noddle.core.components import spine
from tp.tools.rig.noddle.builder.graph.nodes import noddle_component
from tp.tools.rig.noddle.builder import api


class SpineNode(noddle_component.AnimComponentNode):

    ID = None
    IS_EXEC = True
    ICON = 'body.png'
    DEFAULT_TITLE = 'Spine'
    CATEGORY = 'Components'
    UNIQUE = False
    COMPONENT_CLASS = spine.SpineComponent

    @override
    def setup_sockets(self):
        super().setup_sockets()

        self.in_name.set_value('spine')
        self.in_tag.set_value('body')
        self.out_self.data_type = api.DataType.SpineComponent


class FKIKSpineNode(SpineNode):

    ID = 8
    DEFAULT_TITLE = 'FKIK Spine'
    COMPONENT_CLASS = spine.FKIKSpineComponent

    @override
    def setup_sockets(self):
        super().setup_sockets()

        self.out_self.data_type = api.DataType.FkIkSpineComponent

        self.in_start_joint = self.add_input(api.dt.String, label='Start Joint', value=None)
        self.in_end_joint = self.add_input(api.dt.String, label='End Joint', value=None)
        self.in_up_axis = self.add_input(api.dt.String, label='Up Axis', value='y')
        self.in_forward_axis = self.add_input(api.dt.String, label='Forward Axis', value='x')
        self.mark_input_as_required(self.in_start_joint)

        self.out_hook_root = self.add_output(
            api.dt.Numeric, label='Hook Root', value=self.COMPONENT_CLASS.Hooks.ROOT.value)
        self.out_hook_hips = self.add_output(
            api.dt.Numeric, label='Hook Hips', value=self.COMPONENT_CLASS.Hooks.HIPS.value)
        self.out_hook_mid = self.add_output(
            api.dt.Numeric, label='Hook Mid', value=self.COMPONENT_CLASS.Hooks.MID.value)
        self.out_hook_chest = self.add_output(
            api.dt.Numeric, label='Hook Chest', value=self.COMPONENT_CLASS.Hooks.CHEST.value)

    @override
    def execute(self) -> Any:
        self._component_instance = self.COMPONENT_CLASS()


def register_plugin(register_node: callable, register_function: callable, register_data_type: callable):
    register_data_type(
        'SpineComponent', spine.SpineComponent,
        api.DataType.COMPONENT.get('color'), label='Spine', default_value=None)
    register_data_type(
        'FkIkSpineComponent', spine.FKIKSpineComponent,
        api.DataType.COMPONENT.get('color'), label='Spine', default_value=None)

    register_node(FKIKSpineNode.ID, FKIKSpineNode)
