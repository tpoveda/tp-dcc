from __future__ import annotations

import os
import logging
from typing import Iterable, Iterator

from maya import cmds
from maya.api import OpenMaya, OpenMayaAnim

from . import mathlib, plugs, animation, curves, attributetypes, factory, scene
from ..cmds.helpers import is_safe_name
from ...python import helpers

logger = logging.getLogger(__name__)


def check_node(node: str | OpenMaya.MObject) -> bool:
    """Checks if a node is a valid node and raise and exception if the node is not valid.

    :param node: name of the node to be checked or MObject to be checked.
    :return: True if the given node is valid.
    """

    if isinstance(node, str):
        if not cmds.objExists(node):
            return False
    elif isinstance(node, OpenMaya.MObject):
        return not node.isNull()

    return True


def is_dag_node(mobj: OpenMaya.MObject) -> bool:
    """Checks if an MObject is a DAG node.

    :param mobj: Maya object to check.
    :return: True if the MObject is a DAG node or False otherwise.
    """

    return mobj.hasFn(OpenMaya.MFn.kDagNode)


def is_shape(mobj: OpenMaya.MObject) -> bool:
    """Returns whether the given node is a valid shape node.

    :param mobj: object to check as a shape node.
    :return: True if the given node is a valid shape node; False otherwise.
    """

    return False if not mobj.hasFn(OpenMaya.MFn.kShape) else True


def is_valid_mobject(mobj: OpenMaya.MObject) -> bool:
    """Returns whether given node is a valid MObject.

    :param mobj: Maya object to check.
    :return: True if given Maya object is valid; False otherwise.
    """

    handle = OpenMaya.MObjectHandle(mobj)
    return handle.isValid() and handle.isAlive()


def mobject_by_name(node_name: str) -> OpenMaya.MObject | None:
    """Returns an MObject from the given node name.

    :param node_name: name of the node to get.
    :return: Maya object instance from give name.
    """

    selection_list = OpenMaya.MSelectionList()
    try:
        selection_list.add(node_name)
    except RuntimeError:
        logger.warning(
            f'Node "{node_name}" does not exist or multiple nodes with same name within scene'
        )
        return None
    try:
        return selection_list.getDagPath(0).node()
    except TypeError:
        return selection_list.getDependNode(0)
    except Exception as exc:
        logger.warning(f"Impossible to get MObject from name {node_name} : {exc}")
        return None


def mobject_by_uuid(
    uuid: OpenMaya.MUuid,
) -> OpenMaya.MObject | list[OpenMaya.MObject] | None:
    """Returns an MObject from the given UUID.
    If multiples nodes are found with the same UUID, a list will be returned.

    :param uuid: UUID to get object for.
    :return: Maya object instance from given uuid.
    """

    nodes = list(iterate_nodes_by_uuid(uuid))
    if not nodes:
        return None

    if len(nodes) == 1:
        return nodes[0]

    return nodes


def mobject_by_handle(handle: OpenMaya.MObjectHandle) -> OpenMaya.MObject:
    """Returns an MObject from given MObjectHandle.

    :param handle: Maya object handle.
    :return: Maya object instance from given handle.
    """

    return handle.object()


def mobject_by_dag_path(dag_path: OpenMaya.MDagPath) -> OpenMaya.MObject:
    """Returns an MObject from given MDagPath.

    :param dag_path: DAG path instance.
    :return: Maya object instance from given dag path.
    """

    return dag_path.node()


__get_mobject__ = {
    "str": mobject_by_name,
    "MUuid": mobject_by_uuid,
    "MObjectHandle": mobject_by_handle,
    "MDagPath": mobject_by_dag_path,
}


def mobject(
    value: str | OpenMaya.MObject | OpenMaya.MObjectHandle | OpenMaya.MDagPath,
    validate_node: bool = False,
) -> OpenMaya.MObject | None:
    """Returns an MObject for the input scene object.

    :param value: Maya node to get MObject for.
    :param validate_node: whether validate node.
    :return: Maya object instance from given name.
    :raises TypeError: if given node is not a valid Maya node.
    """

    if validate_node:
        check_node(value)

    if isinstance(value, OpenMaya.MObject):
        return value

    type_name = type(value).__name__
    func = __get_mobject__.get(type_name, None)
    if func is not None:
        return func(value)

    raise TypeError(
        f"mobject() expects {tuple(__get_mobject__.keys())} ({type(value).__name__} given)"
    )


def name(
    mobj: OpenMaya.MObject, partial_name: bool = False, include_namespace: bool = True
) -> str:
    """Returns full or partial name for a given MObject (which must be valid).

    :param mobj: Maya object we want to retrieve name of
    :param partial_name: whether to return full path or partial name of the Maya object
    :param include_namespace: whether object namespace should be included in the path or stripped
    :return: name of the Maya object.
    """

    if mobj.hasFn(OpenMaya.MFn.kDagNode):
        dag_node = OpenMaya.MFnDagNode(mobj)
        node_name = (
            dag_node.partialPathName() if partial_name else dag_node.fullPathName()
        )
    else:
        node_name = OpenMaya.MFnDependencyNode(mobj).name()

    if not include_namespace:
        node_name = OpenMaya.MNamespace.stripNamespaceFromName(node_name)

    return node_name


def names_from_mobjs(mobjs: list[OpenMaya.MObject]) -> list[str]:
    """Returns names of the given list of Maya object handles.

    :param mobjs: list of Maya objects to retrieve names of.
    :return: list of names.
    """

    names_list: list[str] = []
    for mobj in mobjs:
        object_handle = OpenMaya.MObjectHandle(mobj)
        if not object_handle.isValid() or not object_handle.isAlive():
            continue
        names_list.append(name(object_handle.object()))

    return names_list


def set_names(nodes: list[OpenMaya.MObject], names: list[str]):
    """Renames given list of nodes with the given list of names.

    :param nodes: list of Maya objects to rename.
    :param names: list of new names.
    """

    nodes = helpers.force_list(nodes)
    names = helpers.force_list(names)

    # This function is not undoable.
    for node, node_name in zip(nodes, names):
        OpenMaya.MFnDagNode(node).setName(node_name)


def rename(
    mobj: OpenMaya.MObject,
    new_name: str,
    mod: OpenMaya.MDagModifier | None = None,
    apply: bool = True,
) -> OpenMaya.MDagModifier:
    """Renames given MObject dependency node with the new given name.

    :param mobj: Maya object to rename.
    :param new_name: new Maya object name.
    :param mod: optional Maya modifier to rename Maya object with.
    :param apply: whether to apply changes instantly.
    :return: renamed Maya object.
    """

    if not is_safe_name(new_name):
        raise NameError(f'"{new_name}" is not a valid name')

    dag_mod = mod or OpenMaya.MDagModifier()
    dag_mod.renameNode(mobj, new_name)
    if mod is None and apply:
        dag_mod.doIt()

    return dag_mod


