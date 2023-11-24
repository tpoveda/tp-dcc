from __future__ import annotations

import json
from typing import Tuple, List, Iterator, Dict
from collections import OrderedDict

from overrides import override

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from tp.common.python import decorators
from tp.maya.cmds import helpers
from tp.maya.api import base, attributetypes, nodes, factory
from tp.maya.om import factory, nodes as om_nodes

CONSTRAINT_TYPES = ('parent', 'point', 'orient', 'scale', 'aim', 'matrix')
TP_CONSTRAINTS_ATTR_NAME = 'tpConstraints'
TP_CONSTRAINT_TYPE_ATTR_NAME = 'tpConstraintType'
TP_CONSTRAINT_KWARGS_ATTR_NAME = 'tpConstraintKwargs'
TP_CONSTRAINT_CONTROLLER_ATTR_NAME = 'tpConstraintController'
TP_CONSTRAINT_CONTROL_ATTR_NAME = 'tpConstraintControlAttrName'
TP_CONSTRAINT_TARGETS_ATTR_NAME = 'tpConstraintTargets'
TP_CONSTRAINT_SPACE_LABEL_ATTR_NAME = 'tpConstraintSpaceLabel'
TP_CONSTRAINT_SPACE_TARGET_ATTR_NAME = 'tpConstraintSpaceTarget'
TP_CONSTRAINT_NODES_ATTR_NAME = 'tpConstraintNodes'
TP_CONSTRAINT_TYPE_INDEX = 0
TP_CONSTRAINT_KWARGS_INDEX = 1
TP_CONSTRAINT_CONTROLLER_INDEX = 2
TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX = 3
TP_CONSTRAINT_TARGETS_INDEX = 4
TP_CONSTRAINT_SPACE_LABEL_INDEX = 0
TP_CONSTRAINT_SPACE_TARGET_INDEX = 1
TP_CONSTRAINT_NODES_INDEX = 5


def has_constraint(node: base.DagNode) -> bool:
    """
    Returns whether this node is constrained by another.

    :param base.DagNode node: node to search for attached constraints.
    :return: True if node is attached to a constraint; False otherwise.
    :rtype: bool
    """

    for i in iterate_constraints(node):
        return True

    return False


def iterate_constraints(node: base.DagNode) -> Iterator[Constraint]:
    """
    Generator function that iterates over all attached constraints by iterating over the compound array attribute
    called "constraints".

    :param base.DagNode node: node to iterate.
    :return: iterated constraints.
    :rtype: Iterator[Constraint]
    """

    array = node.attribute(TP_CONSTRAINTS_ATTR_NAME)
    if array is None:
        return
    for plug_element in array:
        type_value = plug_element.child(0).value()
        if not type_value:
            continue
        yield create_constraint_factory(type_value, node, plug_element)


def create_constraint_factory(
        constraint_type: str, driven_node: base.DagNode, constraint_meta_plug: base.Plug,
        track: bool = True) -> Constraint:
    """
    Factory function that allows to create different Constraint classes based on given type.

    :param str constraint_type: type of the attribute to create.
    :param tp.baseDagNode driven_node: node to drive.
    :param tp.base.Plug constraint_meta_plug: constraint plug.
    :param bool track: whether the constraint and all nodes created should be tracked via metadata.
    :return: new constraint instance.
    :rtype: Constraint
    :raises NotImplementedError: if given constraint type is not supported.
    """

    constraint_class = CONSTRAINT_CLASSES.get(constraint_type)
    if constraint_class is None:
        raise NotImplementedError('Constraint of type {} is not supported'.format(constraint_type))

    constraint_instance = constraint_class(track=track)
    constraint_instance.set_driven(driven_node, constraint_meta_plug)

    return constraint_instance


