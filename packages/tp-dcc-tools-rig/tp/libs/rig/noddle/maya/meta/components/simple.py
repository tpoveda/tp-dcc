from __future__ import annotations

import typing

from overrides import override

from tp.maya import api
from tp.libs.rig.noddle.core import control
from tp.libs.rig.noddle.maya.meta import animcomponent
from tp.libs.rig.noddle.maya.functions import attributes

if typing.TYPE_CHECKING:
    from tp.libs.rig.noddle.core.hook import Hook
    from tp.libs.rig.noddle.maya.meta.components.character import Character


class SimpleComponent(animcomponent.AnimComponent):

    ID = 'noddleSimple'

    @override(check_signature=False)
    def setup(
            self, parent: animcomponent.AnimComponent | None = None, hook: int | None = None,
            character: Character | None = None, side: str = 'c', component_name: str = 'empty', tag: str = ''):

        super().setup(parent=parent, side=side, component_name=component_name, character=character, tag=tag)

        self.connect_to_character(character_component=character, parent=True)
        self.attach_to_component(parent, hook)

    @override
    def attach_to_skeleton(self):
        pass

    @override
    def attach_to_component(
            self, parent_component: animcomponent.AnimComponent, hook_index: int | None = None) -> Hook | None:
        super().attach_to_component(parent_component=parent_component, hook_index=hook_index)

        in_hook = self.in_hook()
        if in_hook:
            _, parent_constraint_nodes = api.build_constraint(
                self.controls_group(),
                drivers={
                    'targets': ((in_hook.fullPathName(partial_name=True, include_namespace=False), in_hook),)},
                constraint_type='parent'
            )
            self.add_util_nodes(parent_constraint_nodes)

    def add_control(
            self, guide_object: api.DagNode, name: str, as_hook: bool = False, bind_joint: api.Joint | None = None,
            *args, **kwargs) -> control.Control:
        """
        Adds a new control to this component.

        :param api.DagNode guide_object: guide where control will be placed.
        :param str name: name for the control.
        :param bool as_hook: whether to create a hook for this control in this component.
        :param api.Joint or None bind_joint: optional bind joint for the control.
        :return: newly created control.
        :rtype: control.Control
        """

        parent = kwargs.pop('parent', None)

        new_control = control.Control.create(
            name=[self.indexed_name, name], guide=guide_object, parent=self.controls_group(), *args, **kwargs
        )
        self._connect_controls([new_control])

        if parent:
            _, parent_constraint_nodes = api.build_constraint(
                new_control.group,
                drivers={
                    'targets': ((parent.fullPathName(partial_name=True, include_namespace=False), parent),)},
                constraint_type='parent', maintainOffset=True
            )
            self.add_util_nodes(parent_constraint_nodes)

        if as_hook:
            self.add_hook(new_control, new_control.control_name)

        if bind_joint:
            _, parent_constraint_nodes = api.build_constraint(
                bind_joint,
                drivers={
                    'targets': ((new_control.fullPathName(partial_name=True, include_namespace=False), new_control),)},
                constraint_type='parent', maintainOffset=True
            )
            self.add_util_nodes(parent_constraint_nodes)
            attributes.add_meta_parent_attribute([bind_joint])
            self._connect_bind_joints([bind_joint])

        return new_control

    def add_existing_control(
            self, control_to_add: control.Control, as_hook: bool = False, bind_joint: api.Joint | None = None):
        """
        Adds an existing control into this component.

        :param control.Control control_to_add: control instance to add to this component.
        :param bool as_hook: whether to create a hook for this control in this component.
        :param api.Joint or None bind_joint: optional bind joint for the control.
        """

        control_to_add.rename(name='_'.join([self.indexed_name, control_to_add.control_name]))
        if not control_to_add.parent():
            control_to_add.setParent(self.controls_group())

        self._connect_controls([control_to_add])

        if as_hook:
            self.add_hook(control_to_add, control_to_add.control_name)

        if bind_joint:
            _, parent_constraint_nodes = api.build_constraint(
                bind_joint,
                drivers={
                    'targets': ((control_to_add.fullPathName(partial_name=True, include_namespace=False), control_to_add),)},
                constraint_type='parent', maintainOffset=True
            )
            self.add_util_nodes(parent_constraint_nodes)
            attributes.add_meta_parent_attribute([bind_joint])
            self._connect_bind_joints([bind_joint])
