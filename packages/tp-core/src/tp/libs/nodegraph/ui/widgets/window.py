from __future__ import annotations

from Qt.QtWidgets import QVBoxLayout

from tp.libs.qt.widgets.window import Window

from .editor import NodeGraphEditor


class NodeGraphWindow(Window):
    """NodeGraph window."""

    def __init__(self, title="Node Graph Editor", width=1000, height=800, **kwargs):
        super().__init__(title=title, width=width, height=height, **kwargs)

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        """Set up all widgets for the window."""

        super().setup_widgets()

        self._graph_editor = NodeGraphEditor(parent=self)

    def setup_layouts(self, main_layout: QVBoxLayout):
        """Set up the layouts for the window."""

        super().setup_layouts(main_layout)

        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._graph_editor)
