from __future__ import annotations

from overrides import override

from tp.common.nodegraph.core import node
from tp.common.nodegraph.graphics import backdrop


class BackdropNode(node.BaseNode):

    ID = 32
    IS_EXEC = False
    DEFAULT_TITLE = 'Backdrop'
    TITLE_EDITABLE = False
    UNIQUE = False
    CATEGORY = 'Utils'
    ICON = None
    GRAPHICS_CLASS = backdrop.GraphicsBackdrop

    @override
    def post_serialization(self, data: dict):
        data['width'] = self.graphics_node.width
        data['height'] = self.graphics_node.height
        data['backdrop_text'] = self.graphics_node.backdrop_text

    @override
    def pre_deserialization(self, data: dict):
        self.graphics_node.width = data['width']
        self.graphics_node.height = data['height']
        self.graphics_node.backdrop_text = data['backdrop_text']


def register_plugin(register_node: callable, register_function: callable, register_data_type: callable):
    register_node(BackdropNode.ID, BackdropNode)
