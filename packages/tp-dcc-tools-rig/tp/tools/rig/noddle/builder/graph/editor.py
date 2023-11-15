from __future__ import annotations

import typing

from tp.common.qt import api as qt
from tp.tools.rig.noddle.builder.graph.core import graph

if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.controller import NoddleController


class NodeEditor(graph.NodeGraph):
    def __init__(self, controller: NoddleController, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._controller = controller

    @property
    def controller(self) -> NoddleController:
        return self._controller