def add_constraint_attribute(node: base.DagNode) -> base.Plug:
    """
    Creates and returns the "constraints" compound attribute, which is used to store all incoming constraints no
    matter how they are created. If the attribute already exists, it will be returned.

    :param base.DagNode node: node to create compound attribute in.
    :return: constraint compound attribute.
    :rtype: base.Plug
    """

    if node.hasAttribute(TP_CONSTRAINTS_ATTR_NAME):
        return node.attribute(TP_CONSTRAINTS_ATTR_NAME)

    constraint_plug = node.addCompoundAttribute(
        name=TP_CONSTRAINTS_ATTR_NAME, type=attributetypes.kMFnCompoundAttribute, isArray=True, attr_map=[
            dict(name=TP_CONSTRAINT_TYPE_ATTR_NAME, type=attributetypes.kMFnDataString),
            dict(name=TP_CONSTRAINT_KWARGS_ATTR_NAME, type=attributetypes.kMFnDataString),
            dict(name=TP_CONSTRAINT_CONTROLLER_ATTR_NAME, type=attributetypes.kMFnMessageAttribute),
            dict(name=TP_CONSTRAINT_CONTROL_ATTR_NAME, type=attributetypes.kMFnDataString),
            dict(name=TP_CONSTRAINT_TARGETS_ATTR_NAME, type=attributetypes.kMFnCompoundAttribute, isArray=True, children=[
                dict(name=TP_CONSTRAINT_SPACE_LABEL_ATTR_NAME, type=attributetypes.kMFnDataString),
                dict(name=TP_CONSTRAINT_SPACE_TARGET_ATTR_NAME, type=attributetypes.kMFnMessageAttribute)]),
            dict(name=TP_CONSTRAINT_NODES_ATTR_NAME, type=attributetypes.kMFnMessageAttribute, isArray=True)
        ]
    )

    return constraint_plug


def build_constraint(
        driven: base.DagNode, drivers: Dict, constraint_type: str = 'parent', track: bool = True,
        **kwargs) -> Tuple[Constraint, List[base.DagNode]]:
    """
    Builds a space switching ready constraint.

    :param tp.maya.api.base.DagNode driven: transform to drive.
    :param Dict drivers: a dict containing the target information. e.g:
        {
            'targets': (
                (driver_guide.fullPathName(partial_name=True, include_namespace=False), driver_guide),
            )
        }
    :param str constraint_type: constraint type.
    :param bool track: whether the constraint and all nodes created should be tracked via metadata.
    :keyword bool maintainOffset: whether to maintain offset transformation after constraint is applied.
    :return: tuple containing the constraint instance and the constraint extra nodes.
    :rtype: Tuple[Constraint, List[base.DagNode]]
    """

    assert constraint_type in CONSTRAINT_TYPES, 'Constraint of type: {} is not supported'.format(constraint_type)

    constraint_attr = None
    if track:
        attr_name = drivers.get('attributeName', '')
        for last_constraint in iterate_constraints(driven):
            if attr_name and attr_name == last_constraint.controller_attribute_name():
                utilities = last_constraint.build(drivers, **kwargs)
                return last_constraint, utilities
            constraint_attr = last_constraint.plug_element
        if constraint_attr is None:
            constraint_attr = add_constraint_attribute(driven)[0]
        else:
            latest_constraint_index = constraint_attr.logicalIndex()
            constraint_attr = driven.attribute(TP_CONSTRAINTS_ATTR_NAME)[latest_constraint_index + 1]

    constraint = create_constraint_factory(constraint_type, driven, constraint_attr, track=track)

    return constraint, constraint.build(drivers, **kwargs)


def delete_constraints(
        constrained_nodes: List[base.DagNode], mod: OpenMaya.MDagModifier | None = None) -> OpenMaya.MDagModifier:
    """
    Deletes all the constraints of the given nodes.

    :param List[base.DagNode] constrained_nodes: nodes we want to delete constraints of.
    :param OpenMaya.MDagModifier or None mod: optional modifier to add to.
    :return: modifier used to run the operation.
    :rtype: OpenMaya.MDagModifier
    """

    mod = mod or OpenMaya.MDagModifier()
    for constrained_node in constrained_nodes:
        for constraint in iterate_constraints(constrained_node):
            constraint.delete(mod=mod, apply=False)
        delete_constraint_map_attribute(constrained_node, mod=mod)

    return mod