# noinspection SpellCheckingInspection
def mdag_path(mobj: OpenMaya.MObject) -> OpenMaya.MDagPath:
    """Takes an object name as a string and returns its MDAGPath.

    :param mobj: Maya object instance to get DAG path of.
    :return: DAG Path.
    """

    check_node(mobj)

    selection_list = OpenMaya.MGlobal.getSelectionListByName(mobj)
    return selection_list.getDagPath(0)


def depend_node(mobj: OpenMaya.MObject) -> OpenMaya.MFnDependencyNode:
    """Returns the dependency node instance of the given node.

    :param mobj: Maya object instance to get depend node instance of.
    :return: dependency node instance.
    """

    check_node(mobj)

    return OpenMaya.MFnDependencyNode(mobj)


def plug(mobj: OpenMaya.MObject, plug_name: str) -> OpenMaya.MPlug:
    """Returns the plug of given Maya object with given name.

    :param mobj: Maya object to get plug of.
    :param plug_name: name of the plug to get.
    """

    check_node(mobj)

    dep_node = depend_node(mobj)
    attr = dep_node.attribute(plug_name)
    return OpenMaya.MPlug(mobj, attr)


def shape(node: OpenMaya.MObject) -> OpenMaya.MObject:
    """Returns the shape node of given node.

    :param node: Maya object to get shape of.
    :return: Maya shape object.
    """

    node = node[0] if isinstance(node, (list, tuple)) else node

    check_node(node)

    if not node.apiType() == OpenMaya.MFn.kTransform:
        return node

    path = OpenMaya.MDagPath.getAPathTo(node)
    num_shapes = path.numberOfShapesDirectlyBelow()
    if num_shapes:
        path.extendToShape(0)
        return path.node()

    return node


def iterate_shapes(
    mobj: OpenMaya.MObject | OpenMaya.MDagPath, filter_types: list[str] | None = None
) -> Iterator[OpenMaya.MDagPath]:
    """Generator function that returns all the given shape DAG paths directly below the given DAG path.

    :param mobj: Maya object or dag path to search shapes of.
    :param filter_types: list of filter shapes for teh shapes to return.
    :return: list of iterate shape DAG paths.
    """

    dag_path = OpenMaya.MDagPath(mobj) if isinstance(mobj, OpenMaya.MObject) else mobj
    filter_types = helpers.force_list(filter_types)
    for i in range(dag_path.numberOfShapesDirectlyBelow()):
        shape_dag_path = OpenMaya.MDagPath(dag_path)
        shape_dag_path.extendToShape(i)
        if not filter_types or shape_dag_path.apiType() in filter_types:
            yield shape_dag_path


def shapes(
    mobj: OpenMaya.MObject | OpenMaya.MDagPath,
    filter_types: list[str | int] | None = None,
) -> list[OpenMaya.MDagPath]:
    """Returns all the given shape DAG paths directly below the given DAG path as a list.

    :param mobj: Maya object to search shapes of
    :param filter_types: list of filter shapes for teh shapes to return
    :return: list of iterated shapes.
    """

    return list(iterate_shapes(mobj, filter_types=filter_types))


def shape_at_index(dag_path: OpenMaya.MDagPath, index: int) -> OpenMaya.MDagPath | None:
    """Finds and returns the shape Dag Path under the given path for the given index.

    :param dag_path: dag path to get shape index of.
    :param index: shape index.
    :return: found shape DAG path.
    """

    if index in range(dag_path.numberOfShapesDirectlyBelow()):
        return OpenMaya.MDagPath(dag_path).extendToShape(index)

    return None


def iterate_nodes_by_uuid(
    *uuids: str | OpenMaya.MUuid | Iterable[str | OpenMaya.MUuid],
) -> Iterator[OpenMaya.MObject]:
    """Generator function that yields dependency nodes with the given UUID.

    :param uuids: node uuids to iterate nodes from.
    :return: list of nodes.
    """

    for uuid in uuids:
        uuid = OpenMaya.MUuid(uuid) if isinstance(uuid, str) else uuid
        selection = OpenMaya.MSelectionList()
        selection.add(uuid)
        for i in range(selection.length()):
            yield selection.getDependNode(i)


def node_color_data(mobj: OpenMaya.MObject) -> dict:
    """Returns the color data in the given Maya node.

    :param mobj: Maya object to get color data of.
    :return: dictionary containing node color data.
    """

    dag_node = OpenMaya.MFnDagNode(OpenMaya.MFnDagNode(mobj).getPath())
    node_plug = dag_node.findPlug("overrideColorRGB", False)
    enabled_plug = dag_node.findPlug("overrideEnabled", False)
    override_rgb_colors = dag_node.findPlug("overrideRGBColors", False)
    use_outliner = dag_node.findPlug("useOutlinerColor", False)

    return {
        "overrideEnabled": enabled_plug.asBool(),
        "overrideColorRGB": OpenMaya.MColor(plugs.plug_value(node_plug)),
        "overrideRGBColors": override_rgb_colors.asBool(),
        "useOutlinerColor": use_outliner.asBool(),
        "outlinerColor": OpenMaya.MColor(
            plugs.plug_value(dag_node.findPlug("outlinerColor", False))
        ),
    }


def set_outliner_color(
    mobj: OpenMaya.MObject,
    color: OpenMaya.MColor | Iterable[float, float, float],
    mod: OpenMaya.MDGModifier | None = None,
):
    """Sets the outliner color of the given Maya object.

    :param mobj: Maya object to set outliner color of.
    :param color: RGB color to set to outliner item.
    :param mod: optional Maya context to use.
    """

    modifier = mod or OpenMaya.MDGModifier()
    dag_node = OpenMaya.MFnDagNode(OpenMaya.MFnDagNode(mobj).getPath())

    outliner_color = helpers.force_list(color)
    if len(outliner_color) > 3:
        outliner_color = outliner_color[:-1]
    use_outliner = dag_node.findPlug("useOutlinerColor", False)
    modifier.newPlugValueBool(use_outliner, True)
    outliner_color_plug = dag_node.findPlug("outlinerColor", False)
    fn_data = OpenMaya.MFnNumericData(outliner_color_plug.asMObject()).setData(
        outliner_color
    )
    modifier.newPlugValue(outliner_color_plug, fn_data.object())

    if mod is None:
        modifier.doIt()


