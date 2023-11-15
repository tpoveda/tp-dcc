from __future__ import annotations

import uuid

from tp.common.nodegraph.core import consts


class NodeModel:
    def __init__(self):
        super().__init__()

        self.uuid = str(uuid.uuid4())
        self.color = consts.NODE_COLOR
        self.border_color = consts.NODE_BORDER_COLOR
        self.header_color = consts.NODE_HEADER_COLOR
        self.text_color = consts.NODE_TEXT_COLOR
        self.disabled = False
        self.selected = False
        self.visible = True
