from __future__ import annotations

import abc
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

    @abc.abstractmethod
    def is_new_scene(self) -> bool:
        """
        Returns whether this is an untitled scene file.

        :return: True if scene is new; False otherwise.
        :rtype: bool
        """

        pass

    @abc.abstractmethod
    def is_save_required(self) -> bool:
        """
        Returns whether the open scene file has changes that need to be saved.

        :return: True if scene has been modified; False otherwise.
        :rtype: bool
        """

        pass

    @abc.abstractmethod
    def new(self):
        """
        Opens a new scene file.
        """

        pass

    @abc.abstractmethod
    def save(self):
        """
        Saves any changes to the current scene file.
        """

        pass

    @abc.abstractmethod
    def save_as(self, file_path: str):
        """
        Saves the current scene to given file path.

        :param str file_path: file path where we want to store scene.
        """

        pass

    @abc.abstractmethod
    def open(self, file_path: str) -> bool:
        """
        Opens the given scene file.

        :param str file_path: absolute file path pointing to a valid scene.
        :return: True if the scene was opened successfully; False otherwise.
        :rtype: bool
        """

        pass

    @abc.abstractmethod
    def active_selection(self) -> list[Any]:
        """
        Returns current active selection.

        :return: list of active nodes.
        :rtype: list[Any]
        """

        pass

    @abc.abstractmethod
    def set_active_selection(self, selection: list[Any], replace: bool = True):
        """
        Updates active selection.

        :param list[Any] selection: list of nodes to set as the active ones.
        :param bool replace: whether to replace selection or add to current one.
        """

        pass

    @abc.abstractmethod
    def clear_active_selection(self):
        """
        Clears current active selection.
        """

        pass
