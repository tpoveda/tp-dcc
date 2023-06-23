from __future__ import annotations

import os
import inspect
from typing import List, Type

from tp.core import log
from tp.common import plugin
from tp.common.qt import api as qt

from tp.tools.rig.crit.builder.views import editor

logger = log.rigLogger


class EditorsManager(qt.QObject):

	MANAGER_ENV = 'CRIT_UI_EDITORS_PATHS'
	_EDITORS_CACHE = []

	editorInvoked = qt.Signal(str, str)

	def __init__(self):
		super().__init__()

		self._manager = plugin.PluginFactory(editor.EditorView, plugin_id='ID', version_id='VERSION')

		self.discover_editors()

	@staticmethod
	def editor_instances(editor_id: str) -> List[editor.EditorView]:
		"""
		Returns already opened editor instances with given ID.

		:param str editor_id: ID of the editor to retrieve.
		:return: found editor instance.
		:rtype: List[editor.EditorView]
		"""

		return [editor_instance for editor_instance in EditorsManager._EDITORS_CACHE if editor_instance.ID == editor_id]

	@staticmethod
	def editor_instance(editor_id: str) -> editor.EditorView | None:
		"""
		Returns already opened editor instance with given ID (only first opened editor with that ID will be returned).

		:param str editor_id: ID of the editor to retrieve.
		:return: found editor instance.
		:rtype: editor.EditorView or None
		"""

		found_editor = None
		for editor_instance in EditorsManager._EDITORS_CACHE:
			if editor_instance.ID == editor_id:
				found_editor = editor_instance
				break

		return found_editor

	def discover_editors(self) -> bool:
		"""
		Searches all editors view implementations located within 'CRIT_UI_EDITORS_PATHS' environment variable paths.

		:return: True if discover editor views was successful; False otherwise.
		:rtype: bool
		"""

		paths = os.environ.get(self.MANAGER_ENV, '').split(os.pathsep)
		if not paths:
			return False

		self._manager.register_paths(paths)

		return True

	def editors(self) -> List[Type]:
		"""
		Returns a list of discovered editor classes.

		:return: List[Type]
		"""

		return self._manager.plugins()

	def find_editor_by_id(self, editor_id: str) -> Type | None:
		"""
		Returns editor class with given ID.

		:param str editor_id: ID of the editor to find.
		:return: found editor class.
		:rtype: Type or None
		"""

		found_editor_class = None
		for editor_class in self.editors():
			if editor_class.ID == editor_id:
				found_editor_class = editor_class
				break

		return found_editor_class

	def find_editor_by_name(self, name: str) -> Type | None:
		"""
		Returns editor class with given name.

		:param str name: name of the editor to find.
		:return: found editor class.
		:rtype: Type or None
		"""

		found_editor_class = None
		for editor_class in self.editors():
			if editor_class.NAME == name:
				found_editor_class = editor_class
				break

		return found_editor_class

	def invoke_editor_by_id(
			self, editor_id: str, parent: qt.QMainWindow, **kwargs) -> editor.EditorView | None:
		"""
		Invokes editor with given name and docks into the given parent widget.

		:param str editor_id: ID of the editor to open.
		:param qt.QMainWindow or None parent: optional main window this editor will be docked into.
		:return: invoked editor.
		:rtype: editor.EditorView or None
		"""

		editor_class = self.find_editor_by_id(editor_id)
		if not editor_class:
			logger.warning(f'No registered editor with ID: "{editor_id}"')
			return None

		return self.invoke_editor_by_name(editor_class.NAME, parent, **kwargs)

	def invoke_editor_by_name(self, name: str, parent: qt.QMainWindow, **kwargs) -> editor.EditorView | None:
		"""
		Invokes editor with given name and docks into the given parent widget.

		:param str name: name of the editor to open.
		:param qt.QMainWindow or None parent: optional main window this editor will be docked into.
		:return: invoked editor.
		:rtype: editor.EditorView or None
		"""

		editor_class = self.find_editor_by_name(name)
		if not editor_class:
			logger.warning(f'No registered editor with name: "{name}"')
			return None

		valid_kwargs = {}
		function_signature = inspect.signature(editor_class.show)
		if function_signature:
			for kwarg_name, kwarg_value in function_signature.parameters.items():
				if kwarg_name in kwargs:
					valid_kwargs[kwarg_name] = kwargs[kwarg_name]

		editor_view = None			# type: editor.EditorView
		opened_editor_names = [editor_class.NAME for editor_class in EditorsManager._EDITORS_CACHE]
		if editor_class.IS_SINGLETON and editor_class.NAME in opened_editor_names:
			for opened_editor in EditorsManager._EDITORS_CACHE:
				if opened_editor.NAME == editor_class.NAME:
					opened_editor.show(**valid_kwargs)
					editor_view = opened_editor
					break
		if editor_view is None:
			editor_view = editor_class()
		if not editor_view:
			logger.warning(f'Was not possible to create an editor instance for "{editor_class}"')
			return None

		if editor_class.ID in [
			editor_instance.ID for editor_instance in EditorsManager._EDITORS_CACHE] and editor_class.IS_SINGLETON:
			return editor_view

		EditorsManager._EDITORS_CACHE.append(editor_view)

		parent.addDockWidget(editor_view.DEFAULT_DOCK_AREA, editor_view)

		editor_view.closed.connect(self._on_editor_closed)
		editor_view.show(**valid_kwargs)

		self.editorInvoked.emit(editor_class.ID, editor_class.NAME)

		return editor_view

	def close_all_editors(self):
		"""
		Closes all opened editors.
		"""

		for editor_instance in EditorsManager._EDITORS_CACHE:
			editor_instance.blockSignals(True)
			editor_instance.close()
		EditorsManager._EDITORS_CACHE.clear()

	def _on_editor_closed(self, editor_id):
		"""
		Internal callback function that is called each time an editdor is closed.

		:param str editor_id: ID of the closed editor.
		"""

		found_editor = None
		for editor_instance in EditorsManager._EDITORS_CACHE:
			if editor_instance.ID == editor_id:
				found_editor = editor_instance
		if found_editor is not None:
			EditorsManager._EDITORS_CACHE.remove(found_editor)