def set_node_color(
    mobj: OpenMaya.MObject,
    color: OpenMaya.MColor | Iterable[float, float, float] | None = None,
    outliner_color: OpenMaya.MColor | Iterable[float, float, float] | None = None,
    use_outliner_color: bool = False,
    mod: OpenMaya.MDGModifier | None = None,
) -> OpenMaya.MDGModifier:
    """Sets the given Maya object its override color. MObject can represent an object or a shape.

    :param mobj: Maya object we want to change color of.
    :param color: RGB color to set.
    :param outliner_color: RGB color to set to outliner item.
    :param use_outliner_color: bool, whether to apply outliner color.
    :param mod: optional Maya context to use.
    """

    color = helpers.force_list(color)
    if color and len(color) > 3:
        color = color[:-1]

    modifier = mod or OpenMaya.MDGModifier()
    dag_node = OpenMaya.MFnDagNode(OpenMaya.MFnDagNode(mobj).getPath())
    found_plug = dag_node.findPlug("overrideColorRGB", False)
    enabled_plug = dag_node.findPlug("overrideEnabled", False)
    override_rgb_colors = dag_node.findPlug("overrideRGBColors", False)
    if not enabled_plug.asBool():
        enabled_plug.setBool(True)
    if not override_rgb_colors.asBool():
        dag_node.findPlug("overrideRGBColors", False).setBool(True)

    fn_data = OpenMaya.MFnNumericData(found_plug.asMObject()).setData(color)
    modifier.newPlugValue(found_plug, fn_data.object())

    if outliner_color and use_outliner_color:
        set_outliner_color(mobj, outliner_color, mod=modifier)

    if mod is None:
        modifier.doIt()

    return modifier


def translation(
    mobj: OpenMaya.MObject,
    space: OpenMaya.MSpace | None = None,
    scene_units: bool = False,
) -> OpenMaya.MVector:
    """Returns the translation for the given Maya object.

    :param mobj: Maya object to get translation of.
    :param space: coordinate system to use.
    :param scene_units: whether the translation vector needs to be converted to scene units.
    :return: object translation.
    """

    space = space or OpenMaya.MSpace.kTransform
    transform = OpenMaya.MFnTransform(OpenMaya.MFnDagNode(mobj).getPath())
    node_translation = transform.translation(space)

    return (
        mathlib.convert_to_scene_units(node_translation)
        if scene_units
        else node_translation
    )


def set_translation(
    mobj: OpenMaya.MObject,
    position: OpenMaya.MVector,
    space: OpenMaya.MSpace | None = None,
    scene_units: bool = False,
):
    """Sets the translation for the given Maya object.

    :param mobj: Maya object to set translation of.
    :param position: translation to set.
    :param space: coordinate system to use.
    :param scene_units: whether the translation vector needs to be converted to scene units.
    """

    space = space or OpenMaya.MSpace.kTransform
    transform = OpenMaya.MFnTransform(OpenMaya.MFnDagNode(mobj).getPath())
    position = mathlib.convert_from_scene_units(position) if scene_units else position
    transform.setTranslation(position, space)


def rotation(
    mobj: OpenMaya.MObject | OpenMaya.MDagPath,
    space: OpenMaya.MSpace | None = None,
    as_quaternion: bool = False,
) -> OpenMaya.MEulerRotation | OpenMaya.MQuaternion:
    """Returns the rotation for the given Maya object.

    :param mobj: Maya object to get rotation of.
    :param space: coordinate system to use.
    :param as_quaternion: whether to return rotation as a quaternion.
    :return: Maya object rotation.
    """

    space = space or OpenMaya.MSpace.kTransform
    transform = OpenMaya.MFnTransform(mobj)

    return transform.rotation(space=space, asQuaternion=as_quaternion)


def set_rotation(
    mobj: OpenMaya.MObject,
    new_rotation: OpenMaya.MEulerRotation | OpenMaya.MQuaternion,
    space: OpenMaya.MSpace | None = None,
):
    """Sets the rotation for the given Maya object.

    :param mobj: Maya object to set rotation of.
    :param new_rotation: rotation to set.
    :param space: coordinate system to use.
    """

    transform = OpenMaya.MFnTransform(OpenMaya.MFnDagNode(mobj).getPath())
    if isinstance(new_rotation, (list, tuple)):
        new_rotation = OpenMaya.MEulerRotation(
            [
                OpenMaya.MAngle(i, OpenMaya.MAngle.kDegrees).asRadians()
                for i in new_rotation
            ]
        )
    transform.setRotation(new_rotation, space)


def matrix(
    mobj: OpenMaya.MObject, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
) -> OpenMaya.MMatrix:
    """Returns local matrix of the given MObject pointing to DAG node.

    :param mobj: Maya object of the DAG node we want to retrieve world matrix of.
    :param ctx: MDGContext to use.
    :return: local matrix.
    """

    return OpenMaya.MFnMatrixData(
        OpenMaya.MFnDependencyNode(mobj).findPlug("matrix", False).asMObject(ctx)
    ).matrix()


def set_matrix(
    mobj: OpenMaya.MObject,
    new_matrix: OpenMaya.MMatrix,
    space: OpenMaya.MSpace = OpenMaya.MSpace.kTransform,
):
    """Sets the object matrix using MTransform.

    :param mobj: Maya object to modify.
    :param new_matrix: Matrix to set.
    :param space: coordinate space to set the matrix by.
    """

    dag = OpenMaya.MFnDagNode(mobj)
    transform = OpenMaya.MFnTransform(dag.getPath())
    transform_matrix = OpenMaya.MTransformationMatrix(new_matrix)
    transform.setTranslation(transform_matrix.translation(space), space)
    transform.setRotation(transform_matrix.rotation(asQuaternion=True), space)
    transform.setScale(transform_matrix.scale(space))


def world_matrix_plug(mobj: OpenMaya.MObject) -> OpenMaya.MPlug:
    """Returns the MPlug pointing worldMatrix of the given MObject pointing a DAG node.

    :param mobj: Maya object of the DAG node we want to retrieve world matrix plug of.
    :return: world matrix plug instance.
    """

    found_world_matrix = OpenMaya.MFnDependencyNode(mobj).findPlug("worldMatrix", False)
    return found_world_matrix.elementByLogicalIndex(0)


def world_matrix(
    mobj: OpenMaya.MObject, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
) -> OpenMaya.MMatrix:
    """Returns world matrix of the given MObject pointing to DAG node.

    :param mobj: Maya object of the DAG node we want to retrieve world matrix of.
    :param ctx: MDGContext to use.
    :return: world matrix.
    """

    return OpenMaya.MFnMatrixData(world_matrix_plug(mobj).asMObject(ctx)).matrix()


