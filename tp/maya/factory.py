from __future__ import annotations

from typing import Iterable, Any

from maya import cmds
from maya.api import OpenMaya

from .om import constants
from .wrapper import (
    node_by_object,
    node_by_name,
    DGNode,
    DagNode,
    Plug,
    Joint,
    IkHandle,
)
from .cmds import decorators
from .om import factory, contexts, curves


def create_dag_node(
    name: str,
    node_type: str,
    parent: DagNode | None = None,
    mod: OpenMaya.MDagModifier | None = None,
    apply: bool = True,
) -> DagNode:
    """
    Creates a new DAG node and if a parent is specified, then parent the new node.

    :param name: name of the DAG node to create.
    :param node_type: type of the DAG node to create.
    :param parent: optional parent.
    :param mod: optional Maya modifier to apply.
    :param apply: whether to apply modifier immediately.
    :return: newly created Maya object instance.
    """

    parent_node = parent.object() if parent else None
    return node_by_object(
        factory.create_dag_node(
            name=name, node_type=node_type, parent=parent_node, mod=mod, apply=apply
        )
    )


def create_dg_node(
    name: str,
    node_type: str,
    mod: OpenMaya.MDGModifier | None = None,
    apply: bool = True,
) -> DGNode | Any:
    """
    Creates a dependency graph node and returns the node Maya object.

    :param name: new name of the node.
    :param node_type: Maya node type to create.
    :param mod: optional Maya modifier to apply.
    :param apply: whether to apply modifier immediately.
    :return: newly created Maya object instance.
    """

    return node_by_object(
        factory.create_dg_node(name=name, node_type=node_type, mod=mod, apply=apply)
    )


def create_mult_matrix(
    name: str, inputs: Iterable[Plug], output: Plug | None
) -> DGNode:
    """
    Creates a multMatrix node.

    :param name: name of the node.
    :param inputs: input plugs.
    :param output: output plug.
    :return: created multMatrix node.
    """

    mult_matrix = create_dg_node(name, "multMatrix")
    compound = mult_matrix.matrixIn
    # noinspection PyTypeChecker
    for i in range(1, len(inputs)):
        # noinspection PyUnresolvedReferences
        _input = inputs[i]
        if isinstance(_input, Plug):
            _input.connect(compound.element(i))
            continue
        compound.element(i).set(_input)
    # noinspection PyUnresolvedReferences
    _input = inputs[0]
    if isinstance(_input, Plug):
        _input.connect(compound.element(0))
    else:
        compound.element(0).set(_input)
    if output is not None:
        mult_matrix.matrixSum.connect(output)

    return mult_matrix


def create_decompose(
    name: str,
    destination: DGNode,
    translate_values: Iterable[bool] = (True, True, True),
    rotation_values: Iterable[bool] = (True, True, True),
    scale_values: Iterable[bool] = (True, True, True),
    input_matrix_plug: Plug | None = None,
) -> DGNode:
    """
    Creates decompose node and connects it to the given destination node.

    :param name: name of the node.
    :param destination: node to connect to.
    :param translate_values: X, Y, Z to apply for the translation channel.
    :param rotation_values: X, Y, Z to apply for the rotation channel.
    :param scale_values: X, Y, Z to apply for the scale channel.
    :param input_matrix_plug: optional input matrix plug to connect from.
    :return: created decompose node.
    """

    decompose = create_dg_node(name, "decomposeMatrix")

    if input_matrix_plug is not None:
        input_matrix_plug.connect(decompose.inputMatrix)

    if destination:
        decompose.outputTranslate.connect(
            destination.translate, children=translate_values
        )
        decompose.outputRotate.connect(destination.rotate, children=rotation_values)
        decompose.outputScale.connect(destination.scale, children=scale_values)

    return decompose