def add_constraint_map(
        drivers: List[base.DagNode], driven: base.DagNode, controller: base.DGNode | None, controller_attr_name: str,
        utilities: List[base.DGNode], constraint_type: str, meta_element_plug: base.Plug | None,
        kwargs_map: Dict | None = None) -> base.Plug:
    """
    Adds a mapping of drivers and utilities to the constraint compound array attribute.

    :param List[base.DagNode] drivers: list of driver nodes.
    :param base.DagNode driven: driven node.
    :param base.DGNode controller: optional node that will be connected to controller plug through its message
        attribute.
    :param str controller_attr_name: controller attribute name.
    :param List[base.DGNode] utilities: list of constraint extra nodes.
    :param str constraint_type: constraint type.
    :param base.Plug or None meta_element_plug: element plug.
    :param Dict or None kwargs_map: optional keyword arguments for the constraint.
    :return: plug where constraint attributes where added.
    """

    kwargs_map = kwargs_map or dict()
    compound_plug = add_constraint_attribute(driven)
    if not meta_element_plug:
        for element in compound_plug:
            element_constraint_type = element.child(TP_CONSTRAINT_TYPE_INDEX).value()
            if not element_constraint_type or element_constraint_type == constraint_type:
                meta_element_plug = element
                break
            if meta_element_plug is None:
                meta_element_plug = compound_plug[0]
    constraint_type_plug = meta_element_plug.child(TP_CONSTRAINT_TYPE_INDEX)
    kwargs_plug = meta_element_plug.child(TP_CONSTRAINT_KWARGS_INDEX)

    if controller is not None:
        controller_plug = meta_element_plug.child(TP_CONSTRAINT_CONTROLLER_INDEX)
        controller_name_plug = meta_element_plug.child(TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX)
        controller.message.connect(controller_plug)
        controller_name_plug.set(controller_attr_name)

    targets_plug = meta_element_plug.child(TP_CONSTRAINT_TARGETS_INDEX)
    constraints_plug = meta_element_plug.child(TP_CONSTRAINT_NODES_INDEX)
    constraint_type_plug.set(constraint_type)
    kwargs_plug.set(json.dumps(kwargs_map))

    index = 0
    driver_element = targets_plug.nextAvailableDestElementPlug()
    for driver_label, driver in drivers:
        index += 1
        driver_element.child(TP_CONSTRAINT_SPACE_LABEL_INDEX).set(driver_label)
        if driver:
            driver.message.connect(driver_element.child(TP_CONSTRAINT_SPACE_TARGET_INDEX))
        driver_element = targets_plug[index]

    for constraint_node in utilities:
        constraint_node.message.connect(constraints_plug.nextAvailableDestElementPlug())

    return compound_plug


def delete_constraint_map_attribute(node: base.DGNode, mod: OpenMaya.MDGModifier | None = None) -> OpenMaya.MDGModifier:
    """
    Removes the constraint metadata if it is present on given node.

    :param base.DGNode node: node to remove metadata from.
    :param OpenMaya.MDGModifier or None mod: optional modifier to add to.
    :return: used modifier to run the operation.
    :rtype: OpenMaya.MDGModifier
    """

    constraint_attr = node.attribute(TP_CONSTRAINTS_ATTR_NAME)
    if constraint_attr is None:
        return mod

    mod = mod or OpenMaya.MDGModifier()
    if constraint_attr.numConnectedElements() > 0:
        for attr in constraint_attr:
            if attr.numConnectedChildren() < 1:
                continue
            target_attr = attr.child(4)
            controller_attr = attr.child(2)
            extra_nodes_attr = attr.child(5)
            controller_attr.disconnectAll(mod=mod)
            if target_attr.numConnectedElements() > 0:
                for element in target_attr:
                    if element.numConnectedElements() < 1:
                        continue
                    element.child(1).disconnectAll(mod=mod)
            if extra_nodes_attr.numConnectedElements() < 1:
                continue
            for element in extra_nodes_attr:
                element.disconnectAll(mod=mod)

    # we need to separate the disconnect from the deletion to avoid crashes.
    mod.doIt()
    constraint_attr.delete(mod=mod)

    return mod


