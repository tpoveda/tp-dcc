from __future__ import annotations

import typing

from tp.common.nodegraph import registers

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.node import BaseNode


def create_node(node_type: int | str) -> BaseNode | None:
    """
    Creates a new node object based on the given node type.

    :param int or str node_type: node type to create.
    :return: newly created node instance.
    :rtype: BaseNode or None
    """

    node_class = registers.node_class_from_id(node_type)
    return node_class() if node_class else None
