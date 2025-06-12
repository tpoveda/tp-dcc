from __future__ import annotations

import typing

from Qt.QtWidgets import QApplication

from tp import dcc
from tp.nodegraph.core.consts import LayoutDirection, ConnectorStyle
from tp.nodegraph.views.uiconsts import (
    NODE_GRAPH_GRID_DISPLAY_NONE,
    NODE_GRAPH_GRID_DISPLAY_LINES,
    NODE_GRAPH_GRID_DISPLAY_DOTS,
)

if typing.TYPE_CHECKING:
    from ..core.graph import NodeGraph


def open_session(graph: NodeGraph):
    """
    Prompts a file open dialog to load a node graph session.

    :param graph: node graph to load session for.
    """

    current = graph.session
    file_path = graph.load_dialog(current)
    if not file_path:
        return
    graph.load_session(file_path)


def import_session(graph: NodeGraph):
    """
    Prompts a file open dialog to import a node graph session.

    :param graph: node graph to import session for.
    """

    current = graph.session
    file_path = graph.load_dialog(current)
    if not file_path:
        return
    graph.import_session(file_path)


def clear_session(graph: NodeGraph):
    """
    Clears the current node graph session.

    :param graph: node graph to clear session for.
    """

    if graph.question_dialog("Clear Current Session?", "Clear Session"):
        graph.clear_session()
        graph.viewer.message_dialog("Session cleared successfully")


def save_session(graph: NodeGraph):
    """
    Prompts a file save dialog to save the current node graph session.

    :param graph: node graph to save session for.
    """

    current = graph.session
    if current:
        graph.save_session(current)
        graph.viewer.message_dialog(f"Session saved successfully:\n{current}")
    else:
        save_session_as(graph)


def save_session_as(graph: NodeGraph):
    """
    Prompts a file save dialog to save the current node graph session as a new file.

    :param graph: node graph to save session for.
    """

    current = graph.session
    file_path = graph.save_dialog(current)
    if not file_path:
        return
    graph.save_session(file_path)


def exit_application():
    """
    Exits the application.
    """

    if not dcc.is_standalone():
        return

    QApplication.quit()


def clear_undo_history(graph: NodeGraph):
    """
    Clears the current node graph undo history.

    :param graph: node graph to clear undo history for.
    """

    if graph.question_dialog("Clear Undo History?", "Clear Undo History"):
        graph.clear_undo_stack()


def show_undo_history(graph: NodeGraph):
    """
    Shows the current node graph undo history.

    :param graph: node graph to show undo history for.
    """

    graph.undo_view.show()


def copy_nodes(graph: NodeGraph):
    """
    Copies selected nodes in the graph.

    :param graph: node graph to copy nodes from.
    """

    graph.copy_nodes()


def duplicate_nodes(graph: NodeGraph):
    """
    Duplicates selected nodes in the graph.

    :param graph: node graph to duplicate nodes from.
    """

    graph.duplicate_nodes()


def cut_nodes(graph: NodeGraph):
    """
    Cuts selected nodes in the graph.

    :param graph: node graph to cut nodes from.
    """

    graph.cut_nodes()


def paste_nodes(graph: NodeGraph):
    """
    Pastes copied nodes in the graph.

    :param graph: node graph to paste nodes into.
    """

    graph.paste_nodes()


def delete_nodes(graph: NodeGraph):
    """
    Deletes selected nodes in the graph.

    :param graph: node graph to delete nodes from.
    """

    graph.delete_nodes()


def select_all_nodes(graph: NodeGraph):
    """
    Selects all nodes in the graph.

    :param graph: node graph to select all nodes in.
    """

    graph.select_all_nodes()


def deselect_all_nodes(graph: NodeGraph):
    """
    Deselects all nodes in the graph.

    :param graph: node graph to deselect all nodes in.
    """

    graph.clear_selected_nodes()


def invert_selection(graph: NodeGraph):
    """
    Inverts the current selection in the graph.

    :param graph: node graph to invert selection for.
    """

    graph.invert_selected_nodes()


def toggle_nodes_enabled(graph: NodeGraph):
    """
    Toggles the enabled state of selected nodes in the graph.

    :param graph: node graph to toggle nodes enabled state for.
    """

    graph.disable_nodes()


