from __future__ import annotations

import contextlib
from functools import wraps
from typing import List, Callable, Any

import maya.api.OpenMaya as OpenMaya

from tp.maya.cmds import decorators
from tp.maya.api import base, callbacks
from tp.maya.libs.triggers import consts, triggernode

CURRENT_SELECTION_CALLBACK = None					# type: callbacks.CallbackSelection


def create_selection_callback():
	"""
	Creates Maya selection callback.
	"""

	def _on_selection_callback(selection: List[OpenMaya.MObjectHandle]):
		"""
		Internal function that is called when Maya selection callback is executed.

		:param List[OpenMaya.MObjectHandle] selection: selected nodes.
		"""

		selection = [base.node_by_object(handle.object()) for handle in selection]
		if selection:
			execute_trigger_from_nodes(selection)

	global CURRENT_SELECTION_CALLBACK
	if CURRENT_SELECTION_CALLBACK is not None:
		if CURRENT_SELECTION_CALLBACK.current_callback_state:
			return
		CURRENT_SELECTION_CALLBACK.start()
		return

	callback = callbacks.CallbackSelection(_on_selection_callback)
	CURRENT_SELECTION_CALLBACK = callback
	callback.start()


def toggle_selection_callback():
	"""
	Toggles the selection callback state.
	"""

	global CURRENT_SELECTION_CALLBACK
	if CURRENT_SELECTION_CALLBACK is None:
		create_selection_callback()
	else:
		remove_selection_callback()


def remove_selection_callback():
	"""
	Removes the Maya trigger selection callback.
	"""

	global CURRENT_SELECTION_CALLBACK
	if CURRENT_SELECTION_CALLBACK is None:
		return
	CURRENT_SELECTION_CALLBACK.stop()


@decorators.undo
def execute_trigger_from_nodes(nodes: List[base.DGNode]):
	"""
	Executes the trigger command for each one of the given nodes.
	
	:param List[base.DGNode] nodes: nodes to execute trigger for. 
	"""

	triggers = []
	for node in nodes:
		triggers.append(triggernode.TriggerNode.from_node(node))
	if not triggers:
		return
	for trigger in triggers:
		if trigger is None or not trigger.is_command_base_type(consts.TRIGGER_SELECTION_TYPE):
			continue
		cmd = trigger.command
		if cmd:
			cmd.execute()


@contextlib.contextmanager
def block_selection_callback():
	"""
	Custom context manager which blocks the selection callback for the scope.
	"""

	global CURRENT_SELECTION_CALLBACK
	if CURRENT_SELECTION_CALLBACK is not None:
		currently_active = CURRENT_SELECTION_CALLBACK.current_callback_state
		try:
			if currently_active:
				remove_selection_callback()
			yield
		finally:
			if currently_active:
				create_selection_callback()
	else:
		yield


def block_selection_callback_decorator(fn: Callable) -> Any:
	"""
	Custom decorator function which blocks the selection callback during function execution.

	:param Callable fn: function to execute.
	:return: function result.
	:rtype: Any
	"""

	@wraps(fn)
	def inner(*args, **kwargs):
		global CURRENT_SELECTION_CALLBACK
		if CURRENT_SELECTION_CALLBACK is not None:
			currently_active = CURRENT_SELECTION_CALLBACK.current_callback_state
			try:
				if currently_active:
					remove_selection_callback()
				return fn(*args, **kwargs)
			finally:
				if currently_active:
					create_selection_callback()
		else:
			return fn(*args, **kwargs)

	return inner
