"""
Module that contains functions related with Maya Skin Cluster node
"""

from __future__ import annotations

from typing import Iterator

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaAnim as OpenMayaAnim

from tp.core import log, command
from tp.common.python import helpers
from tp.maya.om import dagpath, plugs, plugmutators, mesh, undo

logger = log.tpLogger

ZERO_TOLERANCE = 1e-3


def num_control_points(skin_cluster: OpenMaya.MObject) -> int:
    """
    Returns the number of control points given skin cluster affects.

    :param OpenMaya.MObject skin_cluster: skin cluster node.
    :return: number of control points given skin cluster affects.
    :rtype: int
    """

    return OpenMaya.MFnDependencyNode(skin_cluster).findPlug('weightList', False).numElements()


def lock_transform(node: str | OpenMaya.MObject | OpenMaya.MDagPath):
    """
    Locks the transform attributes on the given node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to lock transform of.
    """

    node = dagpath.mobject(node)
    if node.hasFn(OpenMaya.MFn.kShape):
        node = dagpath.parent(node)

    # Lock transform attributes.
    for attribute in ('translate', 'rotate', 'scale'):
        plug = plugs.find_plug(node, attribute)
        for child_plug in plugs.iterate_children(plug):
            child_plug.isLocked = True

    # Disable inherits transform.
    plug = plugs.find_plug(node, 'inheritsTransform')
    plugmutators.set_value(plug, False)


def clear_intermediate_objects(node: str | OpenMaya.MObject | OpenMaya.MDagPath):
    """
    Removes any intermediate objects from the given node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node we want to remove intermediate objects of.
    """

    node = dagpath.mobject(node)
    if node.hasFn(OpenMaya.MFn.kShape):
        node = dagpath.parent(node)

    # Iterate through intermediate objects.
    intermediate_objects = list(dagpath.iterate_intermediate_objects(node))
    for intermediate_object in intermediate_objects:
        logger.info(f'Removing intermediate object: {dagpath.node_name(intermediate_object)}')
        dagpath.delete_node(intermediate_object)


