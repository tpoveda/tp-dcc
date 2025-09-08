from __future__ import annotations

import math

from loguru import logger
from maya import cmds
from maya.api import OpenMaya

from ..nodeutils import naming


def get_skin_cluster(mesh_node_name: str) -> list[str]:
    """Returns the skin cluster attached to the given node.

    Args:
        mesh_node_name: Name of the mesh node to get the skin cluster from.

    Returns:
        Skin clusters node names.
    """

    unique_short_name = naming.get_unique_short_name(mesh_node_name)
    history = (
        cmds.listHistory(
            unique_short_name,
            pruneDagObjects=True,
            interestLevel=2,
        )
        or []
    )
    # noinspection PyTypeChecker
    return cmds.ls(history, type="skinCluster") or []


def get_skin_clusters(node_names: list[str]) -> list[str]:
    """Returns the skin clusters attached to the given nodes.

    Args:
        node_names: List of node names to get the skin clusters from.

    Returns:
        List of skin clusters node names.
    """

    skin_clusters: list[str] = []
    for node_name in node_names:
        skin_clusters.extend(get_skin_cluster(node_name))

    return skin_clusters


def get_selected_skin_clusters() -> list[str]:
    """Returns the skin clusters attached to the selected nodes.

    Returns:
        List of skin clusters node names.
    """

    selected_nodes = cmds.ls(selection=True, long=True) or []
    return get_skin_clusters(selected_nodes)


def transfer_skin_weights(
    source_mesh_node_name: str, target_mesh_node_name: str
) -> str | None:
    """Transfers the skin weights from the source mesh to the target mesh.

    Args:
        source_mesh_node_name: Name of the source mesh node.
        target_mesh_node_name: Name of the target mesh node.

    Returns:
        The name of the new skin cluster created on the target mesh; `None` if
        the operation failed.
    """

    source_skin_clusters = get_skin_cluster(source_mesh_node_name)
    if not source_skin_clusters:
        logger.warning(
            f"No skin cluster found on source mesh '{source_mesh_node_name}'"
        )
        return None
    if len(source_skin_clusters) > 1:
        logger.warning(
            f"Multiple skin clusters found on source mesh '{source_mesh_node_name}'. "
            f"Using the first one: '{source_skin_clusters[0]}'"
        )

    source_skin_cluster = source_skin_clusters[0]

    target_skin_clusters = get_skin_cluster(target_mesh_node_name)
    target_skin_cluster = target_skin_clusters[0] if target_skin_clusters else None
    if not target_skin_cluster:
        influences = cmds.skinCluster(source_skin_cluster, query=True, influence=True)
        target_skin_cluster = cmds.skinCluster(
            target_mesh_node_name, influences, toSelectedBones=True
        )[0]

    cmds.copySkinWeights(
        sourceSkin=source_skin_cluster,
        destinationSkin=target_skin_cluster,
        noMirror=True,
        surfaceAssociation="closestPoint",
        smooth=True,
    )

    return target_skin_cluster


def transfer_skin_weights_for_selection() -> bool:
    """Transfers the skin weights from the first selected object to the rest
    of selected objects.

    Returns:
        `True` if the operation was successful; `False` otherwise.
    """

    selected_nodes = cmds.ls(selection=True, long=True)
    if not selected_nodes:
        logger.warning(
            "No objects selected. Please select at least two skinned meshes."
        )
        return False
    if len(selected_nodes) < 2:
        logger.warning("Please select at least two skinned meshes.")
        return False

    for target_node in selected_nodes[1:]:
        transfer_skin_weights(selected_nodes[0], target_node)

    return True


def toggle_skin_cluster_for_selection() -> bool:
    """Toggles the skin cluster display for the selected meshes.

    Returns:
        `True` if the operation was successful; `False` otherwise.
    """

    selected_nodes = cmds.ls(selection=True, long=True)
    if not selected_nodes:
        logger.warning("No objects selected. Please select at least one object.")
        return False

    if not toggle_skin_clusters(selected_nodes):
        return False

    return True


