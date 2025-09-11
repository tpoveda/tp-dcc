from __future__ import annotations

from tp.libs.modrig.maya import api
from tp.libs.modrig.commands import modrig

from . import utils
from ..core.tool import ModRigTool, ModRigToolUiData


class CreateRigTool(ModRigTool):
    id = "createRig"
    ui_data = ModRigToolUiData(
        icon="add",
        label="Create Rig Instance",
    )

    def execute(self, name: str) -> api.Rig | None:
        """Creates a new rig in the Maya scene and forces the refresh of the UIs.

        Args:
            name: Name of the rig to create.

        Returns:
            Created rig instance.
        """

        success = utils.check_scene_units(parent=self.view)
        if not success:
            return None

        rig = modrig.create_rig(name=name)
        self.request_refresh(force=False)

        return rig
