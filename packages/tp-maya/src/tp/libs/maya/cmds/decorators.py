from __future__ import annotations

from typing import Callable, Any
from functools import wraps, partial

from maya import cmds
from loguru import logger

from tp.libs.python import decorators, helpers


def restore_selection(fn: Callable) -> Callable:
    """Decorator that restores the selection after the function is called.

    Args:
        fn: Function to decorate.

    Returns:
        Wrapped function that restores selection.
    """

    @wraps(fn)
    def wrapped(*args, **kwargs):
        selection = cmds.ls(selection=True, long=True) or []
        try:
            return fn(*args, **kwargs)
        finally:
            if selection:
                # noinspection PyTypeChecker
                cmds.select([i for i in selection if cmds.objExists(i)])

    return wrapped


def undo(fn: Callable) -> Callable:
    """Decorator that wraps the function in an undo chunk.

    Args:
        fn: Function to decorate.

    Returns:
        Wrapped function that opens an undo chunk before execution and
            closes it after.
    """

    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            cmds.undoInfo(openChunk=True, chunkName=fn.__name__)
            return fn(*args, **kwargs)
        finally:
            cmds.undoInfo(closeChunk=True)

    return wrapped


class Undo(decorators.AbstractDecorator):
    """Overload of AbstractDecorator that defines Maya undo chunks."""

    __slots__ = ("_state", "_name")
    __chunk__: str | None = None

    @staticmethod
    def get(*args, **kwargs):
        """Returns an undo wrapper the given function.

        :raises TypeError: if more than one argument is given.
        """

        num_args = len(args)
        if num_args == 0:
            return partial(Undo.get, **kwargs)
        elif num_args == 1:
            return Undo(*args, **kwargs)
        else:
            raise TypeError(f"undo() expects at most 1 argument ({num_args} given)!")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._state = kwargs.get("state", True)
        self._name = kwargs.get("name", "").replace(" ", "_")

    def __enter__(self, *args, **kwargs):
        """Private method that is called when this instance is entered
        using a with statement.

        Args:
            *args: additional arguments.
            **kwargs: additional keyword arguments.
        """

        if self.state:
            # Check if the chunk is already open.
            if not helpers.is_null_or_empty(self.chunk):
                return
            # Open undo chunk.
            self.__class__.__chunk__ = self.name
            cmds.undoInfo(openChunk=True, chunkName=self.name)
        else:
            # Disable undo.
            cmds.undoInfo(stateWithoutFlush=False)

    def __call__(self, *args, **kwargs) -> Any:
        """Private method that is called whenever this instance is evoked.

        Args:
            *args: additional arguments.
            **kwargs: additional keyword arguments.

        Returns:
            Any: results of the function call or None if an error occurs.
        """

        try:
            self.__enter__(*args, **kwargs)
            results = self.func(*args, **kwargs)
            self.__exit__(None, None, None)
            return results
        except RuntimeError as exception:
            # noinspection PyTypeChecker
            logger.error(exception, exc_info=True)
            return None

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        """Private method that is called when this instance is exited using
        a with statement.

        Args:
            exc_type: exception type.
            exc_val: exception value.
            exc_tb: exception traceback.
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
        """The current undo chunk."""

        return self.__class__.__chunk__

    @property
    def state(self) -> bool:
        """The current undo state."""

        return self._state

    @property
    def name(self) -> str:
        """The name of this undo."""

        return self._name
