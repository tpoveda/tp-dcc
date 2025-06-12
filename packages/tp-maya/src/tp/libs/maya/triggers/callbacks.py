from __future__ import annotations

import contextlib
from typing import Callable
from functools import wraps

from maya.api import OpenMaya

from ..wrapper import DGNode, node_by_object
from ..om.callbacks import CallbackSelection

CURRENT_SELECTION_CALLBACK: CallbackSelection | None = None


def create_selection_callback():
    """
    Creates a new selection callback.
    """

    def _on_selection_callback(selection: list[OpenMaya.MObjectHandle]):
        """
        Internal callback function that is called when the selection changes.

        :param selection: List of MObjects that represent the current selection.
        """

        selection = [node_by_object(i.object()) for i in selection]
        if selection:
            execute_trigger_from_nodes(selection)

    global CURRENT_SELECTION_CALLBACK

    if CURRENT_SELECTION_CALLBACK is not None:
        if CURRENT_SELECTION_CALLBACK.current_callback_state:
            return
        CURRENT_SELECTION_CALLBACK.start()
        return

    CURRENT_SELECTION_CALLBACK = CallbackSelection(_on_selection_callback)
    CURRENT_SELECTION_CALLBACK.start()


def toggle_selection_callback():
    """
    Toggles the selection callback.
    """

    global CURRENT_SELECTION_CALLBACK

    if CURRENT_SELECTION_CALLBACK is None:
        create_selection_callback()
    else:
        remove_selection_callback()


def remove_selection_callback():
    """
    Removes the current selection callback.
    """

    global CURRENT_SELECTION_CALLBACK

    if CURRENT_SELECTION_CALLBACK is None:
        return

    CURRENT_SELECTION_CALLBACK.stop()
    CURRENT_SELECTION_CALLBACK = None


def execute_trigger_from_nodes(nodes: list[DGNode]):
    """
    Executes the trigger commands from the given nodes.

    :param nodes: List of nodes to execute the triggers from.
    """

    for node in nodes:
        pass


@contextlib.contextmanager
def block_selection_callback():
    """
    Context manager that blocks the Maya selection callback while the scope is active.
    """

    if CURRENT_SELECTION_CALLBACK is not None:
        current_state = CURRENT_SELECTION_CALLBACK.current_callback_state
        try:
            if current_state:
                remove_selection_callback()
            yield
        finally:
            if current_state:
                create_selection_callback()
    else:
        yield


def block_selection_callback_decorator(func: Callable) -> Callable:
    """
    Decorator function that blocks the Maya selection callback while the decorated
    function is running.

    :param func: Function to be decorated.
    """

    @wraps(func)
    def inner(*args, **kwargs):
        """
        Inner function that wraps the decorated function.

        :param args: Arguments to be passed to the decorated function.
        :param kwargs: Keyword arguments to be passed to the decorated function.
        """

        if CURRENT_SELECTION_CALLBACK is not None:
            current_state = CURRENT_SELECTION_CALLBACK.current_callback_state
            try:
                if current_state:
                    remove_selection_callback()
                return func(*args, **kwargs)
            finally:
                if current_state:
                    create_selection_callback()
        else:
            return func(*args, **kwargs)

    return inner
