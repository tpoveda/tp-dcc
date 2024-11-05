from __future__ import annotations

import json
from abc import abstractmethod
from typing import Iterator, Any

from maya import cmds
from maya.api import OpenMaya

from .om import attributetypes, nodes
from . import factory
from .wrapper import node_by_name, DGNode, DagNode, Plug

CONSTRAINT_TYPES = ("parent", "point", "orient", "scale", "aim", "matrix")
TP_CONSTRAINTS_ATTR_NAME = "tpConstraints"
TP_CONSTRAINT_TYPE_ATTR_NAME = "tpConstraintType"
TP_CONSTRAINT_KWARGS_ATTR_NAME = "tpConstraintKwargs"
TP_CONSTRAINT_CONTROLLER_ATTR_NAME = "tpConstraintController"
TP_CONSTRAINT_CONTROL_ATTR_NAME = "tpConstraintControlAttrName"
TP_CONSTRAINT_TARGETS_ATTR_NAME = "tpConstraintTargets"
TP_CONSTRAINT_SPACE_LABEL_ATTR_NAME = "tpConstraintSpaceLabel"
TP_CONSTRAINT_SPACE_TARGET_ATTR_NAME = "tpConstraintSpaceTarget"
TP_CONSTRAINT_NODES_ATTR_NAME = "tpConstraintNodes"
TP_CONSTRAINT_TYPE_INDEX = 0
TP_CONSTRAINT_KWARGS_INDEX = 1
TP_CONSTRAINT_CONTROLLER_INDEX = 2
TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX = 3
TP_CONSTRAINT_TARGETS_INDEX = 4
TP_CONSTRAINT_SPACE_LABEL_INDEX = 0
TP_CONSTRAINT_SPACE_TARGET_INDEX = 1
TP_CONSTRAINT_NODES_INDEX = 5


