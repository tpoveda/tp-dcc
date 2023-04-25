from Qt.QtCore import Signal
from Qt.QtWidgets import QMenu, QAction

from tp.common.nodegraph.core import consts


class BaseMenu(QMenu):
	def __init__(self, *args, **kwargs):
		super(BaseMenu, self).__init__(*args, **kwargs)

		self._node_class = None
		self._graph = None

		text_color = self.palette().text().color().getRgb()
		selected_color = self.palette().highlight().color().getRgb()
		style_dict = {
			'QMenu': {
				'color': 'rgb({0},{1},{2})'.format(*text_color),
				'background-color': 'rgb({0},{1},{2})'.format(
					*consts.NodeGraphViewStyle.BACKGROUND_COLOR
				),
				'border': '1px solid rgba({0},{1},{2},30)'.format(*text_color),
				'border-radius': '3px',
			},
			'QMenu::item': {
				'padding': '5px 18px 2px',
				'background-color': 'transparent',
			},
			'QMenu::item:selected': {
				'color': 'rgb({0},{1},{2})'.format(*text_color),
				'background-color': 'rgba({0},{1},{2},200)'
					.format(*selected_color),
			},
			'QMenu::separator': {
				'height': '1px',
				'background': 'rgba({0},{1},{2}, 50)'.format(*text_color),
				'margin': '4px 8px',
			}
		}
		stylesheet = ''
		for css_class, css in style_dict.items():
			style = '{} {{\n'.format(css_class)
			for elm_name, elm_val in css.items():
				style += '  {}:{};\n'.format(elm_name, elm_val)
			style += '}\n'
			stylesheet += style
		self.setStyleSheet(stylesheet)

	# ==================================================================================================================
	# PROPERTIES
	# ==================================================================================================================

	@property
	def node_class(self):
		return self._node_class

	@node_class.setter
	def node_class(self, value):
		self._node_class = value

	@property
	def graph(self):
		return self._graph

	@graph.setter
	def graph(self, value):
		self._graph = value

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def get_menu(self, name, node_id=None):
		"""
		Returns the menu associated with given node ID.

		:param str name: name of the menu.
		:param str node_id: optional node ID.
		:return: found menu.
		:rtype: BaseMenu
		"""

		for action in self.actions():
			menu = action.menu()
			if not menu:
				continue
			if menu.title() == name:
				return menu
			if node_id and menu.node_class:
				node = menu.graph.node_by_id(node_id)
				if isinstance(node, menu.node_class):
					return menu

	def get_menus(self, node_class):
		"""
		Returns all the menus associated to a specific node class.

		:param type node_class: node class.
		:return: list of menus.
		:rtype: list[BaseMenu]
		"""

		menus = list()
		for action in self.actions():
			menu = action.menu()
			if menu.node_class:
				if issubclass(menu.node_class, node_class):
					menus.append(menu)

		return menus


class GraphAction(QAction):

	executed = Signal(object)

	def __init__(self, *args, **kwargs):
		super(GraphAction, self).__init__(*args, **kwargs)
		self.graph = None
		self.triggered.connect(self._on_triggered)

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def get_action(self, name):
		for action in self.qmenu.actions():
			if not action.menu() and action.text() == name:
				return action

	# ==================================================================================================================
	# CALLBACKS
	# ==================================================================================================================

	def _on_triggered(self):
		self.executed.emit(self.graph)


class NodeAction(GraphAction):

	executed = Signal(object, object)

	def __init__(self, *args, **kwargs):
		super(NodeAction, self).__init__(*args, **kwargs)
		self.node_id = None

	# ==================================================================================================================
	# CALLBACKS
	# ==================================================================================================================

	def _on_triggered(self):
		node = self.graph.node_by_id(self.node_id)
		self.executed.emit(self.graph, node)
