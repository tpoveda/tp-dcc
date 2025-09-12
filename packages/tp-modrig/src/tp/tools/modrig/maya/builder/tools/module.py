from __future__ import annotations

from tp.libs.modrig.maya import api
from tp.libs.modrig.commands import modrig
from tp.libs.modrig.maya.descriptors import ModuleDescriptor

from . import utils
from ..core.tool import ModRigTool, ModRigToolUiData


class CreateModuleTool(ModRigTool):
    id = "createModule"
    ui_data = ModRigToolUiData(
        icon="add",
        label="Create Module",
    )

    def execute(
        self,
        module_id: str,
        rig: api.Rig,
        name: str | None = None,
        side: str | None = None,
        descriptor: ModuleDescriptor | None = None,
        build_guides: bool = True,
    ) -> api.Module | None:
        """Creates a new module in the current rig.

        Args:
            module_id: ID of the module to create.
            rig: Rig instance to create the module in.
            name: Name of the module to create.
            side: Side of the module to create.
            descriptor: Optional module descriptor to use for the creation
                of the module. If `None`, the module descriptor will be looked
                up using the specified module ID.
            build_guides: Whether to build guides after creating the module.

        Returns:
            Created module instance.
        """

        success = utils.check_scene_units(parent=self.view)
        if not success:
            return None

        name = descriptor.name if descriptor is not None else name
        side = descriptor.side if descriptor is not None else side

        modules = modrig.create_modules(
            rig=rig,
            modules=[
                {
                    "type": module_id,
                    "name": name,
                    "side": side,
                    "descriptor": descriptor,
                }
            ],
            build_guides=build_guides,
        )

        return modules[0] if modules else None
