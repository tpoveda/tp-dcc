from __future__ import annotations

from maya import cmds


def get_transforms(shapes_list: list[str], full_path: bool = True) -> list[str]:
    """
    Returns all transforms from a list of shape nodes.

    :param shapes_list: list of shape nodes to retrieve transform nodes from
    :param full_path: Whether to return full path of shape nodes or not
    :return: list of transform names related with the given shapes.
    """

    found_transform_names: list[str] = []
    for shape_node in shapes_list:
        parent = cmds.listRelatives(shape_node, parent=True, fullPath=full_path)[0]
        if cmds.objectType(parent, isType="transform"):
            found_transform_names.append(parent)

    return list(set(found_transform_names))
