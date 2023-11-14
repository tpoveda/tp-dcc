from __future__ import annotations

from typing import Any

from overrides import override

from tp.libs.rig.noddle.core import character
from tp.tools.rig.noddle.builder import api


class CharacterNode(api.ComponentNode):

    ID = 7
    IS_EXEC = True
    ICON = 'bindpose.png'
    DEFAULT_TITLE = 'Character'
    CATEGORY = 'Components'
    UNIQUE = True
    COMPONENT_CLASS = character.Character

    @override
    def setup_sockets(self):
        super().setup_sockets()

        self.out_self.data_type = api.dt.Character
        self.in_name.set_value('character')
        self.in_tag.set_value('character')

        self.out_root_control = self.add_output(api.dt.Control, label='Root Control')
        self.out_deform_rig = self.add_output(api.dt.String, label='Deformation Rig')
        self.out_control_rig = self.add_output(api.dt.String, label='Control Rig')
        self.out_geometry_group = self.add_output(api.dt.String, label='Geometry Group')

    def execute(self) -> Any:
        self.component_instance = self.COMPONENT_CLASS(
            component_name=self.in_name.value(), tag=self.in_tag.value(), parent=self.in_meta_parent.value())

        self.out_self.set_value(self.component_instance)
        self.out_meta_parent.set_value(
            self.component_instance.meta_parent().fullPathName() if self.component_instance.meta_parent() else None)
        self.out_root_control.set_value(self.component_instance.root_control().fullPathName())
        self.out_deform_rig.set_value(self.component_instance.deformation_rig_group().fullPathName())
        self.out_control_rig.set_value(self.component_instance.control_rig_group().fullPathName())
        self.out_geometry_group.set_value(self.component_instance.geometry_group().fullPathName())


def register_plugin(register_node: callable, register_function: callable, register_data_type: callable):
    register_node(CharacterNode.ID, CharacterNode)
    register_function(
        CharacterNode.COMPONENT_CLASS.control_rig_group, api.dt.Character,
        inputs={'Character': api.dt.Character}, outputs={'Control Rig': api.dt.String},
        nice_name='Get Control Rig', category='Character')
    register_function(
        CharacterNode.COMPONENT_CLASS.deformation_rig_group, api.dt.Character,
        inputs={'Character': api.dt.Character}, outputs={'Deformation Rig': api.dt.String},
        nice_name='Get Deformation Rig', category='Character')
    register_function(
        CharacterNode.COMPONENT_CLASS.geometry_group, api.dt.Character,
        inputs={'Character': api.dt.Character}, outputs={'Geometry Group': api.dt.String},
        nice_name='Get Geometry Group', category='Character')
    register_function(
        CharacterNode.COMPONENT_CLASS.root_control, api.dt.Character,
        inputs={'Character': api.dt.Character}, outputs={'Root Control': api.dt.Control},
        nice_name='Get Root Control', category='Character')
    register_function(
        CharacterNode.COMPONENT_CLASS.world_locator, api.dt.Character,
        inputs={'Character': api.dt.Character}, outputs={'World Locator': api.dt.String},
        nice_name='Get World Locator', category='Character')
