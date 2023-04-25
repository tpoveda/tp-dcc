from distutils.version import LooseVersion

from Qt import QtCore
from Qt.QtGui import QKeySequence

from tp.common.nodegraph.core import exceptions
from tp.common.nodegraph.widgets import actions


class NodeGraphCommand(object):
	"""
	Node graph menu command
	"""

	def __init__(self, graph, qaction):
		super(NodeGraphCommand, self).__init__()

		self._graph = graph
		self._qaction = qaction

	# ==================================================================================================================
	# PROPERTIES
	# ==================================================================================================================

	@property
	def qaction(self):
		"""
		Returns the wrapped qction.

		:return: QAction instance.
		:rtype: Qt.QtWidgets.QAction
		"""

		return self._qaction

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def name(self):
		"""
		Returns the name ofr the menu command.

		:return: command name.
		:rtype: str
		"""

		return self._qaction.text()

	def set_shortcut(self, shortcut=None):
		"""
		Sets the shortcut key combination for the menu command.

		:param str shortcut: shortcut key.
		"""

		shortcut = shortcut or QKeySequence()
		self._qaction.setShortcut(shortcut)

	def run(self):
		"""
		Runs the menu command.
		"""

		self._qaction.trigger()


class NodeGraphMenu(object):
	"""
	Base class that implements the context menu triggered from the node graph.
	"""

	def __init__(self, graph, qmenu):
		super(NodeGraphMenu, self).__init__()

		self._graph = graph
		self._qmenu = qmenu

	def __repr__(self):
		return '<{}("{}") object at {}>'.format(self.__class__.__name__, self.name(), hex(id(self)))

	# ==================================================================================================================
	# PROPERTIES
	# ==================================================================================================================

	@property
	def qmenu(self):
		return self._qmenu

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def name(self):
		"""
		Returns the name for the menu.

		:return: menu name.
		:rtype: str
		"""

		return self.qmenu.title()

	def menu(self, name):
		"""
		Returns the child menu by name.

		:param str name: child menu name to get.
		:return: found child menu.
		:rtype: NodeGraphMenu or None
		"""

		menu = self.qmenu.menu(name)
		if not menu:
			return None

		return NodeGraphMenu(self._graph, menu)

	def command(self, name):
		"""
		Returns the child menu command by name.

		:param str name: name of the command.
		:return: context menu command found.
		:rtype: MenuCommand or None
		"""

		for action in self.qmenu.actions():
			if not action.menu() and action.text() == name:
				return NodeGraphCommand(self._graph, action)

		return None

	def all_commands(self):
		"""
		Returns all child and sub child commands from the current context menu.

		:return: list of all commands.
		:rtype: list[MenuCommand]
		"""

		def _get_actions(menu):
			actions = list()
			for action in menu.actions():
				if not action.menu():
					if not action.isSeparator():
						actions.append(action)
				else:
					actions += _get_actions(action.menu())
			return actions

		child_actions = _get_actions(self._qmenu)
		return [NodeGraphCommand(self._graph, qaction) for qaction in child_actions]

	def add_menu(self, name):
		"""
		Adds a child menu to the current menu.

		:param str name: name of the menu to add.
		:return: newly created menu instance.
		:rtype: NodeGraphMenu
		"""

		new_menu = actions.BaseMenu(name, self.qmenu)
		self.qmenu.addMenu(new_menu)
		return NodeGraphMenu(self._graph, new_menu)

	def add_command(self, name, fn=None, shortcut=None):
		"""
		Adds a command to the menu.

		:param str name: command name.
		:param callable or None fn: optional command function.
		:param str or None shortcut: optional shortcut key.
		:return: newly created command instance.
		:rtype: NodeGraphCommand
		"""

		action = actions.GraphAction(name, self._graph.viewer())
		action.graph = self._graph
		if LooseVersion(QtCore.qVersion()) >= LooseVersion('5.10'):
			action.setShortcutVisibleInContextMenu(True)
		if shortcut:
			action.setShortcut(shortcut)
		if fn:
			action.executed.connect(fn)
		qaction = self.qmenu.addAction(action)
		return NodeGraphCommand(self._graph, qaction)

	def add_separator(self):
		"""
		Adds a separator to the menu.
		"""

		self.qmenu.addSeparator()


class NodesMenu(NodeGraphMenu):
	"""
	Context menu triggered from a node.
	"""

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def add_command(self, name, fn=None, node_type=None, node_class=None):
		"""
		Adds a command to the menu.

		:param str name: command name.
		:param callable or None fn: optional command function.
		:param str or None node_type: optional node type for the command.
		:param type or None node_class: optional node class for the command.
		:return: newly created command instance.
		:rtype: NodeGraphCommand
		"""

		if not node_type and not node_class:
			raise exceptions.NodeMenuError('Node type or Node class not specified!')

		if node_class:
			node_type = node_class.__name__

		node_menu = self.qmenu.get_menu(node_type)
		if not node_menu:
			node_menu = actions.BaseMenu(node_type, self.qmenu)

			if node_class:
				node_menu.node_class = node_class
				node_menu.graph = self._graph

			self.qmenu.addMenu(node_menu)

		if not self.qmenu.isEnabled():
			self.qmenu.setDisabled(False)

		action = actions.NodeAction(name, self._graph.viewer())
		action.graph = self._graph
		if LooseVersion(QtCore.qVersion()) >= LooseVersion('5.10'):
			action.setShortcutVisibleInContextMenu(True)
		if fn:
			action.executed.connect(fn)

		if node_class:
			node_menus = self.qmenu.get_menus(node_class)
			if node_menu in node_menus:
				node_menus.remove(node_menu)
			for menu in node_menus:
				menu.addAction(action)

		return NodeGraphCommand(self._graph, node_menu.addAction(action))
