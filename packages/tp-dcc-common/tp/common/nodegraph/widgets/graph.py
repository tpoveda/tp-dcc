from __future__ import annotations

import typing

from overrides import override

from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.graph import NodeGraph
    from tp.common.nodegraph.graphics.view import GraphicsView


class NodeGraphWidget(qt.QTabWidget):

    aboutToClose = qt.Signal(qt.QWidget, qt.QCloseEvent)

    def __init__(self, parent: qt.QWidget | None = None):
        super().__init__(parent)

        self.setTabsClosable(True)
        self.setTabBarAutoHide(True)

        self.setAttribute(qt.Qt.WA_DeleteOnClose)
        self.setMinimumSize(200, 500)

    @override
    def closeEvent(self, event: qt.QCloseEvent) -> None:
        self.aboutToClose.emit(self, event)

    def add_viewer(self, viewer: GraphicsView, name: str, sub_graph_id: str):
        """
        Adds a new node graph viewer.

        :param GraphicsView viewer: node graph viewer.
        :param str name: graph name.
        :param str sub_graph_id: sub graph ID.
        """

        self.addTab(viewer, name)
        index = self.indexOf(viewer)
        self.setTabToolTip(index, sub_graph_id)
        self.setCurrentIndex(index)

    def graph(self) -> NodeGraph:
        """
        Returns parent graph.

        :return: graph.
        :rtype: NodeGraph
        """

        return self.widget(0).scene
