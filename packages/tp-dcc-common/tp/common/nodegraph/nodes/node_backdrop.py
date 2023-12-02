from __future__ import annotations

from typing import Callable

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
        data['width'] = self.view.width
        data['height'] = self.view.height
        data['backdrop_text'] = self.view.backdrop_text

    @override
    def pre_deserialization(self, data: dict):
        self.view.width = data['width']
        self.view.height = data['height']
        self.view.backdrop_text = data['backdrop_text']


def register_plugin(register_node: Callable, register_function: Callable, register_data_type: Callable):
    register_node(BackdropNode.ID, BackdropNode)