class Constraint:

    ID = ''
    CONSTRAINT_TARGET_INDEX = None

    def __init__(self, driven: base.DagNode | None = None, plug_element: base.Plug | None = None, track: bool = True):
        super().__init__()

        if driven and not plug_element or (plug_element and not driven):
            raise ValueError('if driven or plug_element are specified, both of them must be specified')

        self._driven = driven
        self._plug_element = plug_element
        self._track = track
        self._constraint_node: base.DGNode | None = None

    @property
    def plug_element(self) -> base.Plug:
        return self._plug_element

    @property
    def constraint_node(self) -> base.DGNode:
        return self._constraint_node

    @decorators.abstractmethod
    def build(self, drivers: Dict, **constraint_kwargs: Dict) -> List[base.DGNode]:
        """
        Builds the constraint with given keyword arguments.

        :param Dict drivers: dictionary containing the targets nodes to be driven by the constraint.
        :param Dict constraint_kwargs: constraint keyword arguments.
        :return: list of created nodes.
        :rtype: List[base.DGNode]
        """

        raise NotImplementedError('Build method must be implemented in subclasses')

    def driven(self) -> base.DagNode | None:
        """
        Returns constraint driven node.

        :return: driven node.
        :rtype: base.DagNode or None
        """

        return self._driven

    def set_driven(self, node: base.DagNode, plug_element: base.Plug):
        """
        Sets the driven node for the constraint.

        :param base.DagNode node: driven node.
        :param base.Plug plug_element: plug element
        """

        self._driven = node
        self._plug_element = plug_element

    def iterate_drivers(self) -> Iterator[Tuple[str, base.DagNode]]:
        """
        Generator function that iterates over all driver nodes of the constraint.

        :return: iterated driver nodes.
        :rtype: Iterator[Tuple[str, base.DagNode]]
        """

        if not self._plug_element:
            return

        for target_element in self._plug_element.child(TP_CONSTRAINT_TARGETS_INDEX):
            source_node = target_element.child(TP_CONSTRAINT_SPACE_TARGET_INDEX).sourceNode()
            label = target_element.child(TP_CONSTRAINT_SPACE_LABEL_INDEX).value()
            if label:
                yield label, source_node

    def iterate_utility_nodes(self) -> Iterator[base.DGNode]:
        """
        Generator function that iterates over all the constraint utility nodes.

        :return: iterated utility nodes.
        :rtype: Iterator[base.DGNode]
        """

        if self._plug_element is None:
            return

        for target_plug in self._plug_element.child(TP_CONSTRAINT_NODES_INDEX):
            source_plug = target_plug.source()
            if not source_plug:
                continue
            util_node = source_plug.node()
            if util_node is None:
                continue
            yield util_node

    def has_target(self, node: base.DagNode) -> bool:
        """
        Returns whether this constraint is affecting the given target.

        :param base.DagNode node: node to check.
        :return: True if given node is being affected by this constraint; False otherwise.
        :rtype: bool
        """

        for _, target in self.iterate_drivers():
            if target == node:
                return True

        return False

    def has_target_label(self, label: str) -> bool:
        """
        Returns whether this constraint is affecting a target with given label.

        :param str label: target label to check.
        :return: True if given target label is being affected by this constraint; False otherwise.
        :rtype: bool
        """

        if self._plug_element is None:
            return False

        for target_element in self._plug_element.child(TP_CONSTRAINT_TARGETS_INDEX):
            if target_element.child(TP_CONSTRAINT_SPACE_LABEL_INDEX).value() == label:
                return True

        return False

    def controller_attr_name(self) -> str:
        """
        Returns the attribute name which controls this constraint.

        :return: controller attribute name.
        :rtype: str
        """

        if self._plug_element is None:
            return ''

        return self._plug_element.child(TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX).value()

    def controller(self) -> Dict:
        """
        Returns the controller data.

        :return: controller data.
        :rtype: Dict
        """

        if self._plug_element is None:
            return {'node': None, 'attr': None}

        source_plug = self._plug_element.child(TP_CONSTRAINT_CONTROLLER_INDEX).source()
        if source_plug is None:
            return {'node': None, 'attr': None}
        controller = source_plug.node()

        return {
            'node': controller,
            'attr': source_plug.node().attribute(self._plug_element.child(TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX).value())
        }

    def serialize(self) -> Dict:
        """
        Serializes this constraint into a dictionary.

        :return: serialized constraint.
        :rtype: Dict
        """

        if self._plug_element is None:
            return {}

        sources = self._plug_element[TP_CONSTRAINT_TARGETS_INDEX]
        kwargs_str = self._plug_element[TP_CONSTRAINT_KWARGS_INDEX].value()
        try:
            kwargs = json.loads(kwargs_str)
        except ValueError:
            kwargs = {}
        targets = []
        for source in sources:
            label = source.child(TP_CONSTRAINT_SPACE_LABEL_INDEX).value()
            target = source.child(TP_CONSTRAINT_SPACE_TARGET_INDEX).sourceNode()
            if not target:
                continue
            targets.append((label, target))
        if not targets:
            return {}
        controller_source = self._plug_element.child(TP_CONSTRAINT_CONTROLLER_INDEX).source()
        controller_node = controller_source.node() if controller_source is not None else None

        return {
            'targets': targets,
            'kwargs': kwargs,
            'controller': (controller_node, self._plug_element.child(TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX).value()),
            'type': self.ID
        }

    def delete(self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True) -> bool:
        """
        Deletes constraint.

        :param OpenMaya.MDGModifier or None mod: optional modifier to add to.
        :param bool apply: whether to immediately apply the operation.
        :return: True if the constraint was deleted successfully; False otherwise.
        :rtype: bool
        """

        # disconnect connections from utilities nodes and delete them
        for target_plug in self._plug_element.child(TP_CONSTRAINT_NODES_INDEX):
            source_plug = target_plug.source()
            if not source_plug:
                continue
            util_node = source_plug.node()
            for source_plug, dest_plug in util_node.iterateConnections(True, False):
                source_plug.disconnect(dest_plug, mod=mod, apply=apply)
            util_node.delete(mod=mod, apply=False)

        # delete control attribute
        controller_node = self._plug_element.child(TP_CONSTRAINT_CONTROLLER_INDEX).sourceNode()
        if controller_node is not None:
            attr_name = self._plug_element.child(TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX).value()
            control_attr = controller_node.attribute(attr_name)
            if control_attr is not None:
                control_attr.delete(mod=mod, apply=apply)

        # remove multi instance element plug
        self._plug_element.delete(mod=mod, apply=apply)

        return True


