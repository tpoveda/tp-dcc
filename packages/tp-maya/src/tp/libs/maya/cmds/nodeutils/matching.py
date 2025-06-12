from __future__ import annotations

from typing import Sequence

from maya import mel, cmds

from . import selection, attributes


def center_of_multiple_nodes(node_names: list[str]) -> list[float]:
    """
    Returns the center of the given nodes.

    :param node_names: list of node names to get the center from.
    :return: center of the given nodes.
    """

    components_list = cmds.ls(node_names, flatten=True)
    count = len(components_list)
    sums = [0.0, 0.0, 0.0]
    for component in components_list:
        pos = cmds.xform(component, query=True, translation=True, worldSpace=True)
        for i in range(3):
            sums[i] += pos[i]

    return [sums[0] / count, sums[1] / count, sums[2] / count]


def center_of_selection():
    """
    Returns the averaged center of all selected nodes/components.

    :return: averaged center of all selected nodes/components.
    .info:: face/edge selection is not accurate through this method. Use `match_center_cluster` instead.
    """

    selection = cmds.ls(selection=True, flatten=True)
    if not selection:
        return None

    return center_of_multiple_nodes(selection)


def match_center_cluster(node_name: str, match_to_nodes: list[str]):
    """
    Matches the given node to the center of the cluster of the given nodes.

    :param node_name: name of the node to match.
    :param match_to_nodes: list of nodes to match to.
    """

    cmds.select(match_to_nodes, replace=True)
    cluster = cmds.cluster(name="tempPivot_XXX_cluster")[1]
    cmds.matchTransform(node_name, cluster, position=True, rotation=True, scale=False)
    cmds.delete(cluster)


def average_normals(normals: list[list[float]]) -> list[float]:
    """
    Returns the average normal of the given normals.

    :param normals: list of normals to get the average normal from.
    :return: average normal of the given normals.
    """

    count = len(normals)
    sums = [0.0, 0.0, 0.0]
    for normal in normals:
        for i in range(3):
            sums[i] += normal[i]

    return [sums[0] / count, sums[1] / count, sums[2] / count]


def average_vertices_normals(vertices: list[str]) -> list[float]:
    """
    Returns the average normal of the given vertices.

    :param vertices: list of vertices to get the average normal from.
    :return: average normal of the given vertices.
    """

    normals = cmds.polyNormalPerVertex(vertices, query=True, xyz=True)
    # noinspection PyTypeChecker
    normals: list[list[float]] = list(zip(*(iter(normals),) * 3))
    return average_normals(normals)


def face_normals(faces: list[str]) -> list[list[float]]:
    """
    Returns the normals of the given faces.

    :param faces: list of faces to get the normals from.
    :return: normals of the given faces.
    """

    normals: list[list[float]] = []
    normal_strings = cmds.polyInfo(faces, faceNormals=True)
    for normal_string in normal_strings:
        normal = normal_string.split()
        del normal[0:2]
        normal = [float(x) for x in normal]
        normals.append(normal)

    return normals


def average_face_normals(faces: list[str]) -> list[float]:
    """
    Returns the average normal of the given faces.

    :param faces: list of faces to get the average normal from.
    :return: average normal of the given faces.
    """

    normals = face_normals(faces)
    return average_normals(normals)


def create_group_from_vector(
    vector: Sequence[float],
    aim_vector: Sequence[float] = (0.0, 1.0, 0.0),
    local_up: Sequence[float] = (0.0, 0.0, -1.0),
    world_up: Sequence[float] = (0.0, 1.0, 0.0),
    relative_object: str = None,
) -> str:
    """
    Creates a group oriented to the given vector.

    :param vector: vector to aim the group to.
    :param aim_vector: direction to aim the group to.
    :param local_up: direction to aim the group up.
    :param world_up: world up of the aim.
    :param relative_object: object to aim the group to.
    :return: the transform node name of the group.
    """

    aim_node = cmds.group(empty=True)
    aim_group = cmds.group(empty=True)

    if relative_object:
        cmds.parent(aim_node, relative_object)
        cmds.parent(aim_group, relative_object)
        attributes.reset_transform_attributes(aim_node)
        attributes.reset_transform_attributes(aim_group)

    cmds.setAttr(
        f"{aim_node}.translate", vector[0], vector[1], vector[2], type="float3"
    )

    if relative_object:
        cmds.delete(
            cmds.aimConstraint(
                aim_group,
                aim_node,
                aimVector=aim_vector,
                upVector=local_up,
                worldUpVector=world_up,
                worldUpType="objectrotation",
                worldUpObject=relative_object,
            )
        )
    else:
        cmds.delete(
            cmds.aimConstraint(
                aim_group,
                aim_node,
                aimVector=aim_vector,
                upVector=local_up,
                worldUpVector=world_up,
            )
        )

    cmds.delete(aim_group)

    return aim_node


def create_group_orient_from_vertices(
    vertices: list[str],
    aim_vector: Sequence[float] = (0.0, 1.0, 0.0),
    local_up: Sequence[float] = (0.0, 0.0, -1.0),
    world_up: Sequence[float] = (0.0, 1.0, 0.0),
) -> str:
    """
    Creates a group oriented to the average vector of the selected vertices (using vertex normals).

    :param vertices: list of vertices to get the average vector from.
    :param aim_vector: direction to aim the group to.
    :param local_up: direction to aim the group up.
    :param world_up: world up of the aim.
    :return: the transform node name of the group.
    """

    normals = average_vertices_normals(vertices)
    relative_object = vertices[0].split(".")[0]
    return create_group_from_vector(
        normals,
        aim_vector=aim_vector,
        local_up=local_up,
        world_up=world_up,
        relative_object=relative_object,
    )


