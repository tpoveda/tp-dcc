from __future__ import annotations

import os
import typing
from typing import List

from tp.core import log
from tp.common.python import decorators, strings, path
from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
	from tp.common.python.path import DirectoryPath
	from tp.preferences.assets import BrowserPreference
	from tp.preferences.preference import PreferenceInterface
	from tp.tools.toolbox.widgets.toolui import ToolUiWidget
	from tp.tools.scenesbrowser.widgets.thumbsbrowser import ThumbsBrowser, SuffixFilterModel, FileModel

logger = log.tpLogger


class ScenesBrowserController:
	def __init__(self, tool_ui_widget: ToolUiWidget):
		super().__init__()

		self._tool_ui_widget = tool_ui_widget
		self._scene_prefs = None
		self._directory = None								# type: str
		self._selected_item = None							# type: FileModel.FileItem

	@property
	def selected_item(self) -> FileModel.FileItem:
		return self._selected_item

	@selected_item.setter
	def selected_item(self, value: FileModel.FileItem):
		self._selected_item = value

	def file_path(self, message: bool = True):
		"""
		Returns the file path of the currently selected thumbnail.

		:param bool message: whether to log messages.
		:return: current selected thumbnail path.
		:rtype: str
		"""

		try:
			return self._selected_item.file_path
		except AttributeError:
			if message:
				logger.warning('No thumbnail is selected in the browser. Please select at least one item.')

		return ''

	def browser_model(
			self, view: ThumbsBrowser, directories: List[DirectoryPath] | None = None,
			uniform_icons: bool = False, browser_preferences: BrowserPreference | None = None) -> SuffixFilterModel:
		return SuffixFilterModel(
			view, extensions=[], directories=directories, uniform_icons=uniform_icons,
			browser_preferences=browser_preferences)

	def scene_name_input(self) -> str:
		"""
		Shows an input dialog that allow users to type a new scene name.

		:return: scene name.
		:rtype: str
		"""

		return qt.input_dialog(title='Scene Name', message='New Scene Name: ', parent=self._tool_ui_widget.window())

	@decorators.abstractmethod
	def scene_prefs(self) -> PreferenceInterface | None:
		return None

	@decorators.abstractmethod
	def load_scene(self):
		"""
		Loads active file path.
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def save_scene(self, directory: str, file_type: str = ''):
		"""
		Saves scene within given directory and with the given file type.

		:param str directory: directory where current active scene will be saved into.
		:param str file_type: file type to save with.
		"""

		raise NotImplementedError

	def _prepare_folder(self, directory: str, name: str):
		"""
		Internal function that creates a folder with given name within given directory.

		:param str directory: directory where file with given name should exists. If not, it will be created.
		:param str name: folder name.
		:return: created folder name.
		:rtype: str
		"""

		folder_name = strings.file_safe_name(name, space_to='_')
		folder_path = path.join_path(directory, folder_name)
		if not os.path.exists(folder_path):
			os.mkdir(folder_path)

		return folder_name
