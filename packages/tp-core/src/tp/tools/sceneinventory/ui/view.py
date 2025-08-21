from __future__ import annotations

from Qt.QtWidgets import QWidget, QVBoxLayout

from tp.libs.qt import factory
from tp.libs.qt.widgets.window import Window

from ..controller import SceneInventoryController


class SceneInventoryView(QWidget):
    """Scene inventory view widget."""

    def __init__(
        self, controller: SceneInventoryController, parent: QWidget | None = None
    ):
        super().__init__(parent)

        self._controller = controller

        self._setup_widgets()
        self._setup_layouts()

    def _setup_widgets(self):
        """Set up all view widgets."""

        self._button = factory.base_button("Hello World", parent=self)

    def _setup_layouts(self):
        """Set up the layouts and add all widgets to them."""

        main_layout = factory.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        main_layout.addWidget(self._button)


class SceneInventoryWindow(Window):
    """Scene Inventory window."""

    def __init__(self, title="Scene Inventory", width=1000, height=600, **kwargs):
        self._controller = kwargs.get("controller", SceneInventoryController())

        super().__init__(title=title, width=width, height=height, **kwargs)

        project_name = self._controller.get_current_project_name()

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        """Set up all the widgets."""

        super().setup_widgets()

        self._scene_inventory = SceneInventoryView(
            controller=self._controller, parent=self
        )

    def setup_layouts(self, main_layout: QVBoxLayout):
        """Set up the layouts for the window."""

        super().setup_layouts(main_layout)

        main_layout.addWidget(self._scene_inventory)
