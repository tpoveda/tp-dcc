from __future__ import annotations

import typing
from typing import Any

from loguru import logger
from Qt.QtCore import Signal

from tp.libs.qt import Controller
from tp.libs.python import profiler
from tp.libs.modrig.maya import api
from tp.tools.modrig.maya.builder.managers import ModRigToolsManager

from . import events

if typing.TYPE_CHECKING:
    from tp.tools.modrig.maya.builder.models.rig import RigModel


class ModuleCreatorController(Controller):
    prepareTool = Signal(object)

    def __init__(self):
        super().__init__()

        self._tools_manager = ModRigToolsManager()

    @staticmethod
    def need_refresh(event: events.NeedRefreshEvent) -> None:
        """Checks whether the model needs to be refreshed based on the current
        scene state.

        Args:
            event: NeedRefreshEvent instance.
        """

        rig_meta_nodes = list(api.iterate_scene_rig_meta_nodes())
        if len(rig_meta_nodes) != len(event.rig_models):
            logger.debug(
                f"Number of scene rigs ({len(rig_meta_nodes)}) different than "
                f"in model ({len(event.rig_models)}). Refreshing ..."
            )
            event.result = True
            return

        for rig_meta_node in rig_meta_nodes:
            found_rig_model: RigModel | None = None
            for rig_model in event.rig_models:
                if rig_model.meta == rig_meta_node:
                    found_rig_model = rig_model
                    break

            # If we didn't find the rig model, it means the number of rigs is
            # different from expected.
            if not found_rig_model:
                logger.debug(
                    f"Number of scene rigs ({len(rig_meta_nodes)}) "
                    f"different than in model ({len(event.rig_models)}). "
                    f"Refreshing ..."
                )
                event.result = True
                return

            # If no modules layer found, it means the rig is not fully set up
            # so we need to refresh.
            modules_layer = rig_meta_node.modules_layer()
            if not modules_layer:
                return

            # If the number of modules is different, we need to refresh.
            if len(modules_layer.modules()) != len(found_rig_model.module_models):
                logger.debug(
                    f"Number of modules for rig '{rig_meta_node.name()}' in "
                    f"scene ({len(modules_layer.modules())}) different than "
                    f"in model ({len(found_rig_model.module_models)}). "
                    f"Refreshing ..."
                )
                event.result = True
                return

    @staticmethod
    def refresh_from_scene(event: events.RefreshFromSceneEvent) -> None:
        event.rigs = list(api.iterate_scene_rigs())

    def add_rig(self, event: events.AddRigEvent):
        event.rig = self.execute_tool("createRig", args={"name": event.name})

    def add_module(self, event: events.OpenModuleEvent):
        self.execute_tool(
            "createModule",
            args={
                "rig": event.rig,
                "module_id": event.module_id,
                "name": event.name,
                "side": event.side,
                "descriptor": event.descriptor,
            },
        )

    @profiler.fn_timer
    def execute_tool(self, tool_id: str, args: dict[str, Any] | None = None) -> Any:
        ids = tool_id.split(".")
        variant_id: str | None = None
        if len(ids) > 1:
            tool_id = ids[0]
            variant_id = ids[1]

        tool_class = self._tools_manager.tool_class(tool_id)
        if tool_class is None:
            logger.error(f"Tool '{tool_id}' not found. Make sure it is registered.")
            return False

        tool_instance = tool_class()
        args = args or {}
        if variant_id:
            args["variant"] = variant_id

        self.prepareTool.emit(tool_instance)

        return tool_instance.process(variant_id=variant_id, args=args)
