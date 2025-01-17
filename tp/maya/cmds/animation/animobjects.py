from __future__ import annotations

import logging
from typing import Sequence

from maya import cmds

from ..nodeutils import selection

logger = logging.getLogger(__name__)


def filter_animated_nodes(node_names: Sequence[str]) -> list[str]:
    """
    Function that filters the given node names to only return the animated ones.

    :param node_names: List of node names to filter.
    :return: List of animated node names.
    """

    return [
        node_name
        for node_name in node_names
        if cmds.keyframe(
            node_name, query=True, keyframeCount=True, time=(-100000, 10000000)
        )
    ]


def get_animated_nodes(
    selection_flag: selection.SelectionFlag = selection.SelectionFlag.All,
    select: bool = True,
) -> list[str]:
    """
    Function that returns all animated nodes in the current scene.

    Selection Flags:
        - All: All nodes in the scene.
        - Selected: Only selected nodes.
        - Hierarchy: Only nodes in the hierarchy of selected nodes.

    :param selection_flag: Selection flag to determine which nodes to return.
    :param select: Whether to select the nodes or not after getting them.
    :return: List of animated nodes in the current scene that match the given selection flag.
    """

    selected_node_names, selection_warning = selection.selected_nodes_by_flag(
        selection_flag
    )
    found_animation_node_names = (
        filter_animated_nodes(selected_node_names) if selected_node_names else []
    )
    if found_animation_node_names and select:
        cmds.select(found_animation_node_names, replace=True)

    if found_animation_node_names:
        logger.debug(f"Found animated nodes: {found_animation_node_names}")
    elif selection_warning:
        logger.warning("Please select at least one node to get animated nodes.")
    else:
        logger.debug("No animation nodes found.")

    return found_animation_node_names


def select_animation_nodes(selection_flag: selection.SelectionFlag = selection.SelectionFlag.All):
    """
    Function that selects all animated nodes in the current scene.

    Selection Flags:
        - All: All nodes in the scene.
        - Selected: Only selected nodes.
        - Hierarchy: Only nodes in the hierarchy of selected nodes.

    :param selection_flag: Selection flag to determine which nodes to return.
    """

    get_animated_nodes(selection_flag, select=True)