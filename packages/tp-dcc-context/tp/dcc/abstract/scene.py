from __future__ import annotations

import enum
from typing import Any

from tp.dcc.abstract import base
from tp.common.python import decorators


class AbstractScene(base.AbstractBase):
    """
    Custom class to outline behaviour for DCC scenes
    """

    __slots__ = ()
    __extensions__: enum.IntEnum | None = None

    @decorators.classproperty
    def file_extensions(cls) -> enum.IntEnum:
        """
        Getter method that returns the file extension enumerator for this scene context class.

        :return: file extension enumerator.
        :rtype: enum.IntEnum
        """

        return cls.__extensions__

    @decorators.abstractmethod
    def is_new_scene(self) -> bool:
        """
        Returns whether this is an untitled scene file.

        :return: True if scene is new; False otherwise.
        :rtype: bool
        """

        pass

    @decorators.abstractmethod
    def is_save_required(self) -> bool:
        """
        Returns whether the open scene file has changes that need to be saved.

        :return: True if scene has been modified; False otherwise.
        :rtype: bool
        """

        pass

    @decorators.abstractmethod
    def active_selection(self) -> list[Any]:
        """
        Returns current active selection.

        :return: list of active nodes.
        :rtype: list[Node]
        """

        pass

    @decorators.abstractmethod
    def set_active_selection(self, selection: list[Any], replace: bool = True):
        """
        Updates active selection.

        :param list[Node] selection: list of nodes to set as the active ones.
        :param bool replace: whether to replace selection or add to current one.
        """

        pass

    @decorators.abstractmethod
    def clear_active_selection(self):
        """
        Clears current active selection.
        """

        pass
Any