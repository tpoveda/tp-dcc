from __future__ import annotations

import ast
from typing import Any

import maya.cmds as cmds

from tp.maya import api
from tp.libs.rig.frag.hooks.maya import utils

METADATA_ATTR = 'fragMetaData'


def decode_metadata(data: str, ref_node: str | None = None) -> Any:
    """
    Parses the given metadata string and returns a valid Python object.

    :param str data: string representing encoded metadata.
    :param str or None ref_node: name of the reference node that contains any nodes in the metadata.
    :return: decoded metadata.
    :rtype: Any
    """

    def _decode_metadata_value(_value: str, _ref_node: str | None = None) -> Any:
        """
        Recursive function that parses the string formatted value and returns the resulting Python object.

        :param str _value: string representing encoded metadata.
        :param str or None _ref_node: name of the reference node that contains any nodes in the metadata.
        :return: Python object.
        :rtype: Any
        """

        if isinstance(_value, dict):
            _result = {}
            for k, v in _value.items():
                _result[k] = _decode_metadata_value(v, _ref_node=_ref_node)
            return _result
        elif isinstance(_value, (list, tuple)):
            return _value.__class__([_decode_metadata_value(_v, _ref_node=_ref_node) for _v in _value])
        elif utils.is_uuid(_value):
            return utils.find_node_by_uuid(_value, _ref_node)

        return _value

    if not data:
        return {}

    try:
        data = ast.literal_eval(data.replace('\r', ''))
    except Exception as err:
        raise ValueError(f'Failed to decode metadata: {err}')

    return _decode_metadata_value(data, ref_node)


def encode_metadata(data: Any) -> str:
    """
    Returns the given metadata associated into a string.

    :param Any data: metadata to encode as a string.
    :return: metadata encoded as a string.
    :rtype: str
    """

    def _encode_metadata_value(_value: Any) -> Any:
        """
        Internal function that returns a metadata value, possibly encoding into an alternate format that supports
        string serialization, handling automatically special data types such as Maya nodes.

        :param Any _value: Any Python value to be encoded.
        :return: encoded value, or the unchanged value if no encondigd was necessary.
        :rtype: Any
        """

        if isinstance(_value, dict):
            _result = {}
            for k, v in _value.items():
                _result[k] = _encode_metadata_value(v)
            return _result
        elif isinstance(_value, (list, tuple)):
            return _value.__class__([_encode_metadata_value(v) for v in _value])
        elif isinstance(_value, api.DGNode):
            return utils.uuid(_value)

        return _value

    return repr(_encode_metadata_value(data))


def metadata(node: api.DagNode, class_name: str | None) -> dict:
    """
    Returns the metadata on given node.

    :param Any node: node to get metadata from.
    :param str or None class_name: If given, only data for that metaclass will be  returned.
    :return: dictionary returning all metadata.
    """

    try:
        plug = node.attribute(METADATA_ATTR)
        data_str = plug.asString()
    except RuntimeError:
        return {}

    ref_node = cmds.referenceQuery(node.fullPathName(), referenceNode=True) if node.isReferenced() else None
    data = decode_metadata(data_str, ref_node)

    return data.get(class_name, {}) if class_name is not None else data


def set_metadata(node: api.DagNode, class_name: str, data: Any, undoable: bool = True, replace: bool = False):
    """
    Sets the metadata for a metaclass type on a node.

    :param api.DagNode node: node we want to set data to.
    :param str class_name: name of the metadata class type.
    :param Any data: data to serialize and store on the node.
    :param bool undoable: Whether the set metadat operation can be undone.
    :param bool replace: whether all already existing metadata should be replaced.
    """

    pass
