from __future__ import annotations

from maya import cmds


def selected_nodes(node_type: str = "transform"):
    """Returns the selected node names of the given type.

    Args:
        node_type: The type of nodes to return.

    Returns:
        The selected nodes of the given type.
    """

    return cmds.ls(selection=True, type=type) or []
