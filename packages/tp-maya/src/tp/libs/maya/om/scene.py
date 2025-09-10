from __future__ import annotations

from collections.abc import Iterable, Generator

from maya.api import OpenMaya


def iterate_selected_nodes(
    filter_to_apply: Iterable[int] | None = None,
) -> Generator[OpenMaya.MObject]:
    """Generator function that iterates over selected nodes.

    Args:
        filter_to_apply: List of node types to filter by.

    Returns:
        Iterated selected nodes.
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
    """Return the currently selected nodes.

    Args:
        filter_to_apply: List of node types to filter by.

    Returns:
        List of selected nodes.
    """

    return list(iterate_selected_nodes(filter_to_apply))


def is_centimeters() -> bool:
    """Return whether the current Maya scene is set to use centimeters as
    linear unit.

    Returns:
        `True` if the current Maya scene is set to use centimeters as linear
        unit; `False` otherwise.
    """

    return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kCentimeters


def is_feet() -> bool:
    """Return whether the current Maya scene is set to use feet as linear
    unit.

    Returns:
        `True` if the current Maya scene is set to use feet as linear unit;
        `False` otherwise.
    """

    return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kFeet


def is_inches() -> bool:
    """Return whether the current Maya scene is set to use inches as linear
    unit.

    Returns:
        `True` if the current Maya scene is set to use inches as linear unit;
        `False` otherwise.
    """

    return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kInches


def is_kilometers() -> bool:
    """Return whether the current Maya scene is set to use kilometers as
    linear unit.

    Returns:
        `True` if the current Maya scene is set to use kilometers as linear
        unit; `False` otherwise.
    """

    return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kKilometers


def is_last() -> bool:
    """Return whether the current Maya scene is set to use last as linear
    unit.

    Returns:
        `True` if the current Maya scene is set to use last as linear unit;
        `False` otherwise.
    """

    return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kLast


def is_meters() -> bool:
    """Return whether the current Maya scene is set to use meters as linear
    unit.

    Returns:
        `True` if the current Maya scene is set to use meters as linear unit;
        `False` otherwise.
    """

    return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kMeters


def is_miles() -> bool:
    """Return whether the current Maya scene is set to use miles as linear
    unit.

    Returns:
        `True` if the current Maya scene is set to use miles as linear unit;
        `False` otherwise.
    """

    return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kMiles


def is_millimeters() -> bool:
    """Return whether the current Maya scene is set to use millimeters as
    linear unit.

    Returns:
        `True` if the current Maya scene is set to use millimeters as linear
        unit; `False` otherwise.
    """

    return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kMillimeters


def is_yards() -> bool:
    """Return whether the current Maya scene is set to use yards as linear
    unit.

    Returns:
        `True` if the current Maya scene is set to use yards as linear unit;
        `False` otherwise.
    """

    return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kYards
