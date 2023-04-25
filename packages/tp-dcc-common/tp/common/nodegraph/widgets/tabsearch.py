import re
from collections import OrderedDict

from Qt.QtCore import Qt, Signal, QRegExp, QStringListModel, QSortFilterProxyModel
from Qt.QtWidgets import QCompleter, QLineEdit, QMenu, QAction, QWidgetAction
from Qt.QtGui import QCursor

from tp.common.nodegraph.core import consts


class TabSearchCompleter(QCompleter):
	def __init__(self, nodes=None, parent=None):
		super(TabSearchCompleter, self).__init__(nodes, parent)

		self._local_completion_prefix = ''
		self._using_orig_model = False
		self._source_model = None
		self._filter_model = None

		self.setCompletionMode(self.PopupCompletion)
		self.setCaseSensitivity(Qt.CaseInsensitive)

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def splitPath(self, path):
		self._local_completion_prefix = path
		self.updateModel()

		if self._filter_model.rowCount() == 0:
			self._using_orig_model = False
			self._filter_model.setSourceModel(QStringListModel(list()))
			return list()

		return list()

	def updateModel(self):
		if not self._using_orig_model:
			self._filter_model.setSourceModel(self._source_model)
		pattern = QRegExp(self._local_completion_prefix, Qt.CaseInsensitive, QRegExp.FixedString)
		self._filter_model.setFilterRegExp(pattern)

	def setModel(self, model):
		self._source_model = model
		self._filter_model = QSortFilterProxyModel(self)
		self._filter_model.setSourceModel(self._source_model)
		super(TabSearchCompleter, self).setModel(self._filter_model)
		self._using_orig_model = True


