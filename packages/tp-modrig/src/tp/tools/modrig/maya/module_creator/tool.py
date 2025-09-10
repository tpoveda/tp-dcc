from __future__ import annotations

import typing
from typing import cast

from Qt.QtWidgets import QVBoxLayout

from tp.libs.qt.widgets import Window
from tp.core import Tool, UiData, current_host

from .model import ModuleCreatorModel
from .view import ModuleCreatorView
from .controller import ModuleCreatorController

if typing.TYPE_CHECKING:
    from tp.tools.modrig.maya.builder.core import ModRigTool


class ModuleCreatorTool(Tool):
    """Tool to create rigging modules interactively."""

    id = "tp.modrig.module_creator"
    creator = "Tomi Poveda"
    ui_data = UiData(label="Module Creator")
    tags = ["modrig", "rigging", "modules"]

    # noinspection PyAttributeOutsideInit
    def execute(self, *args, **kwargs):
        """Execute the tool with the specified arguments.

        Args:
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """

        model = ModuleCreatorModel()
        self._controller = ModuleCreatorController()

        host = current_host()
        window = cast(
            ModuleCreatorWindow,
            host.show_dialog(
                window_class=ModuleCreatorWindow,
                name="ModuleBuilderUI",
                allows_multiple=False,
                model=model,
            ),
        )

        self._controller.prepareTool.connect(window.prepare_tool)
        model.needRefresh.connect(self._controller.need_refresh)
        model.refreshFromScene.connect(self._controller.refresh_from_scene)
        model.addRig.connect(self._controller.add_rig)
        model.addModule.connect(self._controller.add_module)

        model.update_widgets_from_properties()


# noinspection PyAttributeOutsideInit
class ModuleCreatorWindow(Window):
    """Main window for the Module Creator tool."""

    def __init__(self, model: ModuleCreatorModel, **kwargs):
        self._model = model
        super().__init__(title="Module Creator", **kwargs)

    def setup_widgets(self):
        super().setup_widgets()

        self._view = ModuleCreatorView(model=self._model, parent=self)

    def setup_layouts(self, main_layout: QVBoxLayout):
        super().setup_layouts(main_layout)

        main_layout.addWidget(self._view)

    # noinspection PyUnresolvedReferences
    def prepare_tool(self, tool: ModRigTool):
        """Prepares the tool before is executed."""

        tool.view = self._view
        # tool.refreshRequested.connect(self._model.refresh_from_scene)
