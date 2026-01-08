from __future__ import annotations

from Qt.QtWidgets import QVBoxLayout

from tp.libs.qt.widgets import Window

class RigBuilderWindow(Window):
    """Main window for Rig Builder"""

    def __init__(self, **kwargs):
        super().__init__(title='Rig Builder', **kwargs)

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        super().setup_widgets()

    def setup_layouts(self, main_layout: QVBoxLayout):
        super().setup_layouts(main_layout)

    def setup_signals(self):
        super().setup_signals()