def world_inverse_matrix(
    mobj: OpenMaya.MObject, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
) -> OpenMaya.MMatrix:
    """Returns world inverse matrix of the given Maya object.

    :param mobj: Maya object of the DAG node we want to retrieve world inverse matrix of.
    :param ctx: MDGContext to use.
    :return: world inverse matrix.
    """

    inverse_matrix_plug = OpenMaya.MFnDependencyNode(mobj).findPlug(
        "worldInverseMatrix", False
    )
    matrix_plug = inverse_matrix_plug.elementByLogicalIndex(0)

    return OpenMaya.MFnMatrixData(matrix_plug.asMObject(ctx)).matrix()


def parent_matrix(
    mobj: OpenMaya.MObject, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
) -> OpenMaya.MMatrix:
    """Returns the parent matrix of the given Maya object.

    :param mobj: Maya object of the DAG node we want to retrieve parent matrix of.
    :param ctx: MDGContext to use.
    :return: parent matrix.
    """

    parent_matrix_plug = OpenMaya.MFnDependencyNode(mobj).findPlug(
        "parentMatrix", False
    )
    matrix_plug = parent_matrix_plug.elementByLogicalIndex(0)

    return OpenMaya.MFnMatrixData(matrix_plug.asMObject(ctx)).matrix()


def parent_inverse_matrix_plug(mobj: OpenMaya.MObject) -> OpenMaya.MPlug:
    """Returns parent inverse matrix MPlug of the given Maya object.

    :param mobj: Maya object of the DAG node we want to retrieve parent inverse matrix plug of.
    :return: parent inverse matrix plug instance.
    """

    found_parent_inverse_matrix_plug = OpenMaya.MFnDependencyNode(mobj).findPlug(
        "parentInverseMatrix", False
    )
    return found_parent_inverse_matrix_plug.elementByLogicalIndex(0)


def parent_inverse_matrix(
    mobj: OpenMaya.MObject, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
) -> OpenMaya.MMatrix:
    """Returns the parent inverse matrix of the given Maya object.

    :param mobj: Maya object of the DAG node we want to retrieve parent inverse matrix of.
    :param ctx: MDGContext to use.
    :return: parent inverse matrix.
    """

    return OpenMaya.MFnMatrixData(
        parent_inverse_matrix_plug(mobj).asMObject(ctx)
    ).matrix()


def offset_matrix(
    start_mobj: OpenMaya.MObject,
    end_mobj: OpenMaya.MObject,
    space: OpenMaya.MSpace | None = None,
    ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal,
) -> OpenMaya.MMatrix:
    """Returns the offset matrix between the given two objects.

    :param start_mobj: start transform Maya object.
    :param end_mobj: end transform Maya object.
    :param space: coordinate space to use.
    :param ctx: context to use.
    :return: resulting offset matrix.
    """

    space = space or OpenMaya.MSpace.kWorld
    if space == OpenMaya.MSpace.kWorld:
        start = world_matrix(start_mobj, ctx=ctx)
        end = world_matrix(end_mobj, ctx=ctx)
    else:
        start = matrix(start_mobj, ctx=ctx)
        end = matrix(end_mobj, ctx=ctx)

    if int(OpenMaya.MGlobal.mayaVersion()) < 2020:
        output_matrix = end * start.inverse()
    else:
        output_matrix = (
            end
            * start.inverse()
            * plugs.plug_value(
                OpenMaya.MFnDependencyNode(start_mobj).findPlug(
                    "offsetParentMatrix", False
                ),
                ctx,
            ).inverse()
        )

    return output_matrix


def decompose_transform_matrix(
    target_matrix: OpenMaya.MMatrix,
    rotation_order: int,
    space: OpenMaya.MSpace | None = None,
) -> tuple[OpenMaya.MVector, OpenMaya.MVector, OpenMaya.MVector]:
    """Returns decomposed translation, rotation and scale of the given Maya matrix.

    :param target_matrix: maya transform matrix to decompose.
    :param rotation_order: rotation order getting transform matrix of.
    :param space: coordinate space to decompose matrix of.
    :return: decompose matrix in translation, rotation and scale.
    """

    space = space or OpenMaya.MSpace.kWorld

    transform_matrix = OpenMaya.MTransformationMatrix(target_matrix)
    transform_matrix.reorderRotation(rotation_order)
    transform_rotation = transform_matrix.rotation(
        asQuaternion=space == OpenMaya.MSpace.kWorld
    )

    return (
        transform_matrix.translation(space),
        transform_rotation,
        transform_matrix.scale(space),
    )


# noinspection PyShadowingNames
def has_attribute(mobj: OpenMaya.MObject, attribute_name: str) -> bool:
    """Returns whether given Maya object has given attribute added to it.

    :param mobj: Maya object to check search attribute in.
    :param attribute_name: name of the attribute to check.
    :return: True if the Maya object has given attribute; False otherwise.
    """

    try:
        return plugs.as_mplug(".".join((name(mobj), attribute_name))) is not None
    except RuntimeError:
        return False


