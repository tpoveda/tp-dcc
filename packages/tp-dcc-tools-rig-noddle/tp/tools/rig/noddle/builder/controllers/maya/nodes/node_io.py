from __future__ import annotations

from typing import Callable

from tp.libs.rig.noddle.maya import io


def register_plugin(register_node: Callable, register_function: Callable, register_data_type: Callable):

    register_function(
        io.BlendShapesManager.import_all, None,
        nice_name='Import BlendShapes', category='Data')
