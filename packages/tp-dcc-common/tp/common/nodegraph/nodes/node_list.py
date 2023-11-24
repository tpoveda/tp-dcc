from __future__ import annotations

from typing import Any, Callable

from tp.common.nodegraph import api


def item_from_list(in_list: list[Any], index: int) -> Any:
    return in_list[int(index)]


def register_plugin(register_node: Callable, register_function: Callable, register_data_type: Callable):

    register_function(
        item_from_list, api.DataType.LIST,
        inputs={'List': api.DataType.LIST, 'Index': api.DataType.NUMERIC}, outputs={'Item': api.DataType.STRING},
        default_values=[[], 0], nice_name='Get String', subtype='string', category='List')