# noinspection PyIncorrectDocstring,PyPep8Naming,PyShadowingBuiltins,SpellCheckingInspection
def add_attribute(
    mobj: OpenMaya.MObject,
    long_name: str,
    short_name: str,
    type: int = attributetypes.kMFnNumericDouble,
    isArray: bool = False,
    apply: bool = True,
    mod: OpenMaya.MDGModifier | None = None,
    **kwargs,
) -> OpenMaya.MFnAttribute:
    """Adds a new attribute to the given Maya object.

    :param mobj: node to add attribute to.
    :param long_name: attribute long name.
    :param short_name: attribute short name.
    :param type: Maya attribute type.
    :param apply: whether to apply changes instantly.
    :param mod: Maya modifier to add attribute with.
    :keyword bool channelBox: whether keys can be set on the attribute.
    :keyword bool keyable: whether the attribute is keyable.
    :keyword Any default: default value for the attribute.
    :keyword Any value: value for the attribute to use.
    :keyword list[str] enums: list of enums for the attribute.
    :keyword bool storable: whether attribute value should be stored when file is saved.
    :keyword bool writable: whether attribute can be changed.
    :keyword bool connectable: whether attribute can be connected to other attributes.
    :keyword bool locked: whether attribute is locked by default.
    :keyword int or float min: hard minimum value for the attribute.
    :keyword int or float max: hard maximum value for the attribute.
    :keyword int or float softMin: soft minimum value for the attribute.
    :keyword int or float softMax: soft maximum value for the attribute.
    :keyword str niceName: optional nice name for the attribute.
    :return: Maya object linked to the attribute.
    :raises AttributeAlreadyExists: if the attribute already exists.
    :raises TypeError: if the attribute type is not supported.

    .. code-block:: python

            # message attribute
            attr_mobj = addAttribute(myNode, "testMsg", "testMsg", attrType=attributetypes.kMFnMessageAttribute,
                                                             isArray=False, apply=True)
            # double angle
            attr_mobj = addAttribute(myNode, "myAngle", "myAngle", attrType=attributetypes.kMFnUnitAttributeAngle,
                                                             keyable=True, channelBox=False)
            # enum
            attr_mobj = addAttribute(myNode, "myEnum", "myEnum", attrType=attributetypes.kMFnkEnumAttribute,
                                                        keyable=True, channelBox=True, enums=["one", "two", "three"])
    """

    if has_attribute(mobj, long_name):
        raise AttributeAlreadyExistsError(
            f'Node "{name(mobj)}" already has attribute "{long_name}"'
        )

    default = kwargs.get("default")
    channel_box = kwargs.get("channelBox")
    keyable = kwargs.get("keyable")
    short_name = short_name or long_name
    numeric_class, data_constant = attributetypes.numeric_type_to_maya_fn_type(type)

    if numeric_class is not None:
        attr = numeric_class()
        if type == attributetypes.kMFnNumericAddr:
            aobj = attr.createAddr(long_name, short_name)
        elif type == attributetypes.kMFnNumeric3Float:
            aobj = attr.createPoint(long_name, short_name)
        else:
            aobj = attr.create(long_name, short_name, data_constant)
    elif type == attributetypes.kMFnkEnumAttribute:
        attr = OpenMaya.MFnEnumAttribute()
        aobj = attr.create(long_name, short_name)
        fields = kwargs.get("enums", list())
        # maya creates an invalid enumAttribute if when creating we don't create any fields
        # so this just safeguards to a single value
        if not fields:
            fields = ["None"]
        for index in range(len(fields)):
            attr.addField(fields[index], index)
    elif type == attributetypes.kMFnCompoundAttribute:
        attr = OpenMaya.MFnCompoundAttribute()
        aobj = attr.create(long_name, short_name)
    elif type == attributetypes.kMFnMessageAttribute:
        attr = OpenMaya.MFnMessageAttribute()
        aobj = attr.create(long_name, short_name)
    elif type == attributetypes.kMFnDataString:
        attr = OpenMaya.MFnTypedAttribute()
        string_data = OpenMaya.MFnStringData().create("")
        aobj = attr.create(long_name, short_name, OpenMaya.MFnData.kString, string_data)
    elif type == attributetypes.kMFnUnitAttributeDistance:
        attr = OpenMaya.MFnUnitAttribute()
        aobj = attr.create(long_name, short_name, OpenMaya.MDistance())
    elif type == attributetypes.kMFnUnitAttributeAngle:
        attr = OpenMaya.MFnUnitAttribute()
        aobj = attr.create(long_name, short_name, OpenMaya.MAngle())
    elif type == attributetypes.kMFnUnitAttributeTime:
        attr = OpenMaya.MFnUnitAttribute()
        aobj = attr.create(long_name, short_name, OpenMaya.MTime())
    elif type == attributetypes.kMFnDataMatrix:
        attr = OpenMaya.MFnMatrixAttribute()
        aobj = attr.create(long_name, short_name)
    # elif type == attributetypes.kMFnDataFloatArray:
    #     attr = OpenMaya.MFnFloatArray()
    #     aobj = attr.create(long_name, short_name)
    elif type == attributetypes.kMFnDataDoubleArray:
        data = OpenMaya.MFnDoubleArrayData().create(OpenMaya.MDoubleArray())
        attr = OpenMaya.MFnTypedAttribute()
        aobj = attr.create(long_name, short_name, OpenMaya.MFnData.kDoubleArray, data)
    elif type == attributetypes.kMFnDataIntArray:
        data = OpenMaya.MFnIntArrayData().create(OpenMaya.MIntArray())
        attr = OpenMaya.MFnTypedAttribute()
        aobj = attr.create(long_name, short_name, OpenMaya.MFnData.kIntArray, data)
    elif type == attributetypes.kMFnDataPointArray:
        data = OpenMaya.MFnPointArrayData().create(OpenMaya.MPointArray())
        attr = OpenMaya.MFnTypedAttribute()
        aobj = attr.create(long_name, short_name, OpenMaya.MFnData.kPointArray, data)
    elif type == attributetypes.kMFnDataVectorArray:
        data = OpenMaya.MFnVectorArrayData().create(OpenMaya.MVectorArray())
        attr = OpenMaya.MFnTypedAttribute()
        aobj = attr.create(long_name, short_name, OpenMaya.MFnData.kVectorArray, data)
    elif type == attributetypes.kMFnDataStringArray:
        data = OpenMaya.MFnStringArrayData().create()
        attr = OpenMaya.MFnTypedAttribute()
        aobj = attr.create(long_name, short_name, OpenMaya.MFnData.kStringArray, data)
    elif type == attributetypes.kMFnDataMatrixArray:
        data = OpenMaya.MFnMatrixArrayData().create(OpenMaya.MMatrixArray())
        attr = OpenMaya.MFnTypedAttribute()
        aobj = attr.create(long_name, short_name, OpenMaya.MFnData.kMatrixArray, data)
    else:
        raise TypeError(
            "Unsupported Attribute Type: {}, name: {}".format(type, long_name)
        )

    attr.array = isArray
    storable = kwargs.get("storable", True)
    writable = kwargs.get("writable", True)
    connectable = kwargs.get("connectable", True)
    min_value = kwargs.get("min")
    max_value = kwargs.get("max")
    soft_min = kwargs.get("softMin")
    soft_max = kwargs.get("softMax")
    value = kwargs.get("value")
    locked = kwargs.get("locked", False)
    nice_name = kwargs.get("niceName", None)

    attr.storable = storable
    attr.writable = writable
    attr.connectable = connectable
    if nice_name:
        attr.setNiceNameOverride(nice_name)

    if channel_box is not None:
        attr.channelBox = channel_box
    if keyable is not None:
        attr.keyable = keyable
    if default is not None:
        if type == attributetypes.kMFnDataString:
            default = OpenMaya.MFnStringData().create(default)
        elif type == attributetypes.kMFnDataMatrix:
            default = OpenMaya.MMatrix(default)
        elif type == attributetypes.kMFnUnitAttributeAngle:
            default = OpenMaya.MAngle(default, OpenMaya.MAngle.kRadians)
        elif type == attributetypes.kMFnUnitAttributeDistance:
            default = OpenMaya.MDistance(default)
        elif type == attributetypes.kMFnUnitAttributeTime:
            default = OpenMaya.MTime(default)
        plugs.set_attribute_fn_default(aobj, default)
    if min_value is not None:
        plugs.set_attr_min(aobj, min_value)
    if max_value is not None:
        plugs.set_attr_max(aobj, max_value)
    if soft_min is not None:
        plugs.set_attr_soft_min(aobj, soft_min)
    if soft_max is not None:
        plugs.set_attr_soft_max(aobj, soft_max)
    if aobj is not None and apply:
        modifier = mod or OpenMaya.MDGModifier()
        modifier.addAttribute(mobj, aobj)
        modifier.doIt()
        found_plug = OpenMaya.MPlug(mobj, aobj)
        kwargs["type"] = type
        if value is not None:
            plugs.set_plug_value(found_plug, value)
        found_plug.isLocked = locked

    return attr


