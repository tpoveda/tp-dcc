from __future__ import annotations

from typing import Any


def decode_metadata(data: str, ref_node: str | None = None) -> Any:
    """
    Parses the given metadata string and returns a valid Python object.

    :param str data: string representing encoded metadata.
    :param str or None ref_node: name of the reference node that contains any nodes in the metadata.
    :return: decoded metadata.
    :rtype: Any
    """

    return None


def encode_metadata(data: Any) -> str:
    """
    Returns the given metadata associated into a string.

    :param Any data: metadata to encode as a string.
    :return: metadata encoded as a string.
    :rtype: str
    """

    return ''


def metadata(node: Any, class_name: str | None) -> dict:
    """
    Returns the metadata on given node.

    :param Any node: node to get metadata from.
    :param str or None class_name: If given, only data for that metaclass will be  returned.
    :return: dictionary returning all metadata.
    """

    return {}


def set_metadata(node: Any, class_name: str, data: Any, undoable: bool = True, replace: bool = False):
    """
    Sets the metadata for a metaclass type on a node.

    :param Any node: node we want to set data to.
    :param str class_name: name of the metadata class type.
    :param Any data: data to serialize and store on the node.
    :param bool undoable: Whether the set metadat operation can be undone.
    :param bool replace: whether all already existing metadata should be replaced.
    """

    pass
