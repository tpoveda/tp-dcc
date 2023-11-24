from __future__ import annotations

import typing
from typing import List, Dict, Iterable, Iterator

from overrides import override

from tp.core import log
from tp.maya import api
from tp.maya.meta import base
from tp.libs.rig.noddle import consts
from tp.libs.rig.noddle.core import hook as core_hook, control
from tp.libs.rig.noddle.maya.meta import component
from tp.libs.rig.noddle.maya.functions import naming, attributes, outliner, rig

if typing.TYPE_CHECKING:
    from tp.libs.rig.noddle.maya.meta.components.character import Character

logger = log.tpLogger


class AnimComponent(component.Component):

    ID = 'noddleAnimComponent'

    def character(self) -> Character:
        """
        Returns character this animation component belongs to.

        :return: character instance.
        :rtype: Character
        """

        return base.MetaBase(list(self.attribute('character').destinationNodes())[0].object())

    def root_group(self) -> api.DagNode:
        """
        Returns this animation component root group.

        :return: root group.
        :rtype: api.DagNode
        """

        return self.sourceNodeByName('rootGroup')

    def controls_group(self) -> api.DagNode:
        """
        Returns this animation component controls group.

        :return: root group.
        :rtype: api.DagNode
        """

        return self.sourceNodeByName('controlsGroup')

    def joints_group(self) -> api.DagNode:
        """
        Returns this animation component joints group.

        :return: root group.
        :rtype: api.DagNode
        """

        return self.sourceNodeByName('jointsGroup')

    def parts_group(self) -> api.DagNode:
        """
        Returns this animation component parts group.

        :return: root group.
        :rtype: api.DagNode
        """

        return self.sourceNodeByName('partsGroup')

    def no_scale_group(self) -> api.DagNode:
        """
        Returns this animation component no scale group.

        :return: root group.
        :rtype: api.DagNode
        """

        return self.sourceNodeByName('noScaleGroup')

    def out_group(self) -> api.DagNode:
        """
        Returns this animation component output group.

        :return: root group.
        :rtype: api.DagNode
        """

        return self.sourceNodeByName('outGroup')

    @override
    def meta_attributes(self) -> list[dict]:

        attrs = super().meta_attributes()

        attrs.extend([
            dict(name='character', type=api.kMFnMessageAttribute),
            dict(name='rootGroup', type=api.kMFnMessageAttribute),
            dict(name='controlsGroup', type=api.kMFnMessageAttribute),
            dict(name='jointsGroup', type=api.kMFnMessageAttribute),
            dict(name='partsGroup', type=api.kMFnMessageAttribute),
            dict(name='noScaleGroup', type=api.kMFnMessageAttribute),
            dict(name='outGroup', type=api.kMFnMessageAttribute),
            dict(name='bindJoints', type=api.kMFnMessageAttribute, isArray=True),
            dict(name='ctlChain', type=api.kMFnMessageAttribute, isArray=True),
            dict(name='controls', type=api.kMFnMessageAttribute, isArray=True),
            dict(name='outHooks', type=api.kMFnMessageAttribute, isArray=True),
            dict(name='inHook', type=api.kMFnMessageAttribute),
        ])

        return attrs

    @override(check_signature=False)
    def setup(
            self, parent: AnimComponent | None = None, component_name: str = 'animComponent', side: str = 'c',
            tag: str = 'body', character: Character | None = None):

        super().setup(parent=parent, component_name=component_name, side=side or parent.side(), tag=tag)

        root_group = api.factory.create_dag_node(naming.generate_name(component_name, side, suffix='comp'), 'transform')
        controls_group = api.factory.create_dag_node(
            naming.generate_name(component_name, side, suffix='ctls'), 'transform', parent=root_group)
        joints_group = api.factory.create_dag_node(
            naming.generate_name(component_name, side, suffix='jnts'), 'transform', parent=root_group)
        parts_group = api.factory.create_dag_node(
            naming.generate_name(component_name, side, suffix='parts'), 'transform', parent=root_group)
        no_scale_group = api.factory.create_dag_node(
            naming.generate_name(component_name, side, suffix='noscale'), 'transform', parent=parts_group)
        no_scale_group.inheritsTransform.set(False)
        out_group = api.factory.create_dag_node(
            naming.generate_name(component_name, side, suffix='out'), 'transform', parent=root_group)
        out_group.setVisible(False)

        attributes.add_meta_parent_attribute(
            [root_group, controls_group, joints_group, parts_group, no_scale_group, out_group])

        root_group.attribute(consts.MPARENT_ATTR_NAME).connect(self.rootGroup)
        controls_group.attribute(consts.MPARENT_ATTR_NAME).connect(self.controlsGroup)
        joints_group.attribute(consts.MPARENT_ATTR_NAME).connect(self.jointsGroup)
        parts_group.attribute(consts.MPARENT_ATTR_NAME).connect(self.partsGroup)
        no_scale_group.attribute(consts.MPARENT_ATTR_NAME).connect(self.noScaleGroup)
        out_group.attribute(consts.MPARENT_ATTR_NAME).connect(self.outGroup)

        self.set_outliner_color(17)

        self.connect_to_character(character, parent=False)

    @override(check_signature=False)
    def parent_component(self) -> AnimComponent | None:
        """
        Returns the parent for this animation component.

        :return: animation parent component.
        :rtype: AnimComponent or None
        """

        return super().parent_component()

    @override(check_signature=False)
    def attach_to_component(
            self, parent_component: AnimComponent, hook_index: int | None = None) -> core_hook.Hook | None:
        """
        Attaches this component into the given parent component.

        :param AnimComponent parent_component: component we want to attach this component under.
        :param int hook_index: optional attach point index.
        :return: attach object instance(hook) used to connect the components.
        :rtype: hook.Hook or None
        """

        if not parent_component:
            return None

        super().attach_to_component(parent_component=parent_component)

        if hook_index is not None:
            try:
                found_hook = parent_component.hook(hook_index)
                found_hook.add_output(self)
            except Exception:
                logger.error(f'Failed to connect {self} to {parent_component} at point {hook_index}')
                raise

    def set_outliner_color(self, color: int | str | Iterable[float, float, float]):
        """
        Sets the color of the animatable component root control within outliner panel.

        :param int or str or Iterable[float, float, float] color: outliner color to set.
        """

        outliner.set_color(self.root_group(), color)

    def scale_controls(self, scale_dict: Dict[control.Control, float]):
        """
        Scale given controls shapes.

        :param Dict[Control, float] scale_dict: dictionary with controls as values and their scale values as keys.
        """

        clamped_size = 1.0
        if self.character() and self.character().clamped_size() > 1.0:
            clamped_size = self.character().clamped_size()

        for control, factor in scale_dict.items():
            control.scale_shapes(clamped_size, factor=factor)

    def iterate_bind_joints(self) -> Iterator[api.Joint]:
        """
        Generator function that iterates over all bind joints of this component.

        :return: iterated bind joints.
        :rtype: Iterator[api.Joint]
        """

        for joint_plug in self.attribute('bindJoints'):
            joint_node = joint_plug.sourceNode()
            if not joint_node:
                continue
            yield joint_node

    def bind_joints(self) -> List[api.Joint]:
        """
        Returns all bind joints of this component.

        :return: bind joints.
        :rtype: List[api.Joint]
        """

        return list(self.iterate_bind_joints())

    def iterate_control_joints(self) -> Iterator[api.Joint]:
        """
        Generator function that iterates over all control joints of this component.

        :return: iterated control joints.
        :rtype: Iterator[api.Joint]
        """

        for joint_plug in self.attribute('ctlChain'):
            joint_node = joint_plug.sourceNode()
            if not joint_node:
                continue
            yield joint_node

    def control_joints(self) -> List[api.Joint]:
        """
        Returns all control joints of this component.

        :return: control joints.
        :rtype: List[api.Joint]
        """

        return list(self.iterate_control_joints())

    def iterate_controls(self) -> Iterator[control.Control]:
        """
        Generator function that iterates over all controls of this component.

        :return: iterated controls.
        :rtype: Iterator[control.Control]
        """

        for control_plug in self.attribute('controls'):
            control_node = control_plug.sourceNode()
            if not control_node:
                continue
            yield control.Control(node=control_node.object())

    def controls(self) -> List[control.Control]:
        """
        Returns all controls of this component.

        :return: controls.
        :rtype: List[control.Control]
        """

        return list(self.iterate_controls())

    def add_hook(self, node: api.DagNode, name: str) -> core_hook.Hook:
        """
        Adds given node as a new hook for this component, so other components can attach to this one using this
        attach point( hook).

        :param api.DagNode node: node that will be set as attach point to this component.
        :param str name: name of the hook.
        :return: newly added hook instance.
        :rtype: hook.Hook
        """

        return core_hook.Hook.create(anim_component=self, node=node, name=name)

    def hook(self, index: int) -> core_hook.Hook | None:
        """
        Returns the component attach point at given index.

        :param int index: attach point index.
        :return: found attach point (hook) at given index.
        :rtype: hook.Hook or None
        """

        found_hook = None
        try:
            found_hook = self.out_hooks()[index]
        except IndexError:
            pass

        return found_hook

    def iterate_out_hooks(self) -> Iterator[core_hook.Hook]:
        """
        Generator function that iterates over all output hooks.

        :return: iterated output hooks.
        :rtype: Iterator[core_hook.Hook]
        """

        out_plugs = self.attribute('outHooks')
        for i in range(out_plugs.evaluateNumElements()):
            out_plug = out_plugs.elementByPhysicalIndex(i)
            source = out_plug.sourceNode()
            if source is None:
                continue
            yield core_hook.Hook(source.object())

    def out_hooks(self) -> List[core_hook.Hook]:
        """
        Returns all output hooks.

        :return: output hooks.
        :rtype: List[core_hook.Hook]
        """

        return list(self.iterate_out_hooks())

    def in_hook(self) -> core_hook.Hook | None:
        """
        Returns the input hook for this component.

        :return: input hook.
        :rtype: core_hook.Hook or None
        """

        in_node = self.sourceNodeByName('inHook')
        return core_hook.Hook(node=in_node.object()) if in_node else None

    def connect_to_character(
            self, character_component: Character | None = None, character_name: str | None = None,
            parent: bool = False):
        """
        Connects component to given character.

        :param character.Character character_component: character component we want to connect this animation
            component to.
        :param str character_name: name of the character.
        :param bool parent: whether to parent this component root group into character component control rig group.
        :raises RuntimeError: if no character is given, a no characters were found within current scene.
        :raises RuntimeError: if given character is not a valid one.
        """

        from tp.libs.rig.noddle.maya.meta.components import character

        if not character_component:
            if character_name:
                all_characters = base.find_meta_nodes_by_class_type(character.Character)
                if not all_characters:
                    raise RuntimeError('No characters found within current scene!')
                for character_meta in all_characters:
                    if character_meta.characterName.get() == character_name:
                        character_component = character_meta
                        break
            else:
                character_component = rig.get_build_character()

        if not isinstance(character_component, character.Character):
            raise RuntimeError(f'"{character_component}" is not a valid character!')

        if self not in character_component.components():
            self.attribute('character').connect(
                character_component.attribute(consts.MCHILDREN_ATTR_NAME).nextAvailableDestElementPlug())

        if parent:
            self.root_group().setParent(character_component.control_rig_group())

    def attach_to_skeleton(self):
        """
        Attaches component into character skeleton.
        """

        logger.info(f'{self} Attaching to skeleton...')
        for control_joint, bind_joint in zip(self.control_joints(), self.bind_joints()):
            if not self.character().IGNORE_EXISTING_CONSTRAINTS_ON_SKELETON_ATTACHMENT:
                found_parent_constraint = None
                for _, destination_plug in bind_joint.iterateConnections(source=False):
                    node = destination_plug.node()
                    if node and node.apiType() == api.kParentConstraint:
                        found_parent_constraint = node
                        break
                if found_parent_constraint:
                    logger.info(f'Replacing {bind_joint} attachment to {control_joint}')
                    found_parent_constraint.delete()
            _, parent_constraint_nodes = api.build_constraint(
                bind_joint,
                drivers={
                    'targets': (
                        (control_joint.fullPathName(partial_name=True, include_namespace=False), control_joint),)
                },
                constraint_type='parent', maintainOffset=True
            )
            self.add_util_nodes(parent_constraint_nodes)

    def _connect_bind_joints(self, joint_chain: List[api.Joint]):
        """
        Internal function that connects given joint chain as the bind joint chain
        of this component.

        :param List[api.Joint] joint_chain: joint chain to bind to this component.
        """

        attributes.add_meta_parent_attribute(joint_chain)
        for jnt in joint_chain:
            if jnt not in [plug.sourceNode() for plug in self.attribute('bindJoints')]:
                jnt.attribute(base.MPARENT_ATTR_NAME).connect(
                    self.attribute('bindJoints').nextAvailableDestElementPlug())

    def _connect_control_joints(self, joint_chain: List[api.Joint]):
        """
        Internal function that connects given joint chain as the control joint chain
        of this component.

        :param List[api.Joint] joint_chain: joint chain to control this component.
        """

        attributes.add_meta_parent_attribute(joint_chain)
        for jnt in joint_chain:
            if jnt not in [plug.sourceNode() for plug in self.attribute('ctlChain')]:
                jnt.attribute(base.MPARENT_ATTR_NAME).connect(
                    self.attribute('ctlChain').nextAvailableDestElementPlug())

    def _connect_controls(self, controls: List[control.Control]):
        """
        Internal function that connects given control as the controls of this component.

        :param List[Control] controls: controls to control this component.
        """

        for found_control in controls:
            if found_control not in [plug.sourceNode() for plug in self.attribute('controls')]:
                found_control.attribute(base.MPARENT_ATTR_NAME).connect(
                    self.attribute('controls').nextAvailableDestElementPlug())
