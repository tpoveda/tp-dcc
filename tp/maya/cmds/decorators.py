from __future__ import annotations

import logging
from functools import wraps
from typing import Callable, Any

from maya import cmds

from ...python import decorators, helpers

logger = logging.getLogger(__name__)


def restore_selection(fn: Callable):
    """
    Decorator that restores the selection after the function is called.

    :param fn: function to decorate.
    """

    @wraps(fn)
    def wrapped(*args, **kwargs):
        selection = cmds.ls(selection=True, long=True) or []
        try:
            return fn(*args, **kwargs)
        finally:
            if selection:
                cmds.select([i for i in selection if cmds.objExists(i)])

    return wrapped


class Undo(decorators.AbstractDecorator):
    """
    Overload of AbstractDecorator that defines Maya undo chunks.
    """

    __slots__ = ("_state", "_name")
    __chunk__: str | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._state = kwargs.get("state", True)
        self._name = kwargs.get("name", "").replace(" ", "_")

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.
        """

        if self.state:
            # Check if chunk is already open.
            if not helpers.is_null_or_empty(self.chunk):
                return
            # Open undo chunk.
            self.__class__.__chunk__ = self.name
            cmds.undoInfo(openChunk=True, chunkName=self.name)
        else:
            # Disable undo.
            cmds.undoInfo(stateWithoutFlush=False)

    def __call__(self, *args, **kwargs) -> Any:
        """
        Private method that is called whenever this instance is evoked.

        :return: call result.
        :rtype: Any
        """

        try:
            self.__enter__(*args, **kwargs)
            results = self.func(*args, **kwargs)
            self.__exit__(None, None, None)
            return results
        except RuntimeError as exception:
            logger.error(exception, exc_info=True)
            return None

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        """
        Private method that is called when this instance is exited using a with statement.

        :param Any exc_type: exception type.
        :param Any exc_val: exception value.
        :param Any exc_tb: exception traceback.
        """

        if self.state:
            # Check if chunk can be closed.
            if self.name != self.chunk:
                return

            # Close undo chunk
            self.__class__.__chunk__ = None
            cmds.undoInfo(closeChunk=True)
        else:
            cmds.undoInfo(stateWithoutFlush=True)

    @property
    def chunk(self) -> str | None:
        """
        Getter method that returns the current undo chunk.

        :return: undo chunk.
        :rtype: str or None
        """

        return self.__class__.__chunk__

    @property
    def state(self) -> bool:
        """
        Getter method that returns current undo state.

        :return: undo state.
        :rtype: bool
        """

        return self._state

    @property
    def name(self) -> str:
        """
        Getter method that returns the name of this undo.

        :return: undo name.
        :rtype: str
        """

        return self._name
