from __future__ import annotations

import re


def unique_node_name(name: str, node_names: list[str]) -> str:
    """
    Returns a unique node from the list of given node names.

    :param str name: name of the node.
    :param list[BaseNode] node_names: list of nodes to check names of.
    :return: unique node name.
    :rtype: str
    """

    name = ' '.join(name.split())
    if name not in node_names:
        return name

    regex = re.compile(r'\w+ (\d+)$')
    search = regex.search(name)
    if not search:
        for x in range(1, len(node_names) + 2):
            new_name = f'{name} {x}'
            if new_name not in node_names:
                return new_name

    version = search.group(1)
    name = name[:len(version) * -1].strip()
    for x in range(1, len(node_names) + 2):
        new_name = f'{name} {x}'
        if new_name not in node_names:
            return new_name
