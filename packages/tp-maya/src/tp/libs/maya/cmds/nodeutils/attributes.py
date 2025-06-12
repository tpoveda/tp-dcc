from __future__ import annotations

from maya import cmds


def reset_transform_attributes(
    node_name: str,
    rotate: bool = True,
    translate: bool = True,
    scale: bool = True,
    visibility: bool = True,
):
    """
    Resets the transformation attributes of the given node

    :param node_name: str, name of the node to reset transformation attributes for
    :param rotate: bool, Whether to reset rotation attributes
    :param translate: bool, Whether to reset translation attributes
    :param scale: bool, Whether to reset scale attributes
    :param visibility: bool, Whether to reset visibility attributes
    """

    if translate:
        cmds.setAttr(f"{node_name}.translate", 0.0, 0.0, 0.0)
    if rotate:
        cmds.setAttr(f"{node_name}.rotate", 0.0, 0.0, 0.0)
    if scale:
        cmds.setAttr(f"{node_name}.scale", 1.0, 1.0, 1.0)
    if visibility:
        cmds.setAttr(f"{node_name}.visibility", True)
