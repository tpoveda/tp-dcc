from __future__ import annotations


from abc import abstractmethod
from typing import Iterator, Any

from .base import AFnBase
from ...python import paths


class AFnScene(AFnBase):
    """
    Overloads `AFnBase` exposing functions to handle DCC scenes.
    """

    @abstractmethod
    def is_new_scene(self) -> bool:
        """
        Returns whether the current scene is new or not.

        :return: Whether the current scene is new or not.
        """

        pass

    @abstractmethod
    def is_save_required(self) -> bool:
        """
        Returns whether the current scene requires saving or not.

        :return: Whether the current scene requires saving or not.
        """

        pass

    @abstractmethod
    def new(self):
        """
        Creates a new scene.
        """

        pass

    @abstractmethod
    def save(self):
        """
        Saves any changes to the current scene file.
        """

        pass

    @abstractmethod
    def save_as(self, file_path: str):
        """
        Saves the current scene to the given file path.

        :param file_path: File path to save the current scene to.
        """

        pass

    @abstractmethod
    def iterate_nodes(self) -> Iterator[Any]:
        """
        Generator function that iterates over all nodes in the scene.

        :return: Iterator to iterate over all nodes in the scene.
        """

        pass

    @abstractmethod
    def active_selection(self) -> list[Any]:
        """
        Returns the current active scene selection.

        :return: list of selected nodes.
        """

        pass

    @abstractmethod
    def set_active_selection(self, selection: list[Any], replace: bool = True):
        """
        Updates current active scene selection with given nodes.

        :param selection: nodes to set as the active selection.
        :param replace: Whether to replace current selection or not.
        """

        pass

    @abstractmethod
    def clear_active_selection(self):
        """
        Clears current active scene selection.
        """

        pass

    def is_read_only(self):
        """
        Returns whether the current scene is read only or not.

        :return: Whether the current scene is read only or not.
        """

        return (
            paths.is_read_only(self.current_file_path())
            if not self.is_new_scene()
            else False
        )
