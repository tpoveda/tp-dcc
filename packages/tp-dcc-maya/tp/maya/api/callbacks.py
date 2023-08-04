from __future__ import annotations

from typing import Tuple, Dict, Callable

import maya.api.OpenMaya as OpenMaya

from tp.core import log
from tp.maya.om import scene

logger = log.tpLogger


class CallbackIdWrapper:
	"""
	Wrapper class to handle the cleanup of MCallbackIds from registered MMessages
	"""

	def __init__(self, callback_id: str):

		self._callback_id = callback_id

	def __del__(self):
		OpenMaya.MMessage.removeCallback(self._callback_id)

	def __repr__(self):
		return f'CallbackIdWrapper({self._callback_id})'


class CallbackSelection:
	"""
	Class that handles the management of a single selection callback which can be stored within a GUI.
	"""

	def __init__(self, fn: Callable, *args: Tuple, **kwargs: Dict):

		self._selection_change_callback = None
		self._current_selection = []
		self._current_callback_state = False
		self._callable = fn
		self._arguments = args
		self._keyword_arguments = kwargs

	def __del__(self):
		self.stop()

	@property
	def current_callback_state(self) -> bool:
		return self._current_callback_state

	def start(self):
		"""
		Creates and stores the selection callback within this instance.
		"""

		if self._current_callback_state:
			return
		if self._callable is None:
			logger.error('Callable must be supplied!')
			return

		self._selection_change_callback = CallbackIdWrapper(
			OpenMaya.MEventMessage.addEventCallback('SelectionChanged', self._on_selection_changed))

		self._current_callback_state = True

	def stop(self):
		"""
		Cleans up the instance by removing the Maya API callback.
		"""

		if not self._current_callback_state:
			return

		try:
			self._selection_change_callback = None
			self._current_callback_state = False
			self._current_selection = []
		except Exception:
			logger.error('Unknown error occurred during callback cleanup', exc_info=True)

	def _on_selection_changed(self, *args, **kwargs):
		"""
		Internal callback function that is called each time user selection changes within Maya.
		"""

		selection = scene.iterate_selected_nodes(OpenMaya.MFn.kTransform)
		self._current_selection = map(OpenMaya.MObjectHandle, selection)
		keywords = {'selection': self._current_selection}
		keywords.update(self._keyword_arguments)
		self._callable(*self._arguments, **keywords)
