from __future__ import annotations

from tp.libs.rig.noddle.maya import io


def register_plugin(register_node: callable, register_function: callable, register_data_type: callable):

    register_function(
        io.BlendShapesManager.import_all, None,
        nice_name='Import BlendShapes', category='Data')