class ParentConstraint(Constraint):

    ID = 'parent'
    CONSTRAINT_TARGET_INDEX = 1
    CONSTRAINT_FN = 'parentConstraint'

    @override
    def build(self, drivers: Dict, **constraint_kwargs: Dict) -> List[base.DGNode]:

        space_node = drivers.get('spaceNode')
        attr_name = drivers.get('attributeName', 'parent')
        target_info = drivers['targets']
        default_driver_label = drivers.get('label', '')

        # check whether the constraint needs to be rebuilt if the request node is the same as the current target
        new_target_structure = OrderedDict(self.iterate_drivers())
        new_target_structure.update(OrderedDict(target_info))
        requires_update = False
        for index, (request_label, request_node) in enumerate(target_info):
            existing_target = new_target_structure.get(request_label)
            if existing_target is not None or existing_target != request_node:
                requires_update = True
            new_target_structure[request_label] = request_node
        if not requires_update:
            return []

        indexing = [index for index, (_, request_node) in enumerate(target_info) if request_node]

        if self._track:
            self.delete()

        driven = self.driven()
        cmds_fn = getattr(cmds, self.CONSTRAINT_FN)
        constraint_kwargs = {str(k): v for k, v in constraint_kwargs.items()}
        target_nodes = [target for _, target in new_target_structure.items() if target]

        self.pre_construct_constraint(driven, target_nodes, constraint_kwargs)

        constraint = cmds_fn(
            [target.fullPathName() for target in target_nodes], driven.fullPathName(), **constraint_kwargs)[0]
        constraint = base.node_by_name(constraint)

        self.post_construct_constraint(driven, target_nodes, constraint, constraint_kwargs)

        self._constraint_node = constraint

        if not space_node:
            if self._track:
                add_constraint_map(
                    target_info, driven, None, '', [constraint], self.ID, meta_element_plug=self._plug_element,
                    kwargs_map=constraint_kwargs)
            return [constraint]

        raise NotImplementedError('Space Switch Setup not implemented yet!')

    def pre_construct_constraint(self, driven: base.DagNode, target_nodes: List[base.DagNode], constraint_kwargs: Dict):
        """
        Function that is called before the constraint is created.

        :param base.DagNode driven: constraint driven node.
        :param List[base.DagNode] target_nodes: list of target nodes.
        :param Dict constraint_kwargs: constraint keyword arguments.
        """

        pass

    def post_construct_constraint(
            self, driven: base.DagNode, target_nodes: List[base.DagNode], constraint: base.DagNode,
            constraint_kwargs: Dict):
        """
        Function that is called after the constraint is created.

        :param base.DagNode driven: constraint driven node.
        :param List[base.DagNode] target_nodes: list of target nodes.
        :param base.DagNode constraint: created constraint node.
        :param dict constraint_kwargs: constraint keyword arguments.
        """

        pass


