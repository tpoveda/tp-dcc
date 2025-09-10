from __future__ import annotations

from Qt.QtWidgets import QWidget

from tp.core.tool import Tool, UiData

from .view import RigFromSkeletonView
from .model import RigFromSkeletonModel
from .controller import RigFromSkeletonController


class RigFromSkeletonTool(Tool):
    """Tool that allows to create new characters from a skin proxy skeleton."""

    id = "tp.tools.rig.rigfromskeleton"
    creator = "Tomas Poveda"
    ui_data = UiData(label="Build Rig from Skeleton")
    tags = ["rig", "noddle", "skeleton", "tp", "rigging"]

    def __init__(self, *args, **kwargs):
        self._model = kwargs.pop("model")
        self._controller = kwargs.pop("controller")

        super().__init__(*args, **kwargs)

        self._view: RigFromSkeletonView | None = None

    def contents(self) -> list[QWidget]:
        self._view = RigFromSkeletonView(model=self._model)
        return [self._view]


def show() -> RigFromSkeletonTool:
    """Function to show the Rig from Skeleton tool.

    :return: Rig from Skeleton tool instance created by this function.
    """

    model = RigFromSkeletonModel()
    controller = RigFromSkeletonController()
    tool = RigFromSkeletonTool(model=model, controller=controller)
    tool.execute()

    model.getSelectionFromScene.connect(controller.get_scene_selection)
    model.buildRigFromSkeleton.connect(controller.build_rig_from_skeleton)

    model.load_presets()
    model.update_widgets_from_properties()

    return tool