class TabSearchLineEditWidget(QLineEdit):

	tabPressed = Signal()

	def __init__(self, parent=None):
		super(TabSearchLineEditWidget, self).__init__(parent)
		self.setAttribute(Qt.WA_MacShowFocusRect, 0)
		self.setMinimumSize(200, 22)
		text_color = self.palette().text().color().getRgb()
		selected_color = self.palette().highlight().color().getRgb()
		style_dict = {
			'QLineEdit': {
				'color': 'rgb({0},{1},{2})'.format(*text_color),
				'border': '1px solid rgb({0},{1},{2})'.format(
					*selected_color
				),
				'border-radius': '3px',
				'padding': '2px 4px',
				'margin': '2px 4px 8px 4px',
				'background': 'rgb({0},{1},{2})'.format(
					*consts.NodeGraphViewStyle.BACKGROUND_COLOR
				),
				'selection-background-color': 'rgba({0},{1},{2},200)'
					.format(*selected_color),
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
	# OVERRIDES
	# ==================================================================================================================

	def keyPressEvent(self, event):
		super(TabSearchLineEditWidget, self).keyPressEvent(event)
		if event.key() == Qt.Key_Tab:
			self.tabPressed.emit()


class TabSearchMenuWidget(QMenu):

	searchSubmitted = Signal(str)

	def __init__(self, node_dict=None):
		super(TabSearchMenuWidget, self).__init__()

		self.line_edit = TabSearchLineEditWidget()
		self.line_edit.tabPressed.connect(self._close)

		self._node_dict = node_dict or {}
		if self._node_dict:
			self._generate_items_from_node_dict()

		search_widget = QWidgetAction(self)
		search_widget.setDefaultWidget(self.line_edit)
		self.addAction(search_widget)

		text_color = self.palette().text().color().getRgb()
		selected_color = self.palette().highlight().color().getRgb()
		style_dict = {
			'QMenu': {
				'color': 'rgb({0},{1},{2})'.format(*text_color),
				'background-color': 'rgb({0},{1},{2})'.format(
					*consts.NodeGraphViewNavStyle.BACKGROUND_COLOR
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
		self._menu_stylesheet = ''
		for css_class, css in style_dict.items():
			style = '{} {{\n'.format(css_class)
			for elm_name, elm_val in css.items():
				style += '  {}:{};\n'.format(elm_name, elm_val)
			style += '}\n'
			self._menu_stylesheet += style
		self.setStyleSheet(self._menu_stylesheet)

		self._actions = dict()
		self._menus = dict()
		self._searched_actions = list()
		self._block_submit = False
		self.rebuild = False

		self._setup_signals()

	def __repr__(self):
		return '<{} at {}>'.format(self.__class__.__name__, hex(id(self)))

	# ==================================================================================================================
	# STATIC METHODS
	# ==================================================================================================================

	@staticmethod
	def _fuzzy_finder(key, collection):
		suggestions = list()
		pattern = '.*?'.join(key.lower())
		regex = re.compile(pattern)
		for item in collection:
			match = regex.search(item.lower())
			if match:
				suggestions.append((len(match.group()), match.start(), item))

		return [x for _, _, x in sorted(suggestions)]

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def keyPressEvent(self, event):
		super(TabSearchMenuWidget, self).keyPressEvent(event)
		self.line_edit.keyPressEvent(event)

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def set_nodes(self, node_dict=None):
		"""
		Set the node data that will be showed within the search widget UI.

		:param dict node_dict: nodes data.
		"""

		if not self._node_dict or self.rebuild:
			self._node_dict.clear()
			self._clear_actions()
			self._set_menu_visible(False)
			for menu in self._menus.values():
				self.removeAction(menu.menuAction())
			self._actions.clear()
			self._menus.clear()
			for name, node_types in node_dict.items():
				if len(node_types) == 1:
					self._node_dict[name] = node_types[0]
					continue
				for node_id in node_types:
					self._node_dict['{} ({})'.format(name, node_id)] = node_id
			self.build_menu_tree()
			self.rebuild = False

		self._show()

	def build_menu_tree(self):
		"""
		Generates the UI based on the node data.
		"""

		node_types = sorted(self._node_dict.values())
		node_names = sorted(self._node_dict.keys())
		menu_tree = OrderedDict()

		max_depth = 0
		for node_type in node_types:
			trees = '.'.join(node_type.split('.')[:-1]).split('::')
			for depth, menu_name in enumerate(trees):
				new_menu = None
				menu_path = '::'.join(trees[:depth + 1])
				if depth in menu_tree.keys():
					if menu_name not in menu_tree[depth].keys():
						new_menu = QMenu(menu_name)
						new_menu.keyPressEvent = self.keyPressEvent
						new_menu.setStyleSheet(self._menu_stylesheet)
						menu_tree[depth][menu_path] = new_menu
				else:
					new_menu = QMenu(menu_name)
					new_menu.setStyleSheet(self._menu_stylesheet)
					menu_tree[depth] = {menu_path: new_menu}
				if depth > 0 and new_menu:
					new_menu.parentPath = '::'.join(trees[:depth])

				max_depth = max(max_depth, depth)

		for i in range(max_depth+1):
			menus = menu_tree[i]
			for menu_path, menu in menus.items():
				self._menus[menu_path] = menu
				if i == 0:
					self.addMenu(menu)
				else:
					parent_menu = self._menus[menu.parentPath]
					parent_menu.addMenu(menu)

		for name in node_names:
			action = QAction(name, self)
			action.setText(name)
			action.triggered.connect(self._on_search_submitted)
			self._actions[name] = action
			menu_name = self._node_dict[name]
			menu_path = '.'.join(menu_name.split('.')[:-1])
			if menu_path in self._menus.keys():
				self._menus[menu_path].addAction(action)
			else:
				self.addAction(action)

	# ==================================================================================================================
	# INTERNAL
	# ==================================================================================================================

	def _setup_signals(self):
		"""
		Internal function that setup the signals for this widget.
		"""

		self.line_edit.returnPressed.connect(self._on_search_submitted)
		self.line_edit.textChanged.connect(self._on_text_changed)

	def _clear_actions(self):
		"""
		Internal function that clears all the actions from the menu.
		"""

		for action in self._searched_actions:
			self.removeAction(action)
			action.triggered.connect(self._on_search_submitted)
		del self._searched_actions[:]

	def _set_menu_visible(self, visible):
		"""
		Internal function that sets whether menu actions are visible.

		:param bool visible: True to show the actions; False to hide them.
		"""

		for menu in self._menus.values():
			menu.menuAction().setVisible(visible)

	def _close(self):
		"""
		Internal function that prepares the menu to be closed.
		"""

		self._set_menu_visible(False)
		self.setVisible(False)
		self.menuAction().setVisible(False)
		self._block_submit = True

	def _show(self):
		"""
		Internal function that prepares the menu to be showed.
		"""

		self.line_edit.setText("")
		self.line_edit.setFocus()
		self._set_menu_visible(True)
		self._block_submit = False
		self.exec_(QCursor.pos())

	# ==================================================================================================================
	# CALLBACKS
	# ==================================================================================================================

	def _on_text_changed(self, text):
		"""
		Internal callback function that is called each time the search text changes.

		:param str text: current search text.
		"""

		self._clear_actions()

		if not text:
			self._set_menu_visible(True)
			return

		self._set_menu_visible(False)

		action_names = self._fuzzy_finder(text, self._actions.keys())

		self._searched_actions = [self._actions[name] for name in action_names]
		self.addActions(self._searched_actions)

		if self._searched_actions:
			self.setActiveAction(self._searched_actions[0])

	def _on_search_submitted(self):
		"""
		Internal callback function that is called when the search is submitted.
		"""

		if not self._block_submit:
			action = self.sender()
			if type(action) is not QAction:
				if len(self._searched_actions) > 0:
					action = self._searched_actions[0]
				else:
					self._close()
					return

			text = action.text()
			node_type = self._node_dict.get(text)
			if node_type:
				self.searchSubmitted.emit(node_type)

		self._close()
