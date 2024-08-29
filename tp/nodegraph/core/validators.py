from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from .port import NodePort


def validate_accept_connection(source_port: NodePort, target_port: NodePort) -> bool:
    """
    Validates if a connection between two ports is valid based on port accept constraints.

    :param source_port: source port to validate.
    :param target_port: target port to validate.
    :return: whether the connection is valid or not.
    """

    source_node_type = source_port.node.type
    # noinspection PyTypeChecker
    target_accepted_types = target_port.accepted_port_types().get(source_node_type)
    if target_accepted_types:
        accepted_port_names = target_accepted_types.get(source_port.type) or set([])
        if source_port.name not in accepted_port_names:
            return False

    target_node_type = target_port.node.type
    # noinspection PyTypeChecker
    source_accepted_types = source_port.accepted_port_types().get(target_node_type)
    if source_accepted_types:
        accepted_port_names = source_accepted_types.get(target_port.type) or set([])
        if target_port.name not in accepted_port_names:
            return False

    return True


def validate_reject_connection(source_port: NodePort, target_port: NodePort) -> bool:
    """
    Validates if a connection between two ports is valid based on port reject constraints.

    :param source_port: source port to validate.
    :param target_port: target port to validate.
    :return: whether the connection is valid or not.
    """

    source_node_type = source_port.node.type

    # noinspection PyTypeChecker
    target_rejected_types = target_port.rejected_port_types().get(source_node_type)
    if target_rejected_types:
        rejected_port_names = target_rejected_types.get(source_port.type) or set([])
        if source_port.name in rejected_port_names:
            return False

    target_node_type = target_port.node.type
    # noinspection PyTypeChecker
    source_rejected_types = source_port.rejected_port_types().get(target_node_type)
    if source_rejected_types:
        rejected_port_names = source_rejected_types.get(target_port.type) or set([])
        if target_port.name in rejected_port_names:
            return False

    return True
