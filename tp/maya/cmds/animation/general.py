from __future__ import annotations

import logging

from maya import cmds, mel

from tp.python.decorators import log_arguments

from . import timerange
from ... import consts, wrapper, animation

logger = logging.getLogger(__name__)


@log_arguments()
def change_rotation_order(
    nodes: list[str] | list[wrapper.DagNode] | None = None,
    new_rotation_order: int = consts.kRotateOrder_XYZ,
    bake_every_frame: bool = False,
    timeline: bool = True,
):
    """
    Sets the rotation order of the given nodes.

    :param nodes: nodes to set the rotation order of. If not given, current selected scene nodes are used.
    :param new_rotation_order: new rotation order number to set (from 0 to 5).
    :param bake_every_frame: whether to bake the rotation order every frame.
    :param timeline: whether the current active timeline should be used as a key filter.
    """

    nodes = [
        wrapper.node_by_name(node) if isinstance(node, str) else node
        for node in (
            nodes or wrapper.selected(filter_types=wrapper.kNodeTypes.kTransform)
        )
        if node
    ]
    if not nodes:
        logger.warning("No nodes to change rotation order for!")
        return

    start, end = map(int, timerange.get_selected_or_current_frame_range())
    frame_range: tuple[int, int] = (start, end)
    animation.set_rotation_order_over_frames(
        nodes,
        new_rotation_order,
        bake_every_frame=bake_every_frame,
        frame_range=frame_range,
    )


def set_key_all():
    """
    Sets a key on all attributes, ignoring any selected Channel Box channel.
    """

    mel.eval("setKeyframe")


def set_key_channel():
    """
    Set key on all attribute channels, but if any channel box attributes are selected, then key only those channels.
    """

    selected_attributes = mel.eval("selectedChannelBoxAttributes")
    if not selected_attributes:
        set_key_all()
        return

    cmds.setKeyframe(breakdown=False, attribute=selected_attributes)
