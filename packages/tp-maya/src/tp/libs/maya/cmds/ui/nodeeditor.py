from __future__ import annotations

from maya import cmds


def primary_node_editor() -> str:
    """Return the name of the primary node editor, if it exists.

    Returns:
        The name of the primary node editor; Empty string if none is found.
    """

    found_node_editor: str = ""
    all_node_editors = cmds.getPanel(scriptType="nodeEditorPanel")
    for node_editor in all_node_editors:
        node_editor_name = f"{node_editor}NodeEditorEd"
        if cmds.nodeEditor(node_editor_name, query=True, primary=True):
            found_node_editor = node_editor_name
            break

    return found_node_editor
