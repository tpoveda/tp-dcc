from __future__ import annotations

import uuid
import typing

from tp.common.nodegraph.core import consts

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.models.graph import NodeGraphModel


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

        self._graph_model: NodeGraphModel | None = None

    @property
    def graph_model(self) -> NodeGraphModel:
        """
        Returns graph model (which is set when node is added into a graph).

        :return: NodeGraphModel
        """

        return self._graph_model

    @graph_model.setter
    def graph_model(self, value: NodeGraphModel):
        """
        Sets graph model this node belongs to.

        :param NodeGraphModel value: graph model.
        """

        self._graph_model = value
