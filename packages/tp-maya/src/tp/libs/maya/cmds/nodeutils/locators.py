from __future__ import annotations

from maya import cmds

from . import matching


def create_locator(name: str = '', handle: bool = False, size: float = 1.0) -> str:
    """
    Creates a locator at the origin of the world.

    :param name: name of the locator.
    :param handle: whether to show display handle.
    :param size: size of the locator.
    :return: name of the created locator.
    """

    locator = cmds.spaceLocator()[0] if not name else cmds.spaceLocator(name=name)[0]
    cmds.setAttr(f'{locator}.localScale', size, size, size, type='double3')
    if handle:
        cmds.setAttr(f'{locator}.displayHandle', True)

    return locator

def create_locators_and_match_to_nodes(node_names: list[str], name: str = '', handle: bool = False, size: float = 1.0) -> str:
    """
    Creates a locator and matches it to the currently selected object or component selection center or world center.

    :param node_names: list of objects to match the locator to.
    :param name: name of the locator.
    :param handle: whether to show display handle.
    :param size: size of the locator.
    :return: name of the created locator.
    """

    locator = create_locator(name=name, handle=handle, size=size)
    matching.match_node_to_center_of_node_components(locator, node_names)
    cmds.select(locator, replace=True)

    return locator