class Constraint:
    """
    Base class to create constraints.
    """

    ID: str = ""
    CONSTRAINT_TARGET_INDEX: int | None = None

    def __init__(
        self,
        driven: DagNode | None = None,
        plug_element: Plug | None = None,
        track: bool = True,
    ):
        super().__init__()

        if driven and not plug_element or (plug_element and not driven):
            raise ValueError(
                "if driven or plug_element are specified, both of them must be specified"
            )

        self._driven = driven
        self._plug_element = plug_element
        self._track = track
        self._constraint_node: DGNode | None = None

    @property
    def plug_element(self) -> Plug:
        """
        Getter method that returns the constraint plug element.

        :return:
        """

        return self._plug_element

    @property
    def constraint_node(self) -> DGNode:
        """
        Getter method that returns the constraint node.

        :return: constraint node.
        """

        return self._constraint_node

    @abstractmethod
    def build(self, drivers: dict, **constraint_kwargs: dict[str, Any]) -> list[DGNode]:
        """
        Builds the constraint with given keyword arguments.

        :param drivers: dictionary containing the targets nodes to be driven by the constraint.
        :param constraint_kwargs: constraint keyword arguments.
        :return: list of created nodes.
        """

        raise NotImplementedError("Build method must be implemented in subclasses")

    def driven(self) -> DagNode | None:
        """
        Returns constraint driven node.

        :return: driven node.
        """

        return self._driven

    def set_driven(self, node: DagNode, plug_element: Plug):
        """
        Sets the driven node for the constraint.

        :param base.DagNode node: driven node.
        :param plug_element: plug element
        """

        self._driven = node
        self._plug_element = plug_element

    def iterate_drivers(self) -> Iterator[tuple[str, DagNode]]:
        """
        Generator function that iterates over all driver nodes of the constraint.

        :return: iterated driver nodes.
        """

        if not self._plug_element:
            return

        for target_element in self._plug_element.child(TP_CONSTRAINT_TARGETS_INDEX):
            source_node = target_element.child(
                TP_CONSTRAINT_SPACE_TARGET_INDEX
            ).sourceNode()
            label = target_element.child(TP_CONSTRAINT_SPACE_LABEL_INDEX).value()
            if label:
                yield label, source_node

    def drivers(self) -> list[tuple[str, DagNode]]:
        """
        Returns all driver nodes of the constraint.

        :return: list of driver nodes.
        """

        return list(self.iterate_drivers())

    def iterate_utility_nodes(self) -> Iterator[DGNode]:
        """
        Generator function that iterates over all the constraint utility nodes.

        :return: iterated utility nodes.
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

    def utility_nodes(self) -> list[DGNode]:
        """
        Returns all utility nodes of the constraint.

        :return: list of utility nodes.
        """

        return list(self.iterate_utility_nodes())

    def has_target(self, node: DagNode) -> bool:
        """
        Returns whether this constraint is affecting the given target.

        :param node: node to check.
        :return: True if given node is being affected by this constraint; False otherwise.
        """

        for _, target in self.iterate_drivers():
            if target == node:
                return True

        return False

    def has_target_label(self, label: str) -> bool:
        """
        Returns whether this constraint is affecting a target with given label.

        :param label: target label to check.
        :return: True if given target label is being affected by this constraint; False otherwise.
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
        """

        if self._plug_element is None:
            return ""

        return self._plug_element.child(TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX).value()

    def controller(self) -> dict:
        """
        Returns the controller data.

        :return: controller data.
        """

        if self._plug_element is None:
            return {"node": None, "attr": None}

        source_plug = self._plug_element.child(TP_CONSTRAINT_CONTROLLER_INDEX).source()
        if source_plug is None:
            return {"node": None, "attr": None}
        controller = source_plug.node()

        return {
            "node": controller,
            "attr": source_plug.node().attribute(
                self._plug_element.child(TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX).value()
            ),
        }

    def serialize(self) -> dict:
        """
        Serializes this constraint into a dictionary.

        :return: serialized constraint.
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
        controller_source = self._plug_element.child(
            TP_CONSTRAINT_CONTROLLER_INDEX
        ).source()
        controller_node = (
            controller_source.node() if controller_source is not None else None
        )

        return {
            "targets": targets,
            "kwargs": kwargs,
            "controller": (
                controller_node,
                self._plug_element.child(TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX).value(),
            ),
            "type": self.ID,
        }

    def add_utility_node(self, node: DGNode):
        """
        Adds a utility node to the constraint.

        :param node: utility node to add.
        """

        if self._plug_element is None:
            return

        element = self._plug_element.child(
            TP_CONSTRAINT_NODES_INDEX
        ).nextAvailableDestElementPlug()
        node.mesasge.connect(element)

    def add_utility_nodes(self, nodes_to_add: list[DGNode]):
        """
        Adds a list of utility nodes to the constraint.

        :param nodes_to_add: list of utility nodes to add.
        """

        if self._plug_element is None:
            return

        for node in nodes_to_add:
            element = self._plug_element.child(
                TP_CONSTRAINT_NODES_INDEX
            ).nextAvailableDestElementPlug()
            node.message.connect(element)

    def delete(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """
        Deletes constraint.

        :param mod: optional modifier to add to.
        :param apply: whether to immediately apply the operation.
        :return: True if the constraint was deleted successfully; False otherwise.
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
        controller_node = self._plug_element.child(
            TP_CONSTRAINT_CONTROLLER_INDEX
        ).sourceNode()
        if controller_node is not None:
            attr_name = self._plug_element.child(
                TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX
            ).value()
            control_attr = controller_node.attribute(attr_name)
            if control_attr is not None:
                control_attr.delete(mod=mod, apply=apply)

        if mod is not None:
            mod.doIt()

        # remove multi instance element plug
        # noinspection PyBroadException
        try:
            self._plug_element.delete(mod=mod, apply=apply)
        except Exception:
            if mod is not None:
                mod.doIt()
            return True

        return True


class ParentConstraint(Constraint):
    """
    Parent constraint class.
    """

    ID = "parent"
    CONSTRAINT_TARGET_INDEX = 1
    CONSTRAINT_FN = "parentConstraint"

    def build(self, drivers: dict, **constraint_kwargs: dict[str, Any]) -> list[DGNode]:
        """
        Builds the constraint with given keyword arguments.

        :param drivers: dictionary containing the targets nodes to be driven by the constraint.
        :param constraint_kwargs: constraint keyword arguments.
        :return: list of created nodes.
        """

        space_node: DagNode | None = drivers.get("spaceNode")
        attr_name = drivers.get("attributeName", "parent")
        target_info = drivers["targets"]
        default_driver_label = drivers.get("label", "")

        # check whether the constraint needs to be rebuilt if the request node is the same as the current target
        new_target_structure = dict(self.iterate_drivers())
        new_target_structure.update(dict(target_info))
        requires_update = False
        for index, (request_label, request_node) in enumerate(target_info):
            existing_target = new_target_structure.get(request_label)
            if existing_target is not None or existing_target != request_node:
                requires_update = True
            new_target_structure[request_label] = request_node
        if not requires_update:
            return []

        indexing: list[int] = [
            index for index, (_, request_node) in enumerate(target_info) if request_node
        ]

        if self._track:
            self.delete()

        driven = self.driven()
        cmds_fn = getattr(cmds, self.CONSTRAINT_FN)
        constraint_kwargs = {str(k): v for k, v in constraint_kwargs.items()}
        target_nodes = [target for _, target in new_target_structure.items() if target]

        self.pre_construct_constraint(driven, target_nodes, constraint_kwargs)

        constraint = cmds_fn(
            [target.fullPathName() for target in target_nodes],
            driven.fullPathName(),
            **constraint_kwargs,
        )[0]
        constraint = node_by_name(constraint)

        self.post_construct_constraint(
            driven, target_nodes, constraint, constraint_kwargs
        )

        self._constraint_node = constraint

        if not space_node:
            if self._track:
                add_constraint_map(
                    target_info,
                    driven,
                    None,
                    "",
                    [constraint],
                    self.ID,
                    meta_element_plug=self._plug_element,
                    kwargs_map=constraint_kwargs,
                )
            return [constraint]

        space_attr = space_node.attribute(attr_name)
        try:
            default_index = list(new_target_structure.keys()).index(
                default_driver_label
            )
        except ValueError:
            default_index = 0

        if space_attr is not None:
            space_attr.setFields(list(new_target_structure.keys()))
        else:
            space_attr = space_node.addAttribute(
                attr_name,
                type=attributetypes.kMFnkEnumAttribute,
                keyable=True,
                channelBox=False,
                locked=False,
                enums=list(new_target_structure.keys()),
                default=default_index,
                value=default_index,
            )

        target_array = constraint.target
        source_short_name = constraint.fullPathName(
            partial_name=True, include_namespace=False
        )

        conditions: list[DGNode] = []
        constraint_target_weight_index = self.CONSTRAINT_TARGET_INDEX
        for i, target_element in enumerate(target_array):
            target_element_weight = target_element.child(constraint_target_weight_index)
            target_weight_source = target_element_weight.source()
            if target_weight_source is None:
                target_weight_source = target_element_weight

            target_node = target_element.child(0).source().node()
            target_short_name = target_node.fullPathName(
                partial_name=True, include_namespace=False
            )

            condition = factory.create_condition_vector(
                first_term=space_attr,
                second_term=float(indexing[i]),
                color_if_true=(1.0, 0.0, 0.0),
                color_if_false=(0.0, 0.0, 0.0),
                operation=0,
                name="_".join([target_short_name, source_short_name, self.ID, "space"]),
            )
            condition.outColorR.connect(target_weight_source)
            conditions.append(condition)

        if self._track:
            add_constraint_map(
                target_info,
                driven,
                space_node,
                attr_name,
                conditions + [constraint],
                self.ID,
                meta_element_plug=self._plug_element,
                kwargs_map=constraint_kwargs,
            )

        return conditions + [constraint]

    def pre_construct_constraint(
        self,
        driven: DagNode,
        target_nodes: list[DagNode],
        constraint_kwargs: dict[str, Any],
    ):
        """
        Function that is called before the constraint is created.

        :param DagNode driven: constraint driven node.
        :param target_nodes: list of target nodes.
        :param constraint_kwargs: constraint keyword arguments.
        """

        pass

    def post_construct_constraint(
        self,
        driven: DagNode,
        target_nodes: list[DagNode],
        constraint: DagNode,
        constraint_kwargs: dict[str, Any],
    ):
        """
        Function that is called after the constraint is created.

        :param driven: constraint driven node.
        :param target_nodes: list of target nodes.
        :param constraint: created constraint node.
        :param constraint_kwargs: constraint keyword arguments.
        """

        pass


class PointConstraint(ParentConstraint):
    """
    Point constraint class.
    """

    ID = "point"
    CONSTRAINT_TARGET_INDEX = 4
    CONSTRAINT_FN = "pointConstraint"

    def pre_construct_constraint(
        self,
        driven: DagNode,
        target_nodes: list[DagNode],
        constraint_kwargs: dict[str, Any],
    ):
        """
        Function that is called before the constraint is created.

        :param DagNode driven: constraint driven node.
        :param target_nodes: list of target nodes.
        :param constraint_kwargs: constraint keyword arguments.
        """

        # point constraint maintain offset has a bug when we add multiple targets with maintain offset and introduces
        # offset so here we manage the translation offset ourselves

        first_target = target_nodes[0]
        if constraint_kwargs.get("maintainOffset"):
            # noinspection PyAttributeOutsideInit
            self._translation_offset = driven.translation(
                space=OpenMaya.MSpace.kWorld
            ) - first_target.translation(space=OpenMaya.MSpace.kWorld)

    def post_construct_constraint(
        self,
        driven: DagNode,
        target_nodes: list[DagNode],
        constraint: DagNode,
        constraint_kwargs: dict[str, Any],
    ):
        """
        Function that is called after the constraint is created.

        :param driven: constraint driven node.
        :param target_nodes: list of target nodes.
        :param constraint: created constraint node.
        :param constraint_kwargs: constraint keyword arguments.
        """

        if constraint_kwargs.get("maintainOffset"):
            constraint.offset.set(self._translation_offset)


class OrientConstraint(ParentConstraint):
    """
    Orient constraint class.
    """

    ID = "orient"
    CONSTRAINT_TARGET_INDEX = 4
    CONSTRAINT_FN = "orientConstraint"


class ScaleConstraint(ParentConstraint):
    """
    Scale constraint class.
    """

    ID = "scale"
    CONSTRAINT_TARGET_INDEX = 2
    CONSTRAINT_FN = "scaleConstraint"


class AimConstraint(ParentConstraint):
    """
    Aim constraint class.
    """

    ID = "aim"
    CONSTRAINT_TARGET_INDEX = 4
    CONSTRAINT_FN = "aimConstraint"


class MatrixConstraint(Constraint):
    """
    Matrix constraint class.
    """

    ID = "matrix"

    def build(
        self,
        drivers: dict,
        decompose: bool = False,
        **constraint_kwargs: dict[str, Any],
    ) -> list[DGNode]:
        """
        Builds the constraint with given keyword arguments.

        :param drivers: dictionary containing the targets nodes to be driven by the constraint.
        :param decompose: whether to decompose the matrix.
        :param constraint_kwargs: constraint keyword arguments.
        :return: list of created nodes.
        """

        if int(OpenMaya.MGlobal.mayaVersion()) >= 2020 and not decompose:
            return MatrixConstraint._build_offset_parent_matrix_constraint(
                self.ID, self.driven(), drivers, self._track, **constraint_kwargs
            )

        return MatrixConstraint._build_matrix_constraint(
            self.ID, self.driven(), drivers, self._track, **constraint_kwargs
        )

    @classmethod
    def _build_offset_parent_matrix_constraint(
        cls,
        constraint_id: str,
        driven: DagNode,
        drivers: dict,
        track: bool = True,
        **constraint_kwargs: dict[str, Any],
    ) -> list[DGNode]:
        """
        Internal function that creates an offset parent matrix constraint.

        :param constraint_id: constraint type.
        :param driven: constraint driven node.
        :param drivers: dictionary containing targets info.
        :param track: whether the constraint and all nodes created should be tracked via metadata.
        :param constraint_kwargs: extra constraint keyword arguments.
        :return: list of constraint related nodes created.
        """

        maintain_offset = constraint_kwargs.get("maintainOffset", False)
        skip_translate = constraint_kwargs.get("skipTranslate", [False, False, False])
        skip_rotate = constraint_kwargs.get("skipRotate", [False, False, False])
        skip_scale = constraint_kwargs.get("skipScale", [False, False, False])
        name = driven.fullPathName(partial_name=True, include_namespace=False)
        target_info = drivers["targets"]
        _, target_nodes = zip(*target_info)
        driver = target_nodes[0]
        compose_name = "_".join([name, "pickMtx"])
        skip_translate = any(i for i in skip_translate)
        skip_rotate = any(i for i in skip_rotate)
        skip_scale = any(i for i in skip_scale)
        utilities = []

        current_world_matrix = driven.worldMatrix()
        if any((skip_scale, skip_translate, skip_rotate)):
            pick_matrix = factory.create_dg_node(compose_name, "pickMatrix")
            driver.attribute("worldMatrix")[0].connect(pick_matrix.inputMatrix)
            pick_matrix.useTranslate = not skip_translate
            pick_matrix.useRotate = not skip_rotate
            pick_matrix.useScale = not skip_scale
            pick_matrix.outputMatrix.connect(driven.offsetParentMatrix)
            utilities.append(pick_matrix)
        else:
            driver.attribute("worldMatrix")[0].connect(driven.offsetParentMatrix)

        if maintain_offset:
            driven.setMatrix(
                current_world_matrix * driven.offsetParentMatrix.value().inverse()
            )
        else:
            driven.resetTransform(translate=True, rotate=True, scale=True)

        if track:
            add_constraint_map(
                target_info,
                driven,
                None,
                "",
                utilities,
                constraint_id,
                None,
                kwargs_map=constraint_kwargs,
            )

        return utilities

    @classmethod
    def _build_matrix_constraint(
        cls,
        constraint_id: str,
        driven: DagNode,
        drivers: dict,
        track: bool = True,
        **constraint_kwargs: dict[str, Any],
    ) -> list[DGNode]:
        """
        Internal function that creates a matrix constraint.

        :param constraint_id: constraint type.
        :param driven: constraint driven node.
        :param drivers: dictionary containing targets info.
        :param track: whether the constraint and all nodes created should be tracked via metadata.
        :param constraint_kwargs: extra constraint keyword arguments.
        :return: list of constraint related nodes created.
        """

        def _compose_joint_matrix_rotation_graph() -> list[DGNode]:
            """
            Internal function that creates a joint matrix rotation graph.

            :return: list of created nodes.
            """

            if all(not i for i in skip_rotate):
                return []

            _joint_orient = OpenMaya.MEulerRotation(driven.jointOrient.value())
            _transform = OpenMaya.MTransformationMatrix()
            _transform.setRotation(_joint_orient)
            _extras = []
            if driven_parent is not None:
                _joint_orient_matrix_inverse = factory.create_dg_node(
                    name + "_orientMatInv", "inverseMatrix"
                )
                _joint_orient_matrix = factory.create_mult_matrix(
                    name + "_orientMat",
                    inputs=(_transform.asMatrix(), parent_world_matrix),
                    output=_joint_orient_matrix_inverse.inputMatrix,
                )
                _orient_offset = _joint_orient_matrix_inverse.outputMatrix
                _extras = [_joint_orient_matrix, _joint_orient_matrix_inverse]
            else:
                _orient_offset = _transform.asMatrixInverse()

            _joint_local_matrix = factory.create_mult_matrix(
                name + "_localRotMtx",
                inputs=(offset, driver.worldMatrixPlug(), _orient_offset),
                output=None,
            )
            _decompose = factory.create_decompose(
                name + "_outputRotMtx",
                input_matrix_plug=_joint_local_matrix.matrixSum,
                destination=driven,
                translate_values=(False, False, False),
                scale_values=(False, False, False),
                rotation_values=skip_rotate or (),
            )
            driver.rotateOrder.connect(decompose.inputRotateOrder)
            _extras.extend([_joint_local_matrix, _decompose])
            return _extras

        def _compose_joint_matrix_translate_scale_graph() -> list[DGNode]:
            """
            Internal function that creates a joint matrix translation/rotation graph.

            :return: list of created nodes.
            """

            if all(not i for i in skip_translate) and all(not i for i in skip_scale):
                return []
            _inputs = (
                [offset, driver.worldMatrixPlug()]
                if maintain_offset
                else [driver.worldMatrixPlug()]
            )
            if driven_parent is not None:
                _inputs.append(driven_parent.worldInverseMatrixPlug())
            _mult_matrix = factory.create_mult_matrix(
                name + "_outputTSMat", inputs=inputs, output=None
            )
            _decompose = factory.create_decompose(
                name + "_outputTSDecomp",
                input_matrix_plug=_mult_matrix.matrixSum,
                destination=driven,
                translate_values=skip_translate,
                scale_values=skip_scale,
                rotation_values=(False, False, False),
            )
            driver.rotateOrder.connect(_decompose.inputRotateOrder)
            return [_mult_matrix, _decompose]

        maintain_offset = constraint_kwargs.get("maintainOffset", False)
        skip_translate = constraint_kwargs.get("skipTranslate", [False, False, False])
        skip_rotate = constraint_kwargs.get("skipRotate", [False, False, False])
        skip_scale = constraint_kwargs.get("skipScale", [False, False, False])
        name = driven.fullPathName(partial_name=True, include_namespace=False)
        target_info = drivers["targets"]
        _, target_nodes = zip(*target_info)
        driver = target_nodes[0]
        is_joint = driven.apiType() == OpenMaya.MFn.kJoint
        driven_parent = driven.parent()
        parent_world_matrix = (
            driven_parent.worldMatrixPlug()
            if driven_parent
            else driven.parentMatrix[0].value()
        )
        offset = nodes.offset_matrix(driver.object(), driven.object())

        utilities = []
        if is_joint:
            utilities.extend(_compose_joint_matrix_rotation_graph())
            utilities.extend(_compose_joint_matrix_translate_scale_graph())
        else:
            if maintain_offset:
                offset = nodes.offset_matrix(driver.object(), driven.object())
                inputs = [offset, driver.attribute("worldMatrix")[0]]
                if driven_parent is not None:
                    inputs.append(driven_parent.worldInverseMatrixPlug())
                offset_name = "_".join([name, "wMtxOffset"])
                mult_matrix = factory.create_mult_matrix(
                    offset_name,
                    inputs=inputs,
                    output=None,
                )
                output_plug = mult_matrix.matrixSum
                utilities.append(mult_matrix)
            else:
                output_plug = driver.attribute("worldMatrix")[0]
            compose_name = "_".join([name, "wMtxCompose"])
            decompose = factory.create_decompose(
                compose_name,
                destination=driven,
                translate_values=skip_translate or (),
                rotation_values=skip_rotate or (),
                scale_values=skip_scale or (),
            )
            driver.rotateOrder.connect(decompose.inputRotateOrder)
            output_plug.connect(decompose.inputMatrix)
            utilities.append(decompose)

        if track:
            add_constraint_map(
                target_info,
                driven,
                None,
                "",
                utilities,
                constraint_id,
                None,
                kwargs_map=constraint_kwargs,
            )

        return utilities


CONSTRAINT_CLASSES = {
    "parent": ParentConstraint,
    "point": PointConstraint,
    "orient": OrientConstraint,
    "scale": ScaleConstraint,
    "aim": AimConstraint,
    "matrix": MatrixConstraint,
}


def create_constraint_factory(
    constraint_type: str,
    driven_node: DagNode,
    constraint_meta_plug: Plug,
    track: bool = True,
) -> Constraint:
    """
    Factory function that allows to create different Constraint classes based on given type.

    :param constraint_type: type of the attribute to create.
    :param driven_node: node to drive.
    :param constraint_meta_plug: constraint plug.
    :param track: whether the constraint and all nodes created should be tracked via metadata.
    :return: new constraint instance.
    :raises NotImplementedError: if given constraint type is not supported.
    """

    constraint_class = CONSTRAINT_CLASSES.get(constraint_type)
    if constraint_class is None:
        raise NotImplementedError(
            f"Constraint of type {constraint_type} is not supported"
        )

    constraint_instance = constraint_class(track=track)
    constraint_instance.set_driven(driven_node, constraint_meta_plug)

    return constraint_instance


def iterate_constraints(node: DagNode) -> Iterator[Constraint]:
    """
    Generator function that iterates over all attached constraints by iterating over the compound array attribute
    called "constraints".

    :param node: node to iterate.
    :return: iterated constraints.
    """

    array = node.attribute(TP_CONSTRAINTS_ATTR_NAME)
    if array is None:
        return
    for plug_element in array:
        type_value = plug_element.child(0).value()
        if not type_value:
            continue
        yield create_constraint_factory(type_value, node, plug_element)


def find_constraint(node: DagNode, constraint_type: str) -> Constraint | None:
    """
    Finds a constraint of given type attached to the given node.

    :param node: node to search for attached constraints.
    :param constraint_type: constraint type to search for.
    :return: constraint instance if found; None otherwise.
    """

    found_constraint: Constraint | None = None
    for element in node.attribute(TP_CONSTRAINTS_ATTR_NAME):
        type_value = element.child(0).value()
        if type_value != constraint_type:
            continue
        found_constraint = create_constraint_factory(constraint_type, node, element)
        break

    return found_constraint


def has_constraint(node: DagNode) -> bool:
    """
    Returns whether this node is constrained by another.

    :param node: node to search for attached constraints.
    :return: True if node is attached to a constraint; False otherwise.
    """

    for _ in iterate_constraints(node):
        return True

    return False


def add_constraint_attribute(node: DagNode) -> Plug:
    """
    Creates and returns the "constraints" compound attribute, which is used to store all incoming constraints no
    matter how they are created. If the attribute already exists, it will be returned.

    :param node: node to create compound attribute in.
    :return: constraint compound attribute.
    """

    if node.hasAttribute(TP_CONSTRAINTS_ATTR_NAME):
        return node.attribute(TP_CONSTRAINTS_ATTR_NAME)

    constraint_plug = node.addCompoundAttribute(
        name=TP_CONSTRAINTS_ATTR_NAME,
        type=attributetypes.kMFnCompoundAttribute,
        isArray=True,
        attr_map=[
            dict(name=TP_CONSTRAINT_TYPE_ATTR_NAME, type=attributetypes.kMFnDataString),
            dict(
                name=TP_CONSTRAINT_KWARGS_ATTR_NAME, type=attributetypes.kMFnDataString
            ),
            dict(
                name=TP_CONSTRAINT_CONTROLLER_ATTR_NAME,
                type=attributetypes.kMFnMessageAttribute,
            ),
            dict(
                name=TP_CONSTRAINT_CONTROL_ATTR_NAME, type=attributetypes.kMFnDataString
            ),
            dict(
                name=TP_CONSTRAINT_TARGETS_ATTR_NAME,
                type=attributetypes.kMFnCompoundAttribute,
                isArray=True,
                children=[
                    dict(
                        name=TP_CONSTRAINT_SPACE_LABEL_ATTR_NAME,
                        type=attributetypes.kMFnDataString,
                    ),
                    dict(
                        name=TP_CONSTRAINT_SPACE_TARGET_ATTR_NAME,
                        type=attributetypes.kMFnMessageAttribute,
                    ),
                ],
            ),
            dict(
                name=TP_CONSTRAINT_NODES_ATTR_NAME,
                type=attributetypes.kMFnMessageAttribute,
                isArray=True,
            ),
        ],
    )

    return constraint_plug


def build_constraint(
    driven: DagNode,
    drivers: dict,
    constraint_type: str = "parent",
    track: bool = True,
    **kwargs,
) -> tuple[Constraint, list[DGNode]]:
    """
    Builds a space switching ready constraint.

    :param DagNode driven: transform to drive.
    :param drivers: a dict containing the target information. e.g:
        {
            'targets': (
                (driver_guide.fullPathName(partial_name=True, include_namespace=False), driver_guide),
            )
        }
    :param constraint_type: constraint type.
    :param track: whether the constraint and all nodes created should be tracked via metadata.
    :keyword bool maintainOffset: whether to maintain offset transformation after constraint is applied.
    :return: tuple containing the constraint instance and the constraint extra nodes.
    """

    assert (
        constraint_type in CONSTRAINT_TYPES
    ), f"Constraint of type: {constraint_type} is not supported"

    constraint_attr = None
    if track:
        attr_name = drivers.get("attributeName", "")
        for last_constraint in iterate_constraints(driven):
            if attr_name and attr_name == last_constraint.controller_attr_name():
                utilities = last_constraint.build(drivers, **kwargs)
                return last_constraint, utilities
            constraint_attr = last_constraint.plug_element
        if constraint_attr is None:
            constraint_attr = add_constraint_attribute(driven)[0]
        else:
            latest_constraint_index = constraint_attr.logicalIndex()
            constraint_attr = driven.attribute(TP_CONSTRAINTS_ATTR_NAME)[
                latest_constraint_index + 1
            ]

    constraint = create_constraint_factory(
        constraint_type, driven, constraint_attr, track=track
    )

    return constraint, constraint.build(drivers, **kwargs)


def delete_constraints(
    constrained_nodes: list[DagNode], mod: OpenMaya.MDagModifier | None = None
) -> OpenMaya.MDagModifier:
    """
    Deletes all the constraints of the given nodes.

    :param constrained_nodes: nodes we want to delete constraints of.
    :param mod: optional modifier to add to.
    :return: modifier used to run the operation.
    """

    mod = mod or OpenMaya.MDagModifier()
    for constrained_node in constrained_nodes:
        for constraint in iterate_constraints(constrained_node):
            constraint.delete(mod=mod, apply=False)
        # we need to separate the disconnect from the deletion to avoid crashes.
        mod.doIt()
        delete_constraint_map_attribute(constrained_node, mod=mod)

    return mod


def add_constraint_map(
    drivers: list[DagNode],
    driven: DagNode,
    controller: DGNode | None,
    controller_attr_name: str,
    utilities: list[DGNode],
    constraint_type: str,
    meta_element_plug: Plug | None,
    kwargs_map: dict | None = None,
) -> Plug:
    """
    Adds a mapping of drivers and utilities to the constraint compound array attribute.

    :param drivers: list of driver nodes.
    :param driven: driven node.
    :param controller: optional node that will be connected to controller plug through its message attribute.
    :param controller_attr_name: controller attribute name.
    :param utilities: list of constraint extra nodes.
    :param constraint_type: constraint type.
    :param meta_element_plug: element plug.
    :param kwargs_map: optional keyword arguments for the constraint.
    :return: plug where constraint attributes where added.
    """

    kwargs_map = kwargs_map or dict()
    compound_plug = add_constraint_attribute(driven)
    if not meta_element_plug:
        for element in compound_plug:
            element_constraint_type = element.child(TP_CONSTRAINT_TYPE_INDEX).value()
            if (
                not element_constraint_type
                or element_constraint_type == constraint_type
            ):
                meta_element_plug = element
                break
            if meta_element_plug is None:
                meta_element_plug = compound_plug[0]
    constraint_type_plug = meta_element_plug.child(TP_CONSTRAINT_TYPE_INDEX)
    kwargs_plug = meta_element_plug.child(TP_CONSTRAINT_KWARGS_INDEX)

    if controller is not None:
        controller_plug = meta_element_plug.child(TP_CONSTRAINT_CONTROLLER_INDEX)
        controller_name_plug = meta_element_plug.child(
            TP_CONSTRAINT_CONTROL_ATTR_NAME_INDEX
        )
        controller.message.connect(controller_plug)
        controller_name_plug.set(controller_attr_name)

    targets_plug = meta_element_plug.child(TP_CONSTRAINT_TARGETS_INDEX)
    constraints_plug = meta_element_plug.child(TP_CONSTRAINT_NODES_INDEX)
    constraint_type_plug.set(constraint_type)
    kwargs_plug.set(json.dumps(kwargs_map))

    index: int = 0
    driver_element = targets_plug.nextAvailableDestElementPlug()
    for driver_label, driver in drivers:
        index += 1
        driver_element.child(TP_CONSTRAINT_SPACE_LABEL_INDEX).set(driver_label)
        if driver:
            driver.message.connect(
                driver_element.child(TP_CONSTRAINT_SPACE_TARGET_INDEX)
            )
        driver_element = targets_plug[index]

    for constraint_node in utilities:
        constraint_node.message.connect(constraints_plug.nextAvailableDestElementPlug())

    return compound_plug


def delete_constraint_map_attribute(
    node: DGNode, mod: OpenMaya.MDGModifier | None = None
) -> OpenMaya.MDGModifier:
    """
    Removes the constraint metadata if it is present on given node.

    :param node: node to remove metadata from.
    :param mod: optional modifier to add to.
    :return: used modifier to run the operation.
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


def serialize_constraints(node: DagNode) -> list[dict]:
    """
    Serializes all constraints of the given node.

    :param node: node to serialize constraints from.
    :return: serialized constraints.
    """

    constraints: list[dict] = []
    if not node.hasAttribute(TP_CONSTRAINTS_ATTR_NAME):
        return constraints

    for constraint in iterate_constraints(node):
        constraint_data = constraint.serialize()
        if not constraint_data:
            continue
        constraints.append(constraint_data)

    return constraints