# noinspection PyPep8Naming
def add_compound_attribute(
    mobj: OpenMaya.MObject,
    long_name: str,
    short_name: str,
    attr_map: list[dict],
    isArray: bool = False,
    apply: bool = True,
    mod: OpenMaya.MDGModifier | None = None,
    **kwargs,
) -> OpenMaya.MFnAttribute:
    """Adds a new compound attribute to the given Maya object.

    :param mobj: node to add compound attribute to.
    :param long_name: compound attribute long name.
    :param short_name: compound attribute short name.
    :param attr_map: list of child attributes to add.
            e.g. [{"name":str, "type": attributetypes.kType, "isArray": bool}]
    :param isArray: whether the compound attribute is an array.
    :param bool apply: whether to apply changes instantly.
    :param mod: Maya modifier to add attribute with.
    :return: MObject linked to the compound attribute.
    """

    exists = False
    modifier = mod or OpenMaya.MDGModifier()
    compound_mobj = OpenMaya.MObject.kNullObj
    short_name = short_name or long_name

    if has_attribute(mobj, long_name):
        exists = True
        compound_attribute = OpenMaya.MFnCompoundAttribute(
            plugs.as_mplug(".".join([name(mobj), long_name])).attribute()
        )
    else:
        compound_attribute = OpenMaya.MFnCompoundAttribute()
        compound_mobj = compound_attribute.create(long_name, short_name)
        compound_attribute.array = isArray

    for attr_data in attr_map:
        if not attr_data:
            continue
        if attr_data["type"] == attributetypes.kMFnCompoundAttribute:
            # when create child compounds maya only wants the root attribute to be created. All children will be
            # created because we execute the addChild()
            child = add_compound_attribute(
                mobj,
                attr_data["name"],
                attr_data["name"],
                attr_data.get("children", []),
                apply=False,
                mod=modifier,
                **attr_data,
            )
        else:
            try:
                child = add_attribute(
                    mobj,
                    short_name=attr_data["name"],
                    long_name=attr_data["name"],
                    mod=modifier,
                    apply=exists,
                    **attr_data,
                )
            except AttributeAlreadyExistsError:
                continue
            except RuntimeError:
                raise
        if child is not None:
            attr_obj = child.object()
            compound_attribute.addChild(attr_obj)

    if apply and not exists:
        modifier.addAttribute(mobj, compound_mobj)
        modifier.doIt()
        kwargs["children"] = attr_map
        plugs.set_plug_info_from_dict(OpenMaya.MPlug(mobj, compound_mobj), **kwargs)

    return compound_attribute


def add_proxy_attribute(
    mobj: OpenMaya.MObject, source_plug: OpenMaya.MPlug, **kwargs
) -> OpenMaya.MFnAttribute:
    """Adds a new proxy attribute into the given node.

    :param mobj: Maya object to add proxy attribute into.
    :param source_plug: source proxy plug.
    :return: created proxy attribute.
    """

    # numeric compound attributes e.g: double3 isn't supported via addCompound as it's an
    # actual maya type mfn.kAttributeDouble3 which means we don't create it via MFnCompoundAttribute.
    # therefore we manage that for via the kwargs dict.
    if kwargs["type"] == attributetypes.kMFnCompoundAttribute:
        attr1 = add_compound_attribute(mobj, attrMap=kwargs["children"], **kwargs)
        attr1.isProxyAttribute = True
        attr_plug = OpenMaya.MPlug(mobj, attr1.object())
        plugs.set_compound_as_proxy(attr_plug, source_plug)
    else:
        attr1 = add_attribute(mobj, **kwargs)
        proxy_plug = OpenMaya.MPlug(mobj, attr1.object())
        # is it's an attribute we're adding which is a special type like double3
        # then ignore connecting the compound as maya proxy attributes require the children
        # not the parent to be connected.
        if proxy_plug.isCompound:
            attr1.isProxyAttribute = True
            plugs.set_compound_as_proxy(proxy_plug, source_plug)
        else:
            attr1.isProxyAttribute = True
            plugs.connect_plugs(source_plug, proxy_plug)

    return attr1


def iterate_attributes(
    mobj: OpenMaya.MObject,
    skip: list[str] | None = None,
    include_attributes: list[str] | None = None,
) -> Iterator[OpenMaya.MPlug]:
    """Generator function to iterate over all plugs of a given Maya object.

    :param mobj: Maya object to iterate.
    :param skip: list of attributes to skip.
    :param include_attributes: list of attributes to force iteration over.
    :return: generator of iterated attributes.
    """

    skip = skip or ()
    dep = OpenMaya.MFnDependencyNode(mobj)
    for idx in range(dep.attributeCount()):
        attr = dep.attribute(idx)
        attr_plug = OpenMaya.MPlug(mobj, attr)
        plug_name = attr_plug.partialName(
            includeNodeName=False,
            includeNonMandatoryIndices=True,
            includeInstancedIndices=True,
            useAlias=False,
            useFullAttributePath=True,
            useLongNames=True,
        )
        if any(i in plug_name for i in skip):
            continue
        elif include_attributes and not any(i in plug_name for i in include_attributes):
            continue
        elif attr_plug.isElement or attr_plug.isChild:
            continue
        yield attr_plug
        for child in plugs.iterate_children(attr_plug):
            yield child


def iterate_extra_attributes(
    mobj: OpenMaya.MObject,
    skip: list[str] | None = None,
    filtered_types: list[str] | None = None,
    include_attributes: list[str] | None = None,
) -> Iterator[OpenMaya.MPlug]:
    """Generator function to iterate over all extra plugs of a given Maya object.

    :param mobj: Maya object to iterate.
    :param skip: list of attributes to skip.
    :param filtered_types: optional list of types we want to filter.
    :param include_attributes: list of attributes to force iteration over.
    :return: generator of iterated extra attributes.
    """

    skip = skip or ()
    filtered_types = filtered_types or ()
    include_attributes = include_attributes or ()
    dep = OpenMaya.MFnDependencyNode(mobj)
    for i in range(dep.attributeCount()):
        try:
            attr = dep.attribute(i)
        except RuntimeError:
            logger.error(
                f"Was not possible to retrieve attribute with index {i} from attribute {dep}"
            )
            continue
        plug_found = OpenMaya.MPlug(mobj, attr)
        if not plug_found.isDynamic:
            continue
        plug_name = plug_found.partialName(
            includeNodeName=False,
            includeNonMandatoryIndices=False,
            includeInstancedIndices=False,
            useAlias=False,
            useFullAttributePath=False,
            useLongNames=False,
        )
        if skip and plug_name.startswith(skip):
            continue
        elif include_attributes and not any(i in plug_name for i in include_attributes):
            continue
        elif not filtered_types or plugs.plug_type(plug_found) in filtered_types:
            yield plug_found