class PointConstraint(ParentConstraint):

    ID = 'point'
    CONSTRAINT_TARGET_INDEX = 4
    CONSTRAINT_FN = 'pointConstraint'

    @override
    def pre_construct_constraint(self, driven: base.DagNode, target_nodes: List[base.DagNode], constraint_kwargs: Dict):

        # point constraint maintain offset has a bug when we add multiple targets with maintain offset and introduces
        # offset so here we manage the translation offset ourselves

        first_target = target_nodes[0]
        if constraint_kwargs.get('maintainOffset'):
            self._translation_offset = driven.translation(
                space=OpenMaya.MSpace.kWorld) - first_target.translation(space=OpenMaya.MSpace.kWorld)

    @override
    def post_construct_constraint(
            self, driven: base.DagNode, target_nodes: List[base.DagNode], constraint: base.DagNode,
            constraint_kwargs: Dict):

        if constraint_kwargs.get('maintainOffset'):
            constraint.offset.set(self._translation_offset)


class OrientConstraint(ParentConstraint):

    ID = 'orient'
    CONSTRAINT_TARGET_INDEX = 4
    CONSTRAINT_FN = 'orientConstraint'


class ScaleConstraint(ParentConstraint):

    ID = 'scale'
    CONSTRAINT_TARGET_INDEX = 2
    CONSTRAINT_FN = 'scaleConstraint'


class AimConstraint(ParentConstraint):

    ID = 'aim'
    CONSTRAINT_TARGET_INDEX = 4
    CONSTRAINT_FN = 'aimConstraint'


