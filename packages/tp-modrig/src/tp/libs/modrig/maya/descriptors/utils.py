from __future__ import annotations

import json
import typing
from typing import Any
from collections.abc import Generator

from ..base import constants

if typing.TYPE_CHECKING:
    from .layers import LayerDescriptorType
    from .nodes import NodeDescriptorType


def traverse_descriptor_layer_dag(
    layer_descriptor: LayerDescriptorType | dict[str, Any],
) -> Generator[NodeDescriptorType]:
    """Traverse a layer descriptor's DAG and yield all nodes in a flat
    structure.

    Args:
        layer_descriptor: The layer descriptor containing the DAG to traverse.

    Yields:
        Each node in the DAG, including all child nodes, in a flat sequence.
    """

    def _iterate_nodes(
        _node: NodeDescriptorType,
    ) -> Generator[NodeDescriptorType]:
        """Recursively iterate over the children of a node.

        Args:
            _node: The node to iterate over.

        Yields:
            The child nodes.
        """

        for _child in iter(_node.children):
            yield _child
            for _n in _iterate_nodes(_child):
                yield _n

    for node in iter(layer_descriptor.get(constants.DAG_DESCRIPTOR_KEY, [])):
        yield node
        for n in _iterate_nodes(node):
            yield n


def parse_raw_descriptor(descriptor_data: dict) -> dict:
    """Parse a raw descriptor data dictionary, transforming it into a
    structured and interpreted format.

    The function processes various keys in the input data, handling them based
    on specific rules and conditions, such as JSON decoding and splitting data
    into components like DAG, settings, and metadata.

    The parsed data is returned as a new structured dictionary.

    Args:
        descriptor_data: A dictionary containing raw descriptor data.
            The values can potentially be JSON strings or other structured
            data formats that need parsing.

    Returns:
        A dictionary containing the structured and interpreted descriptor data.
    """

    translated_data = {}

    for k, v in descriptor_data.items():
        if not v:
            continue
        if k == "info":
            translated_data.update(json.loads(v))
            continue
        elif k == constants.MODULE_SPACE_SWITCH_DESCRIPTOR_KEY:
            translated_data[constants.MODULE_SPACE_SWITCH_DESCRIPTOR_KEY] = json.loads(
                v
            )
            continue
        dag, settings, metadata = (
            v[constants.DAG_DESCRIPTOR_KEY] or "[]",
            v[constants.SETTINGS_DESCRIPTOR_KEY]
            or ("{}" if k == constants.MODULE_RIG_LAYER_DESCRIPTOR_KEY else "[]"),
            v[constants.METADATA_DESCRIPTOR_KEY] or "[]",
        )
        translated_data[k] = {
            constants.DAG_DESCRIPTOR_KEY: json.loads(dag),
            constants.SETTINGS_DESCRIPTOR_KEY: json.loads(settings),
            constants.METADATA_DESCRIPTOR_KEY: json.loads(metadata),
        }

    return translated_data