def iterate_connections(
    node: OpenMaya.MObject, source: bool = True, destination: bool = True
) -> Iterator[tuple[OpenMaya.MPlug, OpenMaya.MPlug]]:
    """Returns a generator function containing a tuple of Maya plugs.

    :param node: Maya node to search.
    :param source: if True, all upstream connections are returned.
    :param destination: if True, all downstream connections are returned.
    :return: tuple of MPlug instances, the first element is the connected MPlug of the given node and the other one is
        the connected MPlug from the other node.
    """

    dep = OpenMaya.MFnDependencyNode(node)
    for plug_found in iter(dep.getConnections()):
        if source and plug_found.isSource:
            for i in iter(plug_found.destinations()):
                yield plug_found, i
        if destination and plug_found.isDestination:
            yield plug_found, plug_found.source()


def set_lock_state_on_attributes(
    mobj: OpenMaya.MObject, attributes: Iterable[str], state: bool = True
) -> bool:
    """Locks and unlocks the given attributes.

    :param mobj: node whose attributes we want to lock/unlock.
    :param attributes: list of attributes names to lock/unlock.
    :param state: whether to lock or unlock the attributes.
    :return: True if the attributes lock/unlock operation was successful; False otherwise.
    """

    attributes = helpers.force_list(attributes)
    dep = OpenMaya.MFnDependencyNode(mobj)
    for attr in attributes:
        try:
            found_plug = dep.findPlug(attr, False)
        except RuntimeError:
            # Plug is missing.
            continue
        if found_plug.isLocked != state:
            found_plug.isLocked = state

    return True


def show_hide_attributes(
    mobj: OpenMaya.MObject, attributes: list[str], state: bool = False
) -> bool:
    """Shows or hides given attributes in the channel box.

    :param mobj: node whose attributes we want to show/hide.
    :param attributes: list of attributes names to lock/unlock
    :param state: whether to hide or show the attributes.
    :return: True if the attributes show/hide operation was successful; False otherwise.
    """

    attributes = helpers.force_list(attributes)
    dep = OpenMaya.MFnDependencyNode(mobj)
    for attr in attributes:
        found_plug = dep.findPlug(attr, False)
        if found_plug.isChannelBox != state:
            found_plug.isChannelBox = state

    return True


def serialize_node(
    node: OpenMaya.MObject,
    skip_attributes: Iterable[str] | None = None,
    include_connections: bool = True,
    include_attributes: Iterable[str] = None,
    extra_attributes_only: bool = False,
    use_short_names: bool = False,
    include_namespace: bool = True,
) -> dict:
    """Function that converts given OpenMaya.MObject into a serialized dictionary.
    This function iterates through all attributes, serializing any extra attribute found and any default value that
    has not changed (defaultValue) and not connected or is an array attribute will be skipped.

    Return value:
    {
        'name': '|root|auto|node',
        'parent': '|root|auto',
        'type': 'transform'
        'attributes':
        [
            {
                'type': 0,
                'channelBox': false,
                'default': false,
                'isArray': false,
                'isDynamic': true,
                'keyable': true,
                'locked': false,
                'max': null,
                'min': null,
                'name': 'test',
                'softMax': null,
                'softMin': null,
                'value': false
            },
        ],
        'connections':
        [
            {
              'destination': '|root|auto|config',
              'destinationPlug': 'run',
              'source': '|control1|control2',
              'sourcePlug': 'translateX'
            },
        ]
    }

    :param node: node to serialize.
    :param skip_attributes: list of attributes names to skip serialization of.
    :param include_connections: whether to find and serialize all connections where the destination is this node.
    :param include_attributes: list of attributes to serialize
    :param extra_attributes_only: whether to serialize only the extra attributes of this node.
    :param use_short_names: whether to use short names to serialize node data.
    :param include_namespace: whether to include the namespace as part of node.
    :return: dictionary containing node data.
    """

    data: dict = {}

    if node.hasFn(OpenMaya.MFn.kDagNode):
        dep = OpenMaya.MFnDagNode(node)
        node_name = (
            dep.fullPathName().split("|")[-1] if use_short_names else dep.fullPathName()
        )
        parent_dep = OpenMaya.MFnDagNode(dep.parent(0))
        parent_dep_name = (
            parent_dep.fullPathName().split("|")[-1]
            if use_short_names
            else parent_dep.fullPathName()
        )
        if not include_namespace:
            node_name = node_name.split("|")[-1].split(":")[-1]
            if parent_dep_name:
                parent_dep_name = parent_dep_name.split("|")[-1].split(":")[-1]
        else:
            node_name = node_name.replace(
                OpenMaya.MNamespace.getNamespaceFromName(node_name).split("|")[-1]
                + ":",
                "",
            )
            if parent_dep_name:
                parent_dep_name = parent_dep_name.replace(
                    OpenMaya.MNamespace.getNamespaceFromName(parent_dep_name).split(
                        "|"
                    )[-1]
                    + ":",
                    "",
                )
        data["parent"] = parent_dep_name
    else:
        dep = OpenMaya.MFnDependencyNode(node)
        node_name = dep.name()
        if not include_namespace:
            node_name = node_name.split("|")[-1].split(":")[-1]
        else:
            node_name = node_name.replace(
                OpenMaya.MNamespace.getNamespaceFromName(node_name).split("|")[-1]
                + ":",
                "",
            )

    data["name"] = node_name
    data["type"] = dep.typeName

    req = dep.pluginName
    if req:
        data["requirements"] = os.path.splitext(os.path.basename(req))[0]
    attributes: list[dict] = []
    visited: list[OpenMaya.MPlug] = []

    if node.hasFn(OpenMaya.MFn.kAnimCurve):
        data.update(animation.serialize_animation_curve(node))
    else:
        if extra_attributes_only:
            iterator = iterate_extra_attributes(
                node, skip=skip_attributes, include_attributes=include_attributes
            )
        else:
            iterator = iterate_attributes(
                node, skip=skip_attributes, include_attributes=include_attributes
            )
        for plug_found in iterator:
            if not plug_found:
                continue
            if (
                plug_found.isDefaultValue() and not plug_found.isDynamic
            ) or plug_found.isChild:
                continue
            attr_data = plugs.serialize_plug(plug_found)
            if attr_data:
                attributes.append(attr_data)
            visited.append(plug_found)
        if attributes:
            data["attributes"] = attributes

    if include_connections:
        connections: list[dict] = []
        for destination, source in iterate_connections(
            node, source=False, destination=True
        ):
            connections.append(plugs.serialize_connection(destination))
        if connections:
            data["connections"] = connections

    return data


