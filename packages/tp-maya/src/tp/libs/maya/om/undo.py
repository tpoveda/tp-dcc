from __future__ import annotations

from typing import Callable

from ..plugins import apiundo
from ..cmds import decorators


def undo(*args, **kwargs):
    """
    Returns an undo wrapper the given function.

    :raises TypeError: if more than one argument is given.
    """

    return decorators.Undo.get(*args, **kwargs)


def commit(do_it: Callable, undo_it: Callable):
    """
    Passes the supplied functions to the py-undo bridge.

    :param Callable do_it: function to call when redo is executed.
    :param Callable undo_it: function to call when undo is executed.
    """

    apiundo.commit(undo=undo_it, redo=do_it)
