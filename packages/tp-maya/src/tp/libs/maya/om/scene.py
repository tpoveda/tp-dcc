from __future__ import annotations

from typing import Iterable, Iterator

from maya.api import OpenMaya


def iterate_selected_nodes(
    filter_to_apply: Iterable[int] | None = None,
) -> Iterator[OpenMaya.MObject]:
    """
    Generator function that iterates over selected nodes.

    :param filter_to_apply: list of node types to filter by.
    :return: iterated selected nodes.
    """

    def _type_conditional(_filters: tuple[int] | None, _node_type: int):
        try:
            iter(_filters)
            return _node_type in _filters or not _filters
        except TypeError:
            return _node_type == _filters or not _filters

    selection = OpenMaya.MGlobal.getActiveSelectionList()
    for i in range(selection.length()):
        node = selection.getDependNode(i)
        if _type_conditional(filter_to_apply, node.apiType()):
            yield node


def selected_nodes(
    filter_to_apply: Iterable[int] | None = None,
) -> list[OpenMaya.MObject]:
    """
    Returns current selected nodes.

    :param filter_to_apply: list of node types to filter by.
    :return: list of selected nodes.
    """

    return list(iterate_selected_nodes(filter_to_apply))