def iterate_influences(skin_cluster: OpenMaya.MObject) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields all the influence objects from the given skin cluster.

    :param OpenMaya.MObject skin_cluster: skin cluster we want to retrieve influence objects from.
    :return: iterated influence objects from the given skin cluster.
    :rtype: Iterator[OpenMaya.MObject]
    """

    fn_depend_node = OpenMaya.MFnDependencyNode(skin_cluster)
    plug = fn_depend_node.findPlug('matrix', False)
    num_elements = plug.evaluateNumElements()
    for i in range(num_elements):
        element = plug.elementByPhysicalIndex(i)
        index = element.logicalIndex()
        if not element.isConnected:
            logger.debug(f'No connected joint found on {fn_depend_node.name()}.matrix[{index}]!')
            continue

        other_plug = element.source()
        other_node = other_plug.node()
        if not other_node.isNull():
            yield index, other_node
        else:
            logger.debug(f'Null object found on {fn_depend_node.name()}.matrix[{index}]!')
            continue


def find_skin_cluster(
        dag_path: str | OpenMaya.MDagPath | None = None) -> tuple[OpenMayaAnim.MFnSkinCluster | None, str | None]:
    """
    Loops through the DAG hierarchy of the given DAG path finding a skin cluster.

    :param OpenMaya.MDagPath dag_path: dag to loop.
    :return: Skin cluster object and skin cluster node name.
    :rtype: tuple[OpenMayaAnim.MFnSkinCluster or None, str or None]
    """

    if not dag_path:
        return None, None

    if not helpers.is_string(dag_path):
        dag_path = dag_path.fullPathName()

    found_skin_cluster = cmds.ls(cmds.listHistory(dag_path), type='skinCluster')
    if not found_skin_cluster:
        return None, None

    skin_name = found_skin_cluster[0]
    selection_list = OpenMaya.MSelectionList(skin_name)

    skin_node = selection_list.getDependNode(0)
    skin_node = OpenMayaAnim.MFnSkinCluster(skin_node)

    return skin_node, skin_name


def iterate_weights(
        skin_cluster: OpenMaya.MObject, vertex_index: int,
        plug: OpenMaya.MPlug | None = None) -> Iterator[tuple[int, float]]:
    """
    Returns a generator that yields the weights for the given vertex.

    :param OpenMaya.MObject skin_cluster: skin cluster we want to iterate weights of.
    :param int vertex_index: index of the weight to iterate.
    :param OpenMaya.MPlug or None plug: optional plug used for optimization purposes when yielding a list of vertices.
    :return: iterated weights for the given vertex.
    :rtype: Iterator[tuple[int, float]]
    """

    plug = plug or plugs.find_plug(skin_cluster, f'weightList[{vertex_index}].weights')
    num_elements = plug.numElements()
    for physical_index in range(num_elements):
        element = plug.elementByPhysicalIndex(physical_index)
        influence_id = element.logicalIndex()
        influence_weight = element.asFloat()
        yield influence_id, influence_weight


def iterate_weights_list(
        skin_cluster: OpenMaya.MObject,
        vertex_indices: list[int] | tuple[int] | None = None) -> Iterator[list[tuple[int, float]]]:
    """
    Returns a generator that yields the vertex weights from the given skin cluster.

    :param OpenMaya.MObject skin_cluster: skin cluster we want to iterate weights of.
    :param list[int] or tuple[int] or None vertex_indices: optional list of vertex indices can be supplied to limit
        the generator.
    :return: iterated vertex weights from the given skin cluster.
    :rtype: Iterator[list[tuple[int, float]]]
    """

    if helpers.is_null_or_empty(vertex_indices):
        vertex_indices = list(range(num_control_points(skin_cluster)))

    weight_list_plug = plugs.find_plug(skin_cluster, 'weightList')
    for vertex_index in vertex_indices:
        element = weight_list_plug.elementByLogicalIndex(vertex_index)
        weights_plug = element.child(0)
        weights = dict(iterate_weights(skin_cluster, vertex_index, plug=weights_plug))
        yield vertex_index, weights


def skin_weights(skin_cluster: str | OpenMayaAnim.MFnSkinCluster, mesh_shape_name: str):
    """
    Returns the skin weights of the given skin cluster in the given mesh.

    :param str or OpenMayaAnim.MFnSkinCluster skin_cluster: skin cluster node.
    :param str mesh_shape_name: name of the mesh to get skin weights of.
    :return:
    """

    found_skin_cluster = skin_cluster
    if helpers.is_string(skin_cluster):
        found_skin_cluster, _ = find_skin_cluster(skin_cluster)
    if not found_skin_cluster:
        return None

    mesh_path, mesh_components = mesh.mesh_path_and_components(mesh_shape_name)
    if not mesh_path or not mesh_components:
        return None

    influences_array = OpenMaya.MIntArray()
    path_array = found_skin_cluster.influenceObjects()
    influences_count = len(path_array)
    for i in range(influences_count):
        influences_array.append(found_skin_cluster.indexForInfluenceObject(path_array[i]))

    weights = found_skin_cluster.getWeights(mesh_path, mesh_components, influences_array)

    return weights


def has_influence(skin_cluster: OpenMaya.MObject, influence: OpenMaya.MObject) -> bool:
    """
    Returns whether given skin cluster has the given influence object.

    :param OpenMaya.MObject skin_cluster: skin cluster to check influence of.
    :param OpenMaya.MObject influence: influence object to check.
    :return: True if given influence is part of the skin cluster; False otherwise.
    :rtype: bool
    """

    found_dag_path = dagpath.dag_path(influence)
    if not found_dag_path.isValid():
        return False

    instance_number = found_dag_path.instanceNumber()
    plug = plugs.find_plug(found_dag_path.node(), f'worldMatrix[{instance_number}]')
    other_plugs = plug.destinations()

    return any([other_plug.node() == skin_cluster for other_plug in other_plugs])


def influence_id(skin_cluster: OpenMaya.MObject, influence: OpenMaya.MObject) -> int | None:
    """
    Returns the influence ID for the given influence object.

    :param OpenMaya.MObject skin_cluster: skin cluster to get influence index of.
    :param OpenMaya.MObject influence: influence object to get index for.
    :return: influence index.
    :rtype: int or None
    """

    found_dag_path = dagpath.dag_path(influence)
    if not found_dag_path.isValid():
        return None

    instance_number = found_dag_path.instanceNumber()
    plug = plugs.find_plug(found_dag_path.node(), f'worldMatrix[{instance_number}]')
    other_plugs = plug.destinations()
    for otherPlug in other_plugs:
        other_node = otherPlug.node()
        if other_node == skin_cluster:
            return otherPlug.logicalIndex()

    return None


def influence(skin_cluster: OpenMaya.MObject, influence_index: int) -> OpenMaya.MObject | None:
    """
    Returns the influence object of the given index.

    :param OpenMaya.MObject skin_cluster: skin cluster to get influence from.
    :param int influence_index: influence index to get object for.
    :return: found influence object at given index.
    :rtype: OpenMaya.MObject or None
    """

    plug = plugs.find_plug(skin_cluster, f'matrix[{influence_index}]')
    other_plug = plug.source()
    if other_plug.isNull:
        logger.warning(f'Unable to locate influence at ID: {influence_index}')
        return None

    return other_plug.node()


@undo.undo(name='Add Influence')
def add_influence(skin_cluster: OpenMaya.MObject, influence_to_add: OpenMaya.MObject, index: int | None = None) -> int:
    """
    Adds the given influence object to the given skin cluster.

    :param OpenMaya.MObject skin_cluster: skin cluster we want to add influence to.
    :param OpenMaya.MObject influence_to_add: influence object to add to skin cluster.
    :param int or None index: optional index for the new influence.
    :return: index of the added influence.
    :rtype: int
    """

    # Check if influence has already been added.
    if has_influence(skin_cluster, influence_to_add):
        return influence_id(skin_cluster, influence_to_add)

    # Get first available index.
    fn_skin_cluster = OpenMaya.MFnDependencyNode(skin_cluster)
    skin_cluster_name = fn_skin_cluster.absoluteName()
    plug = fn_skin_cluster.findPlug('matrix', False)
    if index is None:
        index = plugs.next_available_connection(plug)

    # Connect joint to skin cluster.
    dag_path = dagpath.dag_path(influence_to_add)
    fn_influence = OpenMaya.MFnDagNode(dag_path)
    influence_name = fn_influence.fullPathName()
    instance_number = dag_path.instanceNumber()

    cmds.connectAttr(f'{influence_name}.worldMatrix[{instance_number}]', f'{skin_cluster_name}.matrix[{index}]')
    cmds.connectAttr(f'{influence_name}.objectColorRGB', f'{skin_cluster_name}.influenceColor[{index}]')

    # Check if ".lockInfluenceWeights" attribute exists and add attribute to joint if it does not exist.
    if not cmds.attributeQuery('lockInfluenceWeights', exists=True, node=influence_name):
        cmds.addAttr(
            influence_name, cachedInternally=True, shortName='liw', longName='lockInfluenceWeights', min=0, max=1,
            attributeType='bool')

    # Connect custom attribute.
    cmds.connectAttr(f'{influence_name}.lockInfluenceWeights', f'{skin_cluster_name}.lockWeights[{index}]')

    # Set pre-bind matrix.
    matrix_list = cmds.getAttr(f'{influence_name}.worldInverseMatrix[{instance_number}]')
    cmds.setAttr(f'{skin_cluster_name}.bindPreMatrix[{index}]', matrix_list, type='matrix')


@undo.undo(name='Remove Influence')
def remove_influence(skin_cluster: OpenMaya.MObject, influence_index: int) -> bool:
    """
    Removes the influence with given index from the given skin cluster.

    :param OpenMaya.MObject skin_cluster: skin cluster we want to remove influence from.
    :param int influence_index: index of the influence object to remove from skin cluster.
    :return: True if influence was removed from skin cluster successfully; False otherwise.
    :rtype: bool
    """

    influence_to_remove = influence(skin_cluster, influence_index)
    if influence_to_remove is None:
        return False

    # Disconnect joint from skin cluster.
    fn_skin_cluster = OpenMaya.MFnDependencyNode(skin_cluster)
    skin_cluster_name = fn_skin_cluster.absoluteName()

    fn_influence = OpenMaya.MFnDagNode(influence)
    influence_name = fn_influence.fullPathName()
    instance_number = fn_influence.dagPath().instanceNumber()

    cmds.disconnectAttr(
        f'{influence_name}.worldMatrix[{instance_number}]', f'{skin_cluster_name}.matrix[{influence_index}]')
    cmds.disconnectAttr(
        f'{influence_name}.objectColorRGB', f'{skin_cluster_name}.influenceColor[{influence_index}]')
    cmds.disconnectAttr(
        f'{influence_name}.lockInfluenceWeights', f'{skin_cluster_name}.lockWeights[{influence_index}]')
    cmds.deleteAttr(f'{influence_name}.lockInfluenceWeights')

    return True


def select_influence(skin_cluster: OpenMaya.MObject, influence_index: int):
    """
    Selects the influence with given index.

    :param OpenMaya.MObject skin_cluster: skin cluster influence we want to select is connected to.
    :param int influence_index: index of the influence object to select.
    """

    influence_to_select = influence(skin_cluster, influence_index)
    if influence_to_select is None:
        logger.warning(f'Unable to select influence index: {influence_index}')
        return

    # Connect plugs.
    source = plugs.find_plug(influence_to_select, 'message')
    destination = plugs.find_plug(skin_cluster, 'paintTrans')

    plugs.connect_plugs(source, destination, force=True)


def set_skin_weights(skin_cluster, mesh_shape_name, skin_data):
    _skin_cluster = None
    if helpers.is_string(skin_cluster):
        _skin_cluster, _ = skin_cluster(skin_cluster)
    if not _skin_cluster:
        return None

    skin_data = str(list(skin_data))

    mesh_path, mesh_components = mesh.mesh_path_and_components(mesh_shape_name)
    if not mesh_path or not mesh_components:
        return None

    influences_array = OpenMaya.MIntArray()
    path_array = _skin_cluster.influenceObjects()
    influences_count = len(path_array)
    for i in range(influences_count):
        influences_array.append(_skin_cluster.indexForInfluenceObject(path_array[i]))

    weights_array = OpenMaya.MDoubleArray()
    for i in skin_data[1:-1].split(','):
        weights_array.append(float(i))

    runner = command.CommandRunner()

    runner.run(
        'tp-maya-commands-setSkinWeights',
        skin_cluster=_skin_cluster, mesh_path=mesh_path, mesh_components=mesh_components,
        influences_array=influences_array, weights_array=weights_array)

    # skin_cluster.setWeights(mesh_path, mesh_components, influences_array, weights_array, False)


def set_weights(skin_cluster: OpenMaya.MObject, vertex_index: int, weights: dict[int, float], plug: OpenMaya.MPlug | None, modifier: OpenMaya.MDGModifier | None = None):
    """Updates the weights for the given vertex.

    :param OpenMaya.MObject skin_cluster: skin cluster to update weights of.
    :param int vertex_index: index of the vertex to update weights for.
    :param dict[int, float] weights: weights to apply.
    :param OpenMaya.MPlug or None plug: plug to update weights of. If not given, weights plug for given vertex index
        will be used.
    :param OpenMaya.MDGModifier or None modifier: optional modifier to use to apply weights with.
    """

    fn_depend_node = OpenMaya.MFnDependencyNode(skin_cluster)

    plug = plug or plugs.find_plug(skin_cluster, f'weightList[{vertex_index}].weights')
    modifier = modifier or OpenMaya.MDGModifier()

    # Remove unused influences.
    influence_ids = plug.getExistingArrayAttributeIndices()
    diff = list(set(influence_ids) - set(weights.keys()))
    for influence_id in diff:
        cmds.removeMultiInstance(f'{fn_depend_node.absoluteName()}.weightList[{vertex_index}].weights[{influence_id}]')

    # Iterate through new weights.
    for influence_id, weight in weights.items():

        # Check for zero weights and be sure to remove these when encountered!
        if weight <= ZERO_TOLERANCE:
            cmds.removeMultiInstance(
                f'{fn_depend_node.absoluteName()}.weightList[{vertex_index}].weights[{influence_id}]')
        else:
            element = plug.elementByLogicalIndex(influence_id)
            plugmutators.set_float(element, weight, modifier=modifier)

    undo.commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()


@undo.undo(name='Set Skin Weights')
def set_weight_list(
        skin_cluster: OpenMaya.MObject, weigh_list: dict[int, dict[int, float]],
        modifier: OpenMaya.MDGModifier | None = None):
    """Updates the weights for all the given vertices.

    :param OpenMaya.MObject skin_cluster: skin cluster to update weights of.
    :param dict[int, dict[int, float]] weigh_list: weights to apply.
    :param OpenMaya.MDGModifier or None modifier: optional modifier to use to apply weights with.
    """

    # Disable normalize weights.
    normalize_plug = plugs.find_plug(skin_cluster, 'normalizeWeights')
    normalize_plug.setBool(False)

    try:
        # Iterate through vertices.
        weight_list_plug = plugs.find_plug(skin_cluster, 'weightList')
        for vertex_index, weights in weigh_list.items():
            # Get pre-existing influences
            element = weight_list_plug.elementByLogicalIndex(vertex_index)
            weights_plug = element.child(0)
            set_weights(skin_cluster, vertex_index, weights, plug=weights_plug, modifier=modifier)
    finally:
        # Re-enable normalize weights
        normalize_plug.setBool(True)


def prebind_matrix(skin_cluster: OpenMaya.MObject, influence_id: int) -> OpenMaya.MMatrix:
    """Returns the pre-bind matrix for the given influence ID.

    :param OpenMaya.MObject skin_cluster: skin cluster to get pre-bind matrix from.
    :param int influence_id: ID of the influence to get pre-bind matrix of.
    :return: influence pre-bind matrix.
    :rtype: OpenMaya.MMatrix
    """

    plug = plugs.find_plug(skin_cluster, 'bindPreMatrix')
    element = plug.elementByLogicalIndex(influence_id)

    return plugmutators.value(element)


@undo.undo(name='Reset Pre-Bind Matrices')
def reset_prebind_matrices(skin_cluster: OpenMaya.MObject, modifier: OpenMaya.MDGModifier | None = None):
    """Resets the pre-bind matrices on the given skin cluster influences.

    :param OpenMaya.MObject skin_cluster: skin cluster whose influences we want to reset pre-bind matrices of.
    :param OpenMaya.MDGModifier or None modifier: optional modifier to use to reset pre-bind matrices with.
    """

    modifier = modifier or OpenMaya.MDGModifier()

    # Iterate through matrix elements.
    plug = plugs.find_plug(skin_cluster, 'bindPreMatrix')
    num_elements = plug.evaluateNumElements()
    for i in range(num_elements):
        # Get inverse matrix of influence and check if influence still exists.
        element = plug.elementByPhysicalIndex(i)
        index = element.logicalIndex()
        found_influence = influence(skin_cluster, index)
        if found_influence is None:
            continue
        # Get world inverse matrix from influence.
        dag_path = OpenMaya.MDagPath.getAPathTo(found_influence)
        world_inverse_matrix_plug = plugs.find_plug(found_influence, f'worldInverseMatrix[{dag_path.instanceNumber()}]')
        world_inverse_matrix = plugmutators.as_matrix(world_inverse_matrix_plug)
        plugmutators.set_matrix(element, world_inverse_matrix, modifier=modifier)

    undo.commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()


@undo.undo(name='Reset Intermediate Object')
def reset_intermediate_object(skin_cluster: OpenMaya.MObject):
    """Resets the control points on the intermediate object of the given skin cluster.

    :param OpenMaya.MObject skin_cluster: skin cluster with the intermediate object we want to reset.
    """

    # Store deformed points.
    transform, shape, intermediate_object = dagpath.decompose_deformer(skin_cluster)
    shape = OpenMaya.MDagPath.getAPathTo(shape)
    iter_vertex = OpenMaya.MItMeshVertex(shape)
    points: list[list[float, float, float]] = []
    while not iter_vertex.isDone():
        point = iter_vertex.position()
        points.append([point.x, point.y, point.z])
        iter_vertex.next()

    # Reset influences.
    reset_prebind_matrices(skin_cluster)

    # Apply deformed values to intermediate object.
    intermediate_object = OpenMaya.MDagPath.getAPathTo(intermediate_object)
    iter_vertex = OpenMaya.MItMeshVertex(intermediate_object)
    while not iter_vertex.isDone():
        point = points[iter_vertex.index()]
        iter_vertex.setPosition(OpenMaya.MPoint(point))
        iter_vertex.next()
