from __future__ import annotations

import logging
from typing import Callable

from maya.api import OpenMaya

from . import scene

logger = logging.getLogger(__name__)


def remove_callbacks_from_node(node: OpenMaya.MObject) -> int:
    """
    Removes all callbacks from the given node.

    :param node: Maya node to remove callbacks from.
    :return: Number of callbacks removed from the node.
    """

    node_callbacks = OpenMaya.MMessage.nodeCallbacks(node)
    count = len(node_callbacks)
    OpenMaya.MMessage.removeCallbacks(node_callbacks)
    return count


def remove_callbacks_from_nodes(nodes: list[OpenMaya.MObject]) -> int:
    """
    Removes all callbacks from the given nodes.

    :param nodes: Maya nodes to remove callbacks from.
    :return: Number of callbacks removed from the nodes.
    """

    count = 0
    for node in nodes:
        count += remove_callbacks_from_node(node)
    return count


class MCallbackIdWrapper:
    """
    Wrapper class that handles the cleanup of Maya callback IDs from registered MMessages.
    """

    def __init__(self, callback_id: int):
        super().__init__()

        self._callback_id = callback_id

    def __repr__(self) -> str:
        """
        Overrides base class __repr__ method to return the class name and the callback
        ID.
        """

        return f"{self.__class__.__name__}({self._callback_id})"

    def __del__(self):
        """
        Overrides base class __del__ method to remove the registered callback ID from
        Maya.
        """

        OpenMaya.MMessage.removeCallback(self._callback_id)


class CallbackSelection:
    """
    Class that handles the management of a single selection callback that can be stored
    within UIs.
    """

    def __init__(self, func: Callable, *args, **kwargs):
        """
        Initializes the callback selection instance.

        :param func: Function to be called when the selection callback is triggered.
        :param args: arguments to be passed to the callback function.
        :param kwargs: keyword arguments to be passed to the callback function.
        """

        self._callable = func
        self._arguments = args
        self._keyword_arguments = kwargs
        self._selection_change_callback: MCallbackIdWrapper | None = None
        self._current_selection: list[OpenMaya.MObjectHandle] = []
        self._current_callback_state: bool = False

    @property
    def current_callback_state(self) -> bool:
        """
        Getter that returns the current state of the callback.

        :return: True if the callback is active, False otherwise.
        """

        return self._current_callback_state

    def __del__(self):
        """
        Overrides base class __del__ method to remove the selection callback from Maya.
        """

        self.stop()

    def start(self):
        """
        Creates and stores the selection callback on this instance.
        """

        if self._current_callback_state:
            return

        if self._callable is None:
            logger.error("Cannot start selection callback without a callable function.")
            return

        self._selection_change_callback = MCallbackIdWrapper(
            OpenMaya.MEventMessage.addEventCallback(
                "SelectionChanged", self._on_selection_callback_changed
            )
        )

    def stop(self):
        """
        Cleans up the instance by removing the selection callback.
        """

        if not self._current_callback_state:
            return

        try:
            self._selection_change_callback = None
            self._current_callback_state = False
            self._current_selection.clear()
        except Exception as err:
            logger.exception(f"Failed to stop selection callback: {err}", exc_info=True)

    def _on_selection_callback_changed(self, *args, **kwargs):
        """
        Internal callback function that is triggered when the selection changes in Maya.
        """

        # We need to convert MObjects to MObjectHandles to make sure garbage collector
        # does not delete them. It's the client responsibility to ensure objects are
        # still valid.
        selection = scene.iterate_selected_nodes(OpenMaya.MFn.kTransform)
        self._current_selection = map(OpenMaya.MObjectHandle, selection)
        keywords = {"selection": self._current_selection}
        keywords.update(self._keyword_arguments)
        self._callable(*self._arguments, **keywords)
