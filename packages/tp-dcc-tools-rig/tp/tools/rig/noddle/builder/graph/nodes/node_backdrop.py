from __future__ import annotations

from tp.tools.rig.noddle.builder.graph.core import node
from tp.tools.rig.noddle.builder.graph.graphics import backdrop


class BackdropNode(node.Node):

    ID = 32
    IS_EXEC = False
    DEFAULT_TITLE = 'Backdrop'
    TITLE_EDITABLE = False
    UNIQUE = False
    CATEGORY = 'Utils'
    ICON = None
    GRAPHICS_CLASS = backdrop.GraphicsBackdrop


def register_plugin(register_node: callable, register_function: callable, register_data_type: callable):
    register_node(BackdropNode.ID, BackdropNode)
