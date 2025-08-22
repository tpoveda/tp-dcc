from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from ..core import NodeId, BaseNode


class GraphModel:
    def __init__(self):
        super().__init__()

        self._nodes: dict[NodeId, BaseNode] = {}