def serialize_nodes(
    nodes: list[OpenMaya.MObject],
    skip_attributes: list[str] | None = None,
    include_connections: bool = True,
) -> Iterator[tuple[OpenMaya.MObject, dict]]:
    """Serializes given Maya objects.

    :param nodes: Maya objects to serialize.
    :param skip_attributes: list of attributes names to skip serialization of.
    :param include_connections: whether to find and serialize all connections where the destination is this
        node.
    :return: generator with the serialized nodes and the serialized data
    """

    for node in nodes:
        node_data = serialize_node(
            node,
            skip_attributes=skip_attributes,
            include_connections=include_connections,
        )
        if node.hasFn(OpenMaya.MFn.kNurbsCurve):
            curve_data = curves.serialize_transform_curve(node)
            if curve_data:
                node_data["shape"] = curve_data
        yield node, node_data


def serialize_selected_nodes(skip_attributes=None, include_connections=None):
    """Serializes selected Maya objects.

    :param list(str) skip_attributes: list of attributes names to skip serialization of.
    :param bool include_connections: whether to find and serialize all connections where the destination is this
        node.
    :return: generator with the serialized nodes and the serialized data
    :rtype: generator(tuple(OpenMaya.MObject, dict))
    """

    nodes = scene.selected_nodes()
    if not nodes:
        return

    yield serialize_nodes(
        nodes, skip_attributes=skip_attributes, include_connections=include_connections
    )


# noinspection PyShadowingNames
def deserialize_node(
    data, parent: OpenMaya.MObject | None = None, include_attributes: bool = True
) -> tuple[OpenMaya.MObject | None, list[OpenMaya.MPlug]]:
    """Deserializes given data and creates a new node based on that data.

    :param data: serialized node data.
    :param parent: the parent of the newly created node.
    :param include_attributes: whether to deserialize node attributes.
    :return: tuple with the newly created Maya object and a list of created plugs.

    Input example:
    {
            'name': '|root|auto|node',
            'parent': '|root|auto',
            'type': 'transform'
            'attributes':
            [
                    {
                            'type': 0,
                            'channelBox': false,
                            'default': false,
                            'isArray': false,
                            'isDynamic': true,
                            'keyable': true,
                            'locked': false,
                            'max': null,
                            'min': null,
                            'name': 'test',
                            'softMax': null,
                            'softMin': null,
                            'value': false
                    },
            ],
            'connections':
            [
                    {
                      'destination': '|root|auto|config',
                      'destinationPlug': 'run',
                      'source': '|control1|control2',
                      'sourcePlug': 'translateX'
                    },
            ]
    }
    """

    node_name = data["name"].split("|")[-1]
    node_type = data.get("type")
    if node_type is None:
        return None, []

    requirements = data.get("requirements", "")
    if requirements and not cmds.pluginInfo(requirements, loaded=True, query=True):
        try:
            cmds.loadPlugin(requirements)
        except RuntimeError:
            logger.error(
                "Could not load plugin: {}".format(requirements), exc_info=True
            )
            return None, []

    if "parent" in data:
        new_node = factory.create_dag_node(node_name, node_type, parent)
        mfn = OpenMaya.MFnDagNode(new_node)
        node_name = mfn.fullPathName()
    else:
        new_node = factory.create_dg_node(node_name, node_type)
        if new_node.hasFn(OpenMaya.MFn.kAnimCurve):
            mfn = OpenMayaAnim.MFnAnimCurve(new_node)
            mfn.setPreInfinityType(data["preInfinity"])
            mfn.setPostInfinityType(data["postInfinity"])
            mfn.setIsWeighted(data["weightTangents"])
            mfn.addKeysWithTangents(
                data["frames"],
                data["values"],
                mfn.kTangentGlobal,
                mfn.kTangentGlobal,
                data["inTangents"],
                data["outTangents"],
            )
            for i in range(len(data["frames"])):
                mfn.setAngle(i, OpenMaya.MAngle(data["inTangentAngles"][i]), True)
                mfn.setAngle(i, OpenMaya.MAngle(data["outTangentAngles"][i]), False)
                mfn.setWeight(i, data["inTangentWeights"][i], True)
                mfn.setWeight(i, data["outTangentWeights"][i], False)
                mfn.setInTangentType(i, data["inTangents"][i])
                mfn.setOutTangentType(i, data["outTangents"][i])
        else:
            mfn = OpenMaya.MFnDependencyNode(new_node)

        node_name = mfn.name()

    created_attributes: list[OpenMaya.MPlug] = []
    if not include_attributes:
        return new_node, created_attributes

    for attr_data in data.get("attributes", ()):
        name = attr_data["name"]
        try:
            found_plug = mfn.findPlug(name, False)
            found = True
        except RuntimeError:
            found_plug = None
            found = False
        if found:
            try:
                if found_plug.isLocked:
                    continue
                plugs.set_plug_info_from_dict(found_plug, **attr_data)
            except RuntimeError:
                full_name = ".".join([node_name, name])
                logger.error(f"Failed to set plug data: {full_name}", exc_info=True)
        else:
            if attr_data.get("isChild", False):
                continue
            short_name = name.split(".")[-1]
            children = attr_data.get("children")
            try:
                if children:
                    attr = add_compound_attribute(
                        new_node, short_name, short_name, attr_map=children, **attr_data
                    )
                elif attr_data.get("isElement", False):
                    continue
                else:
                    attr = add_attribute(new_node, short_name, short_name, **attr_data)
            except AttributeAlreadyExistsError:
                continue
            created_attributes.append(OpenMaya.MPlug(new_node, attr.object()))

    return new_node, created_attributes


def deserialize_nodes(
    nodes_data: list[dict],
) -> list[tuple[OpenMaya.MObject | None, list[OpenMaya.MPlug]]]:
    """Deserializes given nodes based on given data

    :param nodes_data: list of serialized node data.
    :return: newly created nodes.
    """

    created_nodes: list[tuple[OpenMaya.MObject | None, list[OpenMaya.MPlug]]] = []
    for node_data in nodes_data:
        created_node = deserialize_node(node_data)
        if created_node:
            created_nodes.append(created_node)

    return created_nodes


class AttributeAlreadyExistsError(Exception):
    """Exception that is raised when an attribute already exists."""

    pass
