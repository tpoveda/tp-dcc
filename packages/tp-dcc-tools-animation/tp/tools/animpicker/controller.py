from __future__ import annotations

from typing import List

from tp.core import log
from tp.common.qt import api as qt

logger = log.modelLogger


class AnimPickerController(qt.QObject):

	def __init__(self):
		super().__init__()

		self._bottom_menu_visible = True
		self._map_mode = True
		self._clipboard = []

	def create_new_map(self):
		"""
		Creates a new animation picker map.
		"""

		print('creating new animation picker map ...')

	def filter_picker_nodes(self) -> List[str]:
		"""
		Returns a list with all picker nodes within current DCC scene.

		:return: list of picker node names.
		:rtype: List[str]
		"""

		return []


class AnimPickerViewerController(qt.QObject):

	def __init__(self):
		super().__init__()

		self._top_menu_visible = True
		self._pose_global_data = []
		self._pose_nodes = None
		self._pose_channels = None
		self._block_callback = False
		self._recent_directory = ''
		self._auto_key_state = False
		self._select_guide_dialog = None
		self._callbacks = []

	def filter_picker_nodes(self) -> List[str]:
		"""
		Returns a list with all picker nodes within current DCC scene.

		:return: list of picker node names.
		:rtype: List[str]
		"""

		return []