def create_reverse(name: str, inputs: Plug | list[Plug], outputs: Plug | list[Plug]):
    """
    Creates a reverse node.

    :param name: name for the reverse node.
    :param inputs: input compound plug or list of plugs.
    :param outputs: output compound plug or list of plugs.
    :return: created reverse node.
    :raises ValueError: if only one input is passed and input plug is not a compound attribute.
    :raises ValueError: if only one output is passed and output plug is not a compound attribute.
    """

    reverse_node = create_dg_node(name, "reverse")
    in_plug = reverse_node.input
    out_plug = reverse_node.output

    if isinstance(inputs, Plug):
        if inputs.isCompound:
            inputs.connect(in_plug)
            return reverse_node
        raise ValueError(
            "inputs argument must be a compound when passing a single plug"
        )
    elif isinstance(outputs, Plug):
        if outputs.isCompound:
            outputs.connect(out_plug)
            return reverse_node
        raise ValueError(
            "outputs argument must be a compound when passing a single plug"
        )

    for child_index in range(len(inputs)):
        in_a = inputs[child_index]
        if in_a is None:
            continue
        out_plug.child(child_index).connect(outputs[child_index])

    return reverse_node


def create_controller_tag(
    node: DagNode,
    name: str,
    parent: DGNode | None = None,
    visibility_plug: Plug | None = None,
) -> DGNode:
    """
    Creates a new Maya kControllerTag node into this control.

    :param node: node to tag.
    :param name: name of the newly created controller tag.
    :param parent: optional controller tag control parent.
    :param visibility_plug: visibility plug to connect to.
    :return: newly created controller tag instance.
    """

    new_controller = create_dg_node(name, "controller")
    node.attribute("message").connect(new_controller.controllerObject)
    if visibility_plug is not None:
        visibility_plug.connect(new_controller.visibilityMode)
    if parent is not None:
        new_controller.attribute("parent").connect(
            parent.children.nextAvailableDestElementPlug()
        )

    return new_controller


def create_display_layer(name: str) -> DGNode:
    """
    Creates a new display layer with given name.

    :param name: name of the display layer.
    :return: newly created display layer instance.
    """

    return node_by_name(cmds.createDisplayLayer(name=name, empty=True))


def create_ik_handle(
    name: str,
    start_joint: Joint,
    end_joint: Joint,
    solver_type=constants.kIkRPSolveType,
    parent: DagNode | None = None,
    **kwargs,
) -> tuple[IkHandle, DagNode]:
    """
    Creates an IK handle and returns both, the IK handle and the IK effector.

    :param name: name of the ik handle.
    :param start_joint: start joint.
    :param end_joint: end joint for the effector.
    :param solver_type: solver type ('ikRPSolver' or 'ikSCsolver' or 'ikSplineSolver').
    :param parent: optional node to be the parent of the handle.
    :keyword str curve: full path to the curve.
    :keyword int priority: 1
    :keyword float weight: 1.0
    :keyword float positionWeight: 1.0
    :keyword bool forceSolver:
    :keyword bool snapHandleFlagToggle:
    :keyword bool sticky: False
    :keyword bool createCurve: True
    :keyword bool simplifyCurve: True
    :keyword bool rootOnCurve: True
    :keyword str twistType: "linear"
    :keyword bool createRootAxis: False
    :keyword bool parentCurve: True
    :keyword bool snapCurve: False
    :keyword int numSpans: 1
    :keyword bool rootTwistMode: False
    :return: tuple with the created IK handle and IK effector.
    """

    with contexts.namespace_context(OpenMaya.MNamespace.rootNamespace()):
        ik_nodes = cmds.ikHandle(
            sj=start_joint.fullPathName(),
            ee=end_joint.fullPathName(),
            solver=solver_type,
            n=name,
            **kwargs,
        )
        handle, effector = map(node_by_name, ik_nodes)
        if parent:
            handle.setParent(parent)

    return handle, effector


