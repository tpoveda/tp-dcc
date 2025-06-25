from __future__ import annotations

from Qt.QtWidgets import QWidget, QVBoxLayout

from tp.libs.qt import factory
from tp.libs.qt.widgets.window import Window
from tp.libs.qt.widgets.viewmodel.treemodel import TreeModel


class PreferencesView(Window):
    """Preferences view window."""

    def __init__(self, title="Preferences", width=850, height=700, **kwargs):
        super().__init__(name=title, title=title, width=width, height=height, **kwargs)

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        """Set up all the widgets."""

        super().setup_widgets()

    def setup_layouts(self, main_layout: QVBoxLayout):
        """Set up the layouts for the window."""

        super().setup_layouts(main_layout)

    def setup_signals(self):
        """Set up the signals for the window."""

        super().setup_signals()