def create_group_orient_from_faces(
    faces: list[str],
    aim_vector: Sequence[float] = (0.0, 1.0, 0.0),
    local_up: Sequence[float] = (0.0, 0.0, -1.0),
    world_up: Sequence[float] = (0.0, 1.0, 0.0),
) -> str:
    """
    Creates a group oriented to the average vector of the selected faces (using face normals).

    :param faces: list of faces to get the average vector from.
    :param aim_vector: direction to aim the group to.
    :param local_up: direction to aim the group up.
    :param world_up: world up of the aim.
    :return: the transform node name of the group.
    """

    normals = cmds.polyInfo(faces, faceNormals=True)
    normals = [normal.split(":")[-1].strip() for normal in normals]
    normals = [list(map(float, normal.split())) for normal in normals]
    normals = average_normals(normals)
    relative_object = faces[0].split(".")[0]
    return create_group_from_vector(
        normals,
        aim_vector=aim_vector,
        local_up=local_up,
        world_up=world_up,
        relative_object=relative_object,
    )


def create_group_orient_from_components(
    components: list[str],
    aim_vector: Sequence[float] = (0.0, 1.0, 0.0),
    local_up: Sequence[float] = (0.0, 0.0, -1.0),
    world_up: Sequence[float] = (0.0, 1.0, 0.0),
) -> str:
    """
    Creates a group oriented to the average vector of the selected vertices/edges/faces.

    :param components: list of components to get the average vector from.
    :param aim_vector: direction to aim the group to.
    :param local_up: direction to aim the group up.
    :param world_up: world up of the aim.
    :return: the transform node name of the group.
    """

    selection_type = selection.component_selection_type(components)

    # If edges are selected, convert to vertices.
    if selection_type == selection.ComponentSelectionType.Edges:
        cmds.select(components, replace=True)
        components = selection.convert_selection(
            component_selection_type=selection.ComponentSelectionType.Vertices
        )
        selection_type = selection.ComponentSelectionType.Vertices

    if selection_type == selection.ComponentSelectionType.Vertices:
        return create_group_orient_from_vertices(
            components, aim_vector=aim_vector, local_up=local_up, world_up=world_up
        )
    elif selection_type == selection.ComponentSelectionType.Faces:
        return create_group_orient_from_faces(
            components, aim_vector=aim_vector, local_up=local_up, world_up=world_up
        )


def match_node_to_center_of_node_components(
    node_name: str,
    match_to_nodes: list[str],
    set_object_mode: bool = True,
    orient_to_components: bool = True,
    aim_vector: Sequence[float] = (0.0, 1.0, 0.0),
    local_up: Sequence[float] = (0.0, 0.0, -1.0),
    world_up: Sequence[float] = (0.0, 1.0, 0.0),
) -> bool:
    """
    Function that takes given node and:
        1. If no match to nodes are given it does nothing.
        2. If one object to match is given, it matches to the rotation and translation.
        3. If multiple objects to match are given, matches to the center of all DAG objects.
        4. If component selection (faces, vertices, edges) are given, it matches to the cent of the selection using
            cluster method and also uses average normal (in faces or vertices) to orient.

    :param node_name: name of the node to match.
    :param match_to_nodes: list of objects or components to match to.
    :param set_object_mode: whether to return to object mode if component mode is enabled.
    :param orient_to_components: whether to orient to the components.
    :param aim_vector: aim vector to use for the orientation.
    :param local_up: local up vector to use for the orientation.
    :param world_up: world up vector to use for the orientation.
    :return: whether the operation was successful or not.
    """

    if not match_to_nodes:
        return False

    selection_type = selection.component_or_object_selection_type(match_to_nodes)
    if not selection_type or selection_type == selection.SelectionType.UV:
        return False

    dag_nodes = cmds.ls(match_to_nodes, dag=True)
    if not dag_nodes and selection_type == selection.SelectionType.Object:
        return False

    if selection_type == selection.SelectionType.Object:
        # If only one object is selected, match to the object directly using the pivot point.
        if len(match_to_nodes) == 1:
            cmds.matchTransform(
                [node_name, match_to_nodes[0]],
                position=True,
                rotation=True,
                scale=False,
                pivot=False,
            )
            return True

        # If multiple objects are selected, match to the center of the objects.
        center_pos = center_of_multiple_nodes(match_to_nodes)
        cmds.move(center_pos[0], center_pos[1], center_pos[2], node_name, absolute=True)
        return True

    # If components are selected, match to the center of the components.
    match_center_cluster(node_name, match_to_nodes)

    if orient_to_components:
        orient_group = create_group_orient_from_components(
            match_to_nodes, aim_vector=aim_vector, local_up=local_up, world_up=world_up
        )
        cmds.matchTransform(
            [node_name, orient_group],
            position=False,
            rotation=True,
            scale=False,
            pivot=False,
        )
        cmds.delete(orient_group)

    if set_object_mode:
        if cmds.selectMode(query=True, component=True):
            mel.eval("SelectTool")
            cmds.selectMode(object=True)
            cmds.select(node_name, replace=True)

    return True