def create_nurbs_curve_from_points(
    name: str,
    points: list[list[float] | OpenMaya.MVector],
    shape_data: dict | None = None,
    parent: DagNode | None = None,
) -> tuple[DagNode, list[DGNode]]:
    """
    Creates a NURBS curve based on given world space points.

    :param name: name of the curve node.
    :param points: list of points for the curve in world space.
    :param shape_data: optional curve shape data.
    :param parent: optional parent for the curve transform node.
    :return: tuple containing the curve transform node and all its shapes.
    """

    spline_curve_transform, created_shapes = curves.create_curve_from_points(
        name=name,
        points=points,
        shape_dict=shape_data,
        parent=parent.object() if parent is not None else None,
    )

    return (
        node_by_name(spline_curve_transform),
        [node_by_name(i) for i in created_shapes if i != spline_curve_transform],
    )


@decorators.restore_selection
def create_poly_plane(name, **kwargs) -> list[DagNode]:
    """
    Creates a single polygon plane.

    :param name: name for the polygon plane.
    :param kwargs: extra keyword arguments (similar to the ones accepted by cmds.polyPlane command).
    :return: newly created poly plane node instance.
    """

    poly_plane = cmds.polyPlane(name=name, **kwargs)
    return list(map(node_by_name, poly_plane))


@decorators.restore_selection
def create_poly_cube(name, **kwargs) -> list[DagNode]:
    """
    Creates a single polygon cube.

    :param name: name for the polygon cube.
    :param kwargs: extra keyword arguments (similar to the ones accepted by cmds.polyCube command).
    :return: newly created poly cube node instance.
    """

    poly_plane = cmds.polyCube(name=name, **kwargs)
    return list(map(node_by_name, poly_plane))


@decorators.restore_selection
def create_poly_sphere(name, **kwargs) -> list[DagNode]:
    """
    Creates a single polygon sphere.

    :param name: name for the polygon sphere.
    :param kwargs: extra keyword arguments (similar to the ones accepted by cmds.polySphere command).
    :return: newly created poly sphere node instance.
    """

    poly_plane = cmds.polySphere(name=name, **kwargs)
    return list(map(node_by_name, poly_plane))


def create_condition_vector(
    first_term: Plug | float,
    second_term: Plug | float,
    color_if_true: Iterable[float | Plug] | Plug | OpenMaya.MVector,
    color_if_false: Iterable[float | Plug] | Plug | OpenMaya.MVector,
    operation: int | Plug,
    name: str,
) -> DGNode:
    """
    Creates a condition node that compares two vectors and returns a color based on the result.

    :param first_term: first term to compare.
    :param second_term: second term to compare.
    :param color_if_true: color to return if the condition is true.
    :param color_if_false: color to return if the condition is false.
    :param operation: operation to apply.
    :param name: name of the condition node.
    :return: created condition node.
    """

    condition_node = create_dg_node(name, "condition")
    if isinstance(operation, Plug):
        operation.connect(condition_node.operation)
    else:
        condition_node.operation.set(operation)
    if isinstance(first_term, float):
        condition_node.firstTerm.set(first_term)
    else:
        first_term.connect(condition_node.firstTerm)
    if isinstance(second_term, float):
        condition_node.secondTerm.set(second_term)
    else:
        second_term.connect(condition_node.secondTerm)
    if isinstance(color_if_true, Plug):
        color_if_true.connect(condition_node.colorIfTrue)
    elif isinstance(color_if_true, OpenMaya.MVector):
        condition_node.colorIfTrue.set(color_if_true)
    else:
        color = condition_node.colorIfTrue
        for i, plug in enumerate(color_if_true):
            if plug is None:
                continue
            child = color.child(i)
            if isinstance(plug, Plug):
                plug.connect(child)
                continue
            child.set(plug)
    if isinstance(color_if_false, Plug):
        color_if_false.connect(condition_node.colorIfFalse)
    elif isinstance(color_if_false, OpenMaya.MVector):
        condition_node.colorIfFalse.set(color_if_false)
    else:
        color = condition_node.colorIfFalse
        for i, plug in enumerate(color_if_false):
            if plug is None:
                continue
            child = color.child(i)
            if isinstance(plug, Plug):
                plug.connect(child)
                continue
            child.set(plug)

    return condition_node
