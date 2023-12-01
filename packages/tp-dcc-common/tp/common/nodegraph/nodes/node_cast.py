from __future__ import annotations

from typing import Callable


from tp.tools.rig.noddle.builder import api


def num_to_string(in_int: int | float) -> str:
    return str(in_int)


def register_plugin(register_node: Callable, register_function: Callable, register_data_type: Callable):

    register_function(
        num_to_string, api.DataType.NUMERIC,
        inputs={'In': api.DataType.NUMERIC}, outputs={'Out': api.DataType.STRING},
        nice_name='Num to Str', category='Utils')