def extract_nodes(graph: NodeGraph):
    """
    Extracts selected nodes from the graph.

    :param graph: node graph to extract nodes from.
    """

    graph.extract_nodes()


def clear_node_connections(graph: NodeGraph):
    """
    Clears all connections from selected nodes in the graph.

    :param graph: node graph to clear node connections from.
    """

    graph.undo_stack.beginMacro("Clear Selected Node Connections")
    for node in graph.selected_nodes():
        for port in node.inputs + node.outputs:
            port.clear_connections()
    graph.undo_stack.endMacro()


def fit_to_selection(graph: NodeGraph):
    """
    Fits the graph view to the current selection.

    :param graph: node graph to fit selection for.
    """

    graph.fit_to_selected_nodes()


def zoom_in(graph: NodeGraph):
    """
    Zooms in the graph view.

    :param graph: node graph to zoom in.
    """

    graph.set_zoom(graph.get_zoom() + 0.1)


def zoom_out(graph: NodeGraph):
    """
    Zooms out the graph view.

    :param graph: node graph to zoom out.
    """

    graph.set_zoom(graph.get_zoom() - 0.1)


def reset_zoom(graph: NodeGraph):
    """
    Resets the zoom level of the graph view.

    :param graph: node graph to reset zoom for.
    """

    graph.reset_zoom()


def background_grid_none(graph: NodeGraph):
    """
    Sets the background grid to None in the graph view.

    :param graph: node graph to set background grid for.
    """

    graph.grid_mode = NODE_GRAPH_GRID_DISPLAY_NONE


def background_grid_lines(graph: NodeGraph):
    """
    Sets the background grid to Lines in the graph view.

    :param graph: node graph to set background grid for.
    """

    graph.grid_mode = NODE_GRAPH_GRID_DISPLAY_LINES


def background_grid_dots(graph: NodeGraph):
    """
    Sets the background grid to Dots in the graph view.

    :param graph: node graph to set background grid for.
    """

    graph.grid_mode = NODE_GRAPH_GRID_DISPLAY_DOTS


def layout_horizontal_mode(graph: NodeGraph):
    """
    Sets the graph layout to Horizontal mode.

    :param graph: node graph to set layout mode for.
    """

    graph.layout_direction = LayoutDirection.Horizontal.value


def layout_vertical_mode(graph: NodeGraph):
    """
    Sets the graph layout to Vertical mode.

    :param graph: node graph to set layout mode for.
    """

    graph.layout_direction = LayoutDirection.Vertical.value


def toggle_node_search(graph: NodeGraph):
    """
    Toggles the node search widget visibility.

    :param graph: node graph to toggle node search for.
    """

    graph.toggle_node_search()


def auto_layout_upstream(graph: NodeGraph):
    """
    Automatically lays out the graph in an upstream direction.

    :param graph: node graph to auto layout for.
    """

    graph.auto_layout_nodes(down_stream=True)


def auto_layout_downstream(graph: NodeGraph):
    """
    Automatically lays out the graph in a downstream direction.

    :param graph: node graph to auto layout for.
    """

    graph.auto_layout_nodes(down_stream=False)


def expand_group_node(graph: NodeGraph):
    """
    Expands selected group nodes in the graph.

    :param graph: node graph to expand group nodes for.
    """

    selected_nodes = graph.selected_nodes()
    if not selected_nodes:
        graph.message_dialog('Please select a "GroupNode" to expand.')
        return
    # noinspection PyTypeChecker
    graph.expand_group_node(selected_nodes[0])


def connector_straight_line(graph: NodeGraph):
    """
    Sets the connector lines to straight in the graph view.

    :param graph: node graph to set connector lines for.
    """

    graph.connector_style = ConnectorStyle.Straight.value


def connector_curved_line(graph: NodeGraph):
    """
    Sets the connector lines to curved in the graph view.

    :param graph: node graph to set connector lines for.
    """

    graph.connector_style = ConnectorStyle.Curved.value


def connector_angled_line(graph: NodeGraph):
    """
    Sets the connector lines to angled in the graph view.

    :param graph: node graph to set connector lines for.
    """

    graph.connector_style = ConnectorStyle.Angle.value
