from __future__ import annotations

from typing import Any
from functools import partial

import maya.api.OpenMaya as OpenMaya

from tp.common.python import decorators


def locksmith(*args, **kwargs) -> callable:
    """
    Returns a locksmith wrapper for the given function.

    :raises TypeError: if not enough arguments are given.
    """

    num_args = len(args)
    if num_args == 0:
        return partial(locksmith, **kwargs)
    elif num_args == 1:
        return Locksmith(*args, **kwargs)
    else:
        raise TypeError(f'locksmith() expects at most 1 argument ({num_args} given)!')


class Locksmith(decorators.AbstractDecorator):
    """
    Overload of AbstractDecorator that toggles the lock state on plugs when mutating values.
    """

    __slots__ = ('_plug', '_value', '_is_locked', '_force')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._plug: OpenMaya.MPlug | None = None
        self._value: Any = None
        self._is_locked = False
        self._force = False

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.
        """

        num_args = len(args)
        if num_args != 2:
            raise TypeError(f'__enter__() expects 2 arguments ({num_args} given)!')

        self._plug, self._value = args
        self._is_locked = bool(self.plug.isLocked)
        self._force = kwargs.get('force', False)

        if self._force:
            self.plug.isLocked = False
        elif self.plug.isLocked and not self.force:
            raise TypeError('__enter__() cannot mutate locked plug!')

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        """
        Private method that is called when this instance is exited using a with statement.

        :param Any exc_type: exception type.
        :param Any exc_val: exception value.
        :param Any exc_tb: exception traceback.
        """

        if self.force and self.is_locked:
            self.plug.isLocked = True

    @property
    def plug(self) -> OpenMaya.MPlug:
        """
        Getter method that returns the current plug.

        :return: current plug.
        :rtype: OpenMaya.MPlug
        """

        return self._plug

    @property
    def value(self) -> Any:
        """
        Getter method that returns the current value.

        :return: current value.
        :rtype: Any
        """

        return self._value

    @property
    def force(self) -> bool:
        """
        Getter method that returns the force flag.

        :return: force flag.
        :rtype: bool
        """

        return self._force

    @property
    def is_locked(self) -> bool:
        """
        Getter method that returns the locked state.

        :return: locked state.
        :rtype: bool
        """

        return self._is_locked
