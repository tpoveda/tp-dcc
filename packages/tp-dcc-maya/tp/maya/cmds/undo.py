from __future__ import annotations

from functools import partial

from tp.core import log
from tp.maya.cmds import decorators

logger = log.tpLogger


def undo(*args, **kwargs):
    """
    Returns an undo wrapper the given function.

    :raises TypeError: if more than one argument is given.
    """

    num_args = len(args)
    if num_args == 0:
        return partial(undo, **kwargs)
    elif num_args == 1:
        return decorators.Undo(*args, **kwargs)
    else:
        raise TypeError(f'undo() expects at most 1 argument ({num_args} given)!')