def toggle_skin_clusters(node_names: list[str], freeze: bool = False) -> list[str]:
    """Toggles the skin cluster display for the given meshes.

    Args:
        node_names: List of mesh node names to toggle the skin cluster for.
        freeze: If `True`, freezes the joints after setting the bind pose.

    Returns:
        List of skin clusters node names.
    """

    skin_clusters: list[str] = []
    for node_name in node_names:
        skin_cluster = toggle_skin_cluster(node_name, freeze=freeze)
        if not skin_cluster:
            continue
        skin_clusters.append(skin_cluster)

    return skin_clusters


def toggle_skin_cluster(mesh_node_name: str, freeze: bool = False) -> str | None:
    """Sets the bind pose for the skin cluster attached to the given mesh node.

    Args:
        mesh_node_name: Name of the mesh node to set the bind pose for.
        freeze: If `True`, freezes the joints after setting the bind pose.

    Returns:
        The name of the skin cluster; `None` if no skin cluster was found.
    """

    skin_clusters = get_skin_cluster(mesh_node_name)
    if not skin_clusters:
        return None

    if len(skin_clusters) > 1:
        logger.warning(
            f"Multiple skin clusters found on mesh '{mesh_node_name}'. "
            f"Using the first one: '{skin_clusters[0]}'"
        )

    skin_cluster = skin_clusters[0]

    joints = (
        cmds.listConnections(f"{skin_cluster}.matrix", type="joint", destination=True)
        or []
    )
    joint_indexes = cmds.getAttr(f"{skin_cluster}.matrix", multiIndices=True) or []
    for joint, index in zip(joints, joint_indexes):
        world_inverse_matrix = cmds.getAttr(f"{joint}.worldInverseMatrix")
        cmds.setAttr(
            f"{skin_cluster}.bindPreMatrix[{index}]",
            world_inverse_matrix,
            type="matrix",
        )
    # noinspection PyTypeChecker
    cmds.dagPose(
        joints,
        cmds.listConnections(f"{skin_cluster}.bindPose", type="dagPose"),
        reset=True,
    )

    if freeze:
        freeze_joints(joints)

    return skin_cluster


def freeze_joint(joint_name: str):
    """Freezes the joint transformation and sets the `jointOrient` to zero.

    Args:
        joint_name: Name of the joint to freeze.
    """

    selection = OpenMaya.MSelectionList()
    selection.add(joint_name)
    joint_object = OpenMaya.MFnTransform(selection.getDagPath(0))

    # Current local rotation as matrix.
    local_rotation_matrix = joint_object.rotation().asMatrix()

    # Read jointOrient (X,Y,Z in degrees) and convert to radians Euler.
    joint_orient_plug = joint_object.findPlug("jointOrient", False)
    joint_orient_x = joint_orient_plug.child(0).asDouble()
    joint_orient_y = joint_orient_plug.child(1).asDouble()
    joint_orient_z = joint_orient_plug.child(2).asDouble()
    joint_orient_euler = OpenMaya.MEulerRotation(
        math.radians(joint_orient_x),
        math.radians(joint_orient_y),
        math.radians(joint_orient_z),
    )

    # New rotation = local_rotate * jointOrient.
    new_rotation_matrix = local_rotation_matrix * joint_orient_euler.asMatrix()
    new_rotation_euler = OpenMaya.MTransformationMatrix(new_rotation_matrix).rotation()

    # Zero .rotate and set .jointOrient to new_rot (in degrees).
    # noinspection PyTypeChecker
    cmds.setAttr(f"{joint_name}.rotate", 0, 0, 0)
    cmds.setAttr(
        f"{joint_name}.jointOrient",
        *map(
            math.degrees,
            (new_rotation_euler.x, new_rotation_euler.y, new_rotation_euler.z),
        ),
        type="double3",
    )


def freeze_joints(joint_names: list[str]):
    """Freezes the joint transformations and sets the `jointOrient` to zero.

    Args:
        joint_names: List of joint names to freeze.
    """

    for joint_name in joint_names:
        freeze_joint(joint_name)
