from __future__ import annotations

from typing import Iterator, Any

from ..abstract.scene import AFnScene


class FnScene(AFnScene):
    """
    Overloads `AFnScene` exposing functions to handle Standalone scenes.
    """

    def iterate_nodes(self) -> Iterator[Any]:
        """
        Generator function that iterates over all nodes in the scene.

        :return: Iterator to iterate over all nodes in the scene.
        """

        pass

    def active_selection(self) -> list[Any]:
        """
        Returns the current active scene selection.

        :return: list of selected nodes.
        """

        return []

    def set_active_selection(self, selection: list[Any], replace: bool = True):
        """
        Updates current active scene selection with given nodes.

        :param selection: nodes to set as the active selection.
        :param replace: Whether to replace current selection or not.
        """

        pass

    def clear_active_selection(self):
        """
        Clears current active scene selection.
        """

        pass
