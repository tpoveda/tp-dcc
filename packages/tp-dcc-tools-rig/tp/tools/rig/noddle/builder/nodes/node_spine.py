from __future__ import annotations

from typing import Any

from overrides import override

from tp.libs.rig.noddle.core.components import spine
from tp.tools.rig.noddle.builder import api
from tp.tools.rig.noddle.builder.nodes import node_component


class SpineNode(node_component.AnimComponentNode):

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
        self._component_instance = self.COMPONENT_CLASS(
            character=self.in_character.value(),
            component_name=self.in_name.value(),
            side=self.in_side.value(),
            tag=self.in_tag.value(),
            hook=self.in_hook.value(),
            start_joint=self.in_start_joint.value(),
            end_joint=self.in_end_joint.value(),
            up_axis=self.in_up_axis.value(),
            forward_axis=self.in_forward_axis.value(),
            parent=self.in_meta_parent.value())

        self.out_self.set_value(self._component_instance)


def register_plugin(register_node: callable, register_function: callable, register_data_type: callable):
    register_data_type(
        'SpineComponent', spine.SpineComponent,
        api.DataType.COMPONENT.get('color'), label='Spine', default_value=None)
    register_data_type(
        'FkIkSpineComponent', spine.FKIKSpineComponent,
        api.DataType.COMPONENT.get('color'), label='Spine', default_value=None)

    register_node(FKIKSpineNode.ID, FKIKSpineNode)

    register_function(
        SpineNode.COMPONENT_CLASS.root_control, api.DataType.SpineComponent,
        inputs={'Spine': api.DataType.SpineComponent}, outputs={'Root Control': api.dt.Control},
        nice_name='Root Control', category='Spine')
    register_function(
        SpineNode.COMPONENT_CLASS.hips_control, api.DataType.SpineComponent,
        inputs={'Spine': api.DataType.SpineComponent}, outputs={'Hips Control': api.dt.Control},
        nice_name='Hips Control', category='Spine')
    register_function(
        SpineNode.COMPONENT_CLASS.chest_control, api.DataType.SpineComponent,
        inputs={'Spine': api.DataType.SpineComponent}, outputs={'Chest Control': api.dt.Control},
        nice_name='Chest Control', category='Spine')

    register_function(
        FKIKSpineNode.COMPONENT_CLASS.fk1_control, api.DataType.FkIkSpineComponent,
        inputs={'FKIK Spine': api.DataType.FkIkSpineComponent}, outputs={'FK1 Control': api.dt.Control},
        nice_name='FK1 Control', category='FKIK Spine')
    register_function(
        FKIKSpineNode.COMPONENT_CLASS.fk2_control, api.DataType.FkIkSpineComponent,
        inputs={'FKIK Spine': api.DataType.FkIkSpineComponent}, outputs={'FK2 Control': api.dt.Control},
        nice_name='FK2 Control', category='FKIK Spine')
    register_function(
        FKIKSpineNode.COMPONENT_CLASS.mid_control, api.DataType.FkIkSpineComponent,
        inputs={'FKIK Spine': api.DataType.FkIkSpineComponent}, outputs={'Mid Control': api.dt.Control},
        nice_name='Mid Control', category='FKIK Spine')
    register_function(
        FKIKSpineNode.COMPONENT_CLASS.pivot_control, api.DataType.FkIkSpineComponent,
        inputs={'FKIK Spine': api.DataType.FkIkSpineComponent}, outputs={'Pivot Control': api.dt.Control},
        nice_name='Pivot Control', category='FKIK Spine')
