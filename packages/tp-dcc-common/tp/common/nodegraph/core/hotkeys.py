NODES_PALETTE = None
NODES_TREE = None
PROPERTIES_EDITOR = None


def open_session(graph):
	"""
	Prompts a file open dialog to load a session.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	current = graph.current_session()
	file_path = graph.load_dialog(current)
	if file_path:
		graph.load_session(file_path)


def import_session(graph):
	"""
	Prompts a file open to import a session into current one.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	current = graph.current_session()
	file_path = graph.load_dialog(current)
	if file_path:
		graph.import_session(file_path)


def save_session(graph):
	"""
	Prompts a file save dialog to serialize a session.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	current = graph.current_session()
	if current:
		graph.save_session(current)
		graph.message_dialog('Session layout saved:\n{}'.format(current), 'Session Saved')
	else:
		save_session_as(graph)


def save_session_as(graph):
	"""
	Prompts a file save dialog to serialize a session.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	current = graph.current_session()
	file_path = graph.save_dialog(current)
	if file_path:
		graph.save_session(file_path)


def new_session(graph):
	"""
	Prompts a warning dialog to create a new node graph session.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	if graph.question_dialog('Clear Current Session?', 'Clear Session'):
		graph.clear_session()


def copy_nodes(graph):
	"""
	Copy selected graph nodes to the clipboard.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.copy_nodes()


def cut_nodes(graph):
	"""
	Cut selected graph nodes to the clipboard.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.cut_nodes()


def paste_nodes(graph):
	"""
	Pastes nodes copied from the clipboard in the node graph.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.paste_nodes()


def delete_nodes(graph):
	"""
	Deletes selected nodes in node graph.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.delete_nodes(graph.selected_nodes())


def select_all_nodes(graph):
	"""
	Select all node graph nodes.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.select_all_nodes()


def clear_node_selection(graph):
	"""
	Clears node graph selection.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.clear_selection()


def disable_nodes(graph):
	"""
	Toggle disable on selected nodes.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.disable_nodes(graph.selected_nodes())


def duplicate_nodes(graph):
	"""
	Duplicates selected nodes.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.duplicate_nodes(graph.selected_nodes())


def fit_to_selection(graph):
	"""
	Sets the zoom level to fit the selected nodes.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.fit_to_selection()


def zoom_in(graph):
	"""
	Sets the node graph to zoom in by 0.1.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.set_zoom(graph.get_zoom() + 0.1)


def zoom_out(graph):
	"""
	Sets the node graph to zoom out by 0.1.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.set_zoom(graph.get_zoom() - 0.1)


def reset_zoom(graph):
	"""
	Resets zoom level.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.reset_zoom()


def layout_horizontal_mode(graph):
	"""
	Sets node graph layout direction to horizontal.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.set_layout_direction(0)


def layout_vertical_mode(graph):
	"""
	Sets node graph layout direction to vertical.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.set_layout_direction(1)


def bg_grid_none(graph):
	"""
	Turns off background node graph grid pattern.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	from tp.common.nodegraph.core import consts
	graph.set_grid_mode(consts.NodeGraphViewStyle.GRID_DISPLAY_NONE)


def bg_grid_lines(graph):
	"""
	Sets background node graph with grid dots.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	from tp.common.nodegraph.core import consts
	graph.set_grid_mode(consts.NodeGraphViewStyle.GRID_DISPLAY_LINES)


def bg_grid_dots(graph):
	"""
	Sets background node graph with grid dots.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	from tp.common.nodegraph.core import consts
	graph.set_grid_mode(consts.NodeGraphViewStyle.GRID_DISPLAY_DOTS)


def clear_undo(graph):
	"""
	Clears node graph undo stack.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	viewer = graph.viewer()
	if graph.question_dialog('Clear Undo History', 'Clear all undo history, Are you sure?'):
		graph.clear_undo_stack()


def show_undo_view(graph):
	"""
	Shows the node graph undo list widget.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.undo_view.show()


def toggle_node_search(graph):
	"""
	Shows/Hide the node search widget for the given graph.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	graph.toggle_node_search()


def show_nodes_palette(graph):
	"""
	Shows node palette.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	from tp.common.nodegraph.editors import nodespalette

	global NODES_PALETTE

	if NODES_PALETTE:
		NODES_PALETTE.close()

	NODES_PALETTE = nodespalette.NodesPalette(graph)
	NODES_PALETTE.show()


def show_nodes_tree(graph):
	"""
	Shows node tree.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	from tp.common.nodegraph.editors import nodestree

	global NODES_TREE

	if NODES_TREE:
		NODES_TREE.close()

	NODES_TREE = nodestree.NodesTreeWidget(graph)
	NODES_TREE.show()


def show_properties_editor(graph):
	"""
	Shows properties editor.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	from tp.common.nodegraph.editors import propertieseditor

	global PROPERTIES_EDITOR

	if PROPERTIES_EDITOR:
		PROPERTIES_EDITOR.close()

	PROPERTIES_EDITOR = propertieseditor.PropertiesEditorWidget(graph)
	PROPERTIES_EDITOR.show()


def layout_graph_up(graph):
	"""
	Auto layout nodes up stream.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	nodes = graph.selected_nodes() or graph.all_nodes()
	graph.auto_layout_nodes(nodes=nodes, down_stream=False)


def layout_graph_down(graph):
	"""
	Auto layout nodes down stream.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	nodes = graph.selected_nodes() or graph.all_nodes()
	graph.auto_layout_nodes(nodes=nodes, down_stream=True)


def expand_group_node(graph):
	"""
	Expands selected group node.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	selected_nodes = graph.selected_nodes()
	if not selected_nodes:
		graph.message_dialog('Please selected a GroupNode to expand.')
		return
	graph.expand_group_node(selected_nodes[0])


def curved_connectors(graph):
	"""
	Set node graph connectors layout as curved.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	from tp.common.nodegraph.core import consts
	graph.set_connector_style(consts.ConnectorLayoutStyles.CURVED)


def straight_connectors(graph):
	"""
	Set node graph connectors layout as straight.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	from tp.common.nodegraph.core import consts
	graph.set_connector_style(consts.ConnectorLayoutStyles.STRAIGHT)


def angle_connectors(graph):
	"""
	Set node graph connectors layout as angle.

	:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
	"""

	from tp.common.nodegraph.core import consts
	graph.set_connector_style(consts.ConnectorLayoutStyles.ANGLE)