class MatrixConstraint(Constraint):

    ID = 'matrix'

    @override(check_signature=False)
    def build(self, drivers: Dict, decompose: bool = False, **constraint_kwargs: Dict) -> List[base.DGNode]:

        if helpers.maya_version() >= 2020 and not decompose:
            return MatrixConstraint._build_offset_parent_matrix_constraint(
                self.ID, self.driven(), drivers, self._track, **constraint_kwargs)

        return MatrixConstraint._build_matrix_constraint(
            self.ID, self.driven(), drivers, self._track, **constraint_kwargs)

    @classmethod
    def _build_offset_parent_matrix_constraint(
            cls, constraint_id: str, driven: base.DagNode, drivers: Dict, track: bool = True,
            **constraint_kwargs: Dict) -> List[base.DGNode]:
        """
        Internal function that creates an offset parent matrix constraint.

        :param str constraint_id: constraint type.
        :param base.DagNode driven: constraint driven node.
        :param Dict drivers: dictionary containing targets info.
        :param bool track: whether the constraint and all nodes created should be tracked via metadata.
        :param Dict constraint_kwargs: extra constraint keyword arguments.
        :return: list of constraint related nodes created.
        :rtype: List[base.DGNode]
        """

        maintain_offset = constraint_kwargs.get('maintainOffset', False)
        skip_translate = constraint_kwargs.get('skipTranslate', [False, False, False])
        skip_rotate = constraint_kwargs.get('skipRotate', [False, False, False])
        skip_scale = constraint_kwargs.get('skipScale', [False, False, False])
        name = driven.fullPathName(partial_name=True, include_namespace=False)
        target_info = drivers['targets']
        _, target_nodes = zip(*target_info)
        driver = target_nodes[0]
        compose_name = '_'.join([name, 'pickMtx'])
        skip_translate = any(i for i in skip_translate)
        skip_rotate = any(i for i in skip_rotate)
        skip_scale = any(i for i in skip_scale)
        utilities = []

        current_world_matrix = driven.worldMatrix()
        if any((skip_scale, skip_translate, skip_rotate)):
            pick_matrix = factory.create_dg_node(compose_name, 'pickMatrix')
            driver.attribute('worldMatrix')[0].connect(pick_matrix.inputMatrix)
            pick_matrix.useTranslate = not skip_translate
            pick_matrix.useRotate = not skip_rotate
            pick_matrix.useScale = not skip_scale
            pick_matrix.outputMatrix.connect(driven.offsetParentMatrix)
            utilities.append(pick_matrix)
        else:
            driver.attribute('worldMatrix')[0].connect(driven.offsetParentMatrix)

        if maintain_offset:
            driven.setMatrix(current_world_matrix * driven.offsetParentMatrix.value().inverse())
        else:
            driven.resetTransform(translate=True, rotate=True, scale=True)

        if track:
            add_constraint_map(
                target_info, driven, None, '', utilities, constraint_id, None, kwargs_map=constraint_kwargs)

        return utilities

    @classmethod
    def _build_matrix_constraint(
            cls, constraint_id: str, driven: base.DagNode, drivers: Dict, track: bool = True,
            **constraint_kwargs: Dict) -> List[base.DGNode]:
        """
        Internal function that creates a matrix constraint.

        :param str constraint_id: constraint type.
        :param base.DagNode driven: constraint driven node.
        :param Dict drivers: dictionary containing targets info.
        :param bool track: whether the constraint and all nodes created should be tracked via metadata.
        :param Dict constraint_kwargs: extra constraint keyword arguments.
        :return: list of constraint related nodes created.
        :rtype: List[base.DGNode]
        """

        maintain_offset = constraint_kwargs.get('maintainOffset', False)
        skip_translate = constraint_kwargs.get('skipTranslate', [False, False, False])
        skip_rotate = constraint_kwargs.get('skipRotate', [False, False, False])
        skip_scale = constraint_kwargs.get('skipScale', [False, False, False])
        name = driven.fullPathName(partial_name=True, include_namespace=False)
        target_info = drivers['targets']
        _, target_nodes = zip(*target_info)
        driver = target_nodes[0]
        compose_name = '_'.join([name, 'wMtxCompose'])
        utilities = []

        if maintain_offset:
            offset = om_nodes.offset_matrix(driver.object(), driven.object())
            offset_name = '_'.join([name, 'wMtxOffset'])
            mult_matrix = factory.create_mult_matrix(
                offset_name, inputs=(offset, driver.attribute('worldMatrix')[0], driven.parentInverseMatrix()),
                output=None)
            output_plug = mult_matrix.matrixSum
            utilities.append(mult_matrix)
        else:
            output_plug = driver.attribute('worldMatrix')[0]

        decompose = factory.create_decompose(
            compose_name, destination=driven, translate_values=skip_translate or (), rotation_values=skip_rotate or (),
            scale_values=skip_scale or ())
        driver.rotateOrder.connect(decompose.inputRotateOrder)
        output_plug.connect(decompose.inputMatrix)
        utilities.append(decompose)

        if track:
            add_constraint_map(
                target_info, driven, None, '', utilities, constraint_id, None, kwargs_map=constraint_kwargs)

        return utilities


CONSTRAINT_CLASSES = {
    'parent': ParentConstraint,
    'point': PointConstraint,
    'orient': OrientConstraint,
    'scale': ScaleConstraint,
    'aim': AimConstraint,
    'matrix': MatrixConstraint
}
