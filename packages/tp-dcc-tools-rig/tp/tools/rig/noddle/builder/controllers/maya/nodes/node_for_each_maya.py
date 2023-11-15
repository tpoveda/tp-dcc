from __future__ import annotations


from tp.tools.rig.noddle.builder import api

from tp.common.nodegraph.nodes import node_for_each


class ForEachComponent(node_for_each.ForEachNode):
    ID = 105
    DEFAULT_TITLE = "For Each Component"
    COLLECTION_DATA_TYPE = api.DataType.COMPONENT


def register_plugin(register_node: callable, register_function: callable, register_data_type: callable):
    register_node(ForEachComponent.ID, ForEachComponent)
