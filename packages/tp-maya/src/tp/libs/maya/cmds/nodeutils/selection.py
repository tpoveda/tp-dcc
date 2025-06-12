from __future__ import annotations

import enum
from typing import Sequence

from maya import mel, cmds


class SelectionFlag(enum.Enum):
    """Enumeration that defines the selection flags."""

    # All nodes in the scene.
    All = 0

    # Selected nodes in the scene.
    Selected = 1

    # Selected nodes and their children in the scene.
    Hierarchy = 2


class SelectionType(enum.Enum):
    """Enumeration that defines the selection types."""

    # Object selection type.
    Object = 0

    # Component selection type.
    Component = 1

    # UV selection type.
    UV = 2


class ComponentSelectionType(enum.Enum):
    """Enumeration that defines the component selection types."""

    # Vertices selection type.
    Vertices = 1

    # Edges selection type.
    Edges = 2

    # Faces selection type.
    Faces = 3

    # UV selection type.
    UV = 4

    # EdgeLoop selection type.
    EdgeLoop = 5

    # EdgeRing selection type.
    EdgeRing = 6

    # EdgePerimeter selection type.
    EdgePerimeter = 7

    # UVShell selection type.
    UVShell = 8

    # UVShellBorder selection type.
    UVShellBorder = 9


def selected_nodes(node_type: str = "transform", full_path: bool = True):
    """Returns the selected node names of the given type.

    Args:
        node_type: The type of nodes to return.
        full_path: Whether to return the full path of the nodes.

    Returns:
        The selected nodes of the given type.
    """

    return cmds.ls(selection=True, type=node_type, long=full_path) or []


def selected_nodes_by_flag(
    selection_flag: SelectionFlag, full_path: bool = False
) -> tuple[Sequence[str], bool]:
    """
    Returns the selected nodes based on the given selection flag.

    :param selection_flag: The selection flag to use.
    :param full_path: Whether to return the full path of the nodes.
    :return: A tuple containing the selected nodes and a flag indicating if the operation was successful.
    :raises ValueError: If the selection flag is invalid.
    """

    selection_warning: bool = False
    if selection_flag == SelectionFlag.All:
        found_node_names = cmds.ls(dag=True, long=full_path)
    elif selection_flag == SelectionFlag.Selected:
        found_node_names = cmds.ls(selection=True, long=full_path)
        if not found_node_names:
            selection_warning = True
    elif selection_flag == SelectionFlag.Hierarchy:
        found_node_names = cmds.ls(selection=True, long=full_path, dag=True)
        if found_node_names:
            found_node_names.extend(
                cmds.listRelatives(
                    found_node_names, allDescendents=True, fullPath=full_path
                )
                or []
            )
        else:
            selection_warning = True
    else:
        raise ValueError(f"Invalid selection flag: {selection_flag}")

    return found_node_names, selection_warning


def component_or_object_selection_type(selection: list[str]) -> SelectionType | None:
    """
    Returns either 'object' or 'component' or 'uv' based on the first selection type.

    :param selection: The selection string to check.
    :return: The selection type.
    """

    if not selection:
        return None

    if "." not in selection[0]:
        return SelectionType.Object
    elif ".vtx" in selection[0]:
        return SelectionType.Component
    elif ".e" in selection[0]:
        return SelectionType.Component
    elif ".f" in selection[0]:
        return SelectionType.Component
    elif ".map" in selection[0]:
        return SelectionType.UV

    return None


def component_selection_type(
    selection: list[str],
) -> ComponentSelectionType | SelectionType | None:
    """
    Returns the component selection type based on the first selection type.

    :param selection: The selection string to check.
    :return: The component selection type.
    """

    if not selection:
        return None

    if "." not in selection[0]:
        return SelectionType.Object
    elif ".vtx" in selection[0]:
        return ComponentSelectionType.Vertices
    elif ".e" in selection[0]:
        return ComponentSelectionType.Edges
    elif ".f" in selection[0]:
        return ComponentSelectionType.Faces
    elif ".map" in selection[0]:
        return SelectionType.UV

    return None


def convert_selection(
    component_selection_type: ComponentSelectionType, flatten: bool = False
) -> list[str]:
    """
    Converts the current selection to the given component type.

    :param component_selection_type: The component type to convert to.
    :param flatten: Whether to flatten the selection.
    :return: The converted selection.
    """

    if component_selection_type == ComponentSelectionType.Faces:
        mel.eval("ConvertSelectionToFaces;")
    if component_selection_type == ComponentSelectionType.Vertices:
        mel.eval("ConvertSelectionToVertices;")
    if component_selection_type == ComponentSelectionType.Edges:
        mel.eval("ConvertSelectionToEdges;")
    if component_selection_type == ComponentSelectionType.UV:
        mel.eval("ConvertSelectionToUVs;")
    elif component_selection_type == ComponentSelectionType.EdgeLoop:
        mel.eval("SelectEdgeLoopSp;")
    elif component_selection_type == ComponentSelectionType.EdgeRing:
        mel.eval("SelectEdgeRingSp;")
    elif component_selection_type == ComponentSelectionType.EdgePerimeter:
        mel.eval("ConvertSelectionToEdgePerimeter;")
    elif component_selection_type == ComponentSelectionType.UVShell:
        mel.eval("ConvertSelectionToUVShell;")
    elif component_selection_type == ComponentSelectionType.UVShellBorder:
        mel.eval("ConvertSelectionToUVShellBorder;")

    return cmds.ls(selection=True, flatten=flatten) or []
