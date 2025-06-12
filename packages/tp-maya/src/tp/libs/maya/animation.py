from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Iterator

from maya import cmds
from maya.api import OpenMayaAnim

from . import consts
from .wrapper import DagNode
from .om.animation import timerange


@dataclass
class NodeKeyInfo:
    name: str
    keys: set[int]
    rotation_order: int


def keyframes_for_node(
    node: DagNode,
    attributes: Sequence[str],
    default_key_frames: Sequence[int] | None = None,
    bake_every_frame: bool = False,
    frame_range: Sequence[int, int] | None = None,
) -> NodeKeyInfo:
    """
    Returns a dictionary with the keyframes, rotation order and name for the given node and attributes.

    - When `bake_every_frame` is True and `frame_range` is not None, then the given default is returned. This is due
        to the need to cache the keyframes to optimize the function across multiple requests.
    - When `frame_range` is None `bake_every_frame` is True, then the function will query the min and max keyframes for
        the attributes and will return all keyframes on whole numbers between them.

    :param node: node to get the keyframes from.
    :param attributes: list of attributes to get the keyframes from.
    :param default_key_frames: default keyframes to use if no keyframes are found.
    :param bake_every_frame: Whether to bake the keyframes on every frame or not.
    :param frame_range: Frame range to bake the keyframes on. If None, all keyframes will be returned.
    :return: Dictionary with the keyframes for the given attributes.
    """

    default_key_frames = default_key_frames or []
    node_name = node.fullPathName()

    # Bake all keyframes on every frame.
    if bake_every_frame:
        # Grab the keyframes for the given frame range or between the minimum and maximum keys.
        rotation_keys = (
            default_key_frames
            if frame_range
            else list(range(int(min(rotation_keys)), int(max(rotation_keys)) + 1))
            if (
                rotation_keys := cmds.keyframe(
                    node_name, attribute=attributes, query=True, timeChange=True
                )
            )
            else []
        )
    # Only bake the keyframes on the given frame range.
    elif frame_range:
        rotation_keys = cmds.keyframe(
            node_name,
            time=tuple(frame_range),
            attribute=attributes,
            query=True,
            timeChange=True,
        )
    # Bake current keyframes.
    else:
        rotation_keys = cmds.keyframe(
            node_name, attribute=attributes, query=True, timeChange=True
        )

    return NodeKeyInfo(
        name=node_name,
        keys=set(rotation_keys or []),
        rotation_order=node.rotationOrder(),
    )


def iterate_keyframes_for_nodes(
    nodes: Sequence[DagNode],
    attributes: Sequence[str],
    bake_every_frame: bool = False,
    frame_range: Sequence[int, int] | None = None,
) -> Iterator[tuple[DagNode, NodeKeyInfo]]:
    """
    Generator function that iterates over the keyframes for the given nodes and attributes.

    :param nodes: list of nodes to get the keyframes from.
    :param attributes: list of attributes to get the keyframes from.
    :param bake_every_frame: Whether to bake the keyframes on every frame or not.
    :param frame_range: Frame range to bake the keyframes on. If None, all keyframes will be returned.
    :return: Yields a tuple with the node and the keyframes for the given attributes.
    """

    all_keyframes = (
        list(range(*frame_range[:-1], frame_range[-1] + 1)) if frame_range else []
    )

    for node in nodes:
        yield (
            node,
            keyframes_for_node(
                node,
                attributes=attributes,
                default_key_frames=all_keyframes,
                bake_every_frame=bake_every_frame,
                frame_range=frame_range,
            ),
        )


def set_rotation_order_over_frames(
    nodes: Sequence[DagNode],
    rotation_order: int,
    bake_every_frame: bool = False,
    frame_range: tuple[int, int] | None = None,
):
    """
    Sets the rotation order of the given nodes over the given frame range while preserving animation.

    :param nodes: list of nodes to set the rotation order to.
    :param rotation_order: new rotation order to set to the given nodes.
    :param bake_every_frame: Whether to bake the rotation order on every frame or not.
    :param frame_range: Frame range to bake the rotation order on. If None, only existing keys will be updated.
    """

    rotation_order_name = consts.kRotateOrderNames[rotation_order]

    all_key_times = set()
    keyed_nodes_mapping: dict[DagNode, NodeKeyInfo] = {}
    unkeyed_node_names: set[str] = set()

    for node, node_key_info in iterate_keyframes_for_nodes(
        nodes,
        ["rotate", "rotateOrder"],
        bake_every_frame=bake_every_frame,
        frame_range=frame_range,
    ):
        if node_key_info.keys:
            all_key_times.update(node_key_info.keys)
            keyed_nodes_mapping[node] = node_key_info
        else:
            unkeyed_node_names.add(node_key_info.name)

    # Change rotation order for keyed objects.
    if keyed_nodes_mapping:
        all_key_times = list(all_key_times)
        all_key_times.sort()
        with timerange.maintain_time():
            # Force set keyframes on all rotation attributes, so we ensure original state is preserved.
            for context in timerange.iterate_frames_dg_context(all_key_times):
                frame_time = context.getTime()
                frame = frame_time.value
                OpenMayaAnim.MAnimControl.setCurrentTime(frame_time)
                for node, key_info in keyed_nodes_mapping.items():
                    if frame not in key_info.keys:
                        continue
                    node_name = key_info.name
                    cmds.setKeyframe(
                        node_name,
                        attribute="rotate",
                        preserveCurveShape=True,
                        respectKeyable=True,
                    )
                    if node.rotateOrder.isAnimated():
                        cmds.setKeyframe(
                            node_name, attribute="rotateOrder", preserveCurveShape=True
                        )

            # Actual rotation order change and keyframe new rotation values.
            for context in timerange.iterate_frames_dg_context(all_key_times):
                frame_time = context.getTime()
                frame = frame_time.value
                OpenMayaAnim.MAnimControl.setCurrentTime(frame_time)
                for node, key_info in keyed_nodes_mapping.items():
                    if frame not in key_info.keys:
                        continue
                    node_name = key_info.name
                    node.setRotationOrder(rotation_order)
                    cmds.setKeyframe(
                        node_name,
                        attribute="rotate",
                        preserveCurveShape=True,
                        respectKeyable=True,
                    )
                    if node.rotateOrder.isAnimated():
                        cmds.setKeyframe(
                            node_name, attribute="rotateOrder", preserveCurveShape=True
                        )

                    # Make sure to reset to original rotation order, so on next frame we have the original animation.
                    node.setRotationOrder(
                        rotate_order=key_info.rotation_order, preserve=False
                    )

        # Here we use cmds, so undo works as expected.
        for key_info in keyed_nodes_mapping.values():
            cmds.xform(key_info.name, rotateOrder=rotation_order_name, preserve=False)
        cmds.filterCurve([key_info.name for key_info in keyed_nodes_mapping.values()])

    # Change rotation order for unkeyed objects.
    for node_name in unkeyed_node_names:
        cmds.xform(node_name, rotateOrder=rotation_order_name, preserve=True)
