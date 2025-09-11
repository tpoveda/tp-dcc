from __future__ import annotations

from typing import Any

from maya.api import OpenMaya

from tp.libs.maya.wrapper import selected, select, DagNode
from tp.libs.commands import Command
from tp.libs.modrig.maya import api


class CreateModulesCommand(Command):
    """Command that creates new modules to a rig in the scene."""

    id = "modrig.rig.create.modules"
    is_undoable = True
    use_undo_chunk = True
    disable_queue = True

    _rig: api.Rig | None = None
    _modules: list[dict[str, Any]] = []
    _parent_node: DagNode | None = None

    def resolve_arguments(self, arguments: dict[str, Any]) -> dict[str, Any] | None:
        """Function that is called before running the command.

        Notes:
            Useful to validate incoming command arguments before executing
            the command.

        Args:
            arguments: Dictionary with the same key value pairs as the
                arguments param.

        Returns:
            Dictionary with the same key value pairs as the arguments param.
        """

        rig: api.Rig = arguments.get("rig")
        if rig is None:
            self.display_warning("Must provide a rig instance to add modules to.")
            return

        modules_data: list[dict[str, Any]] = arguments.get("modules")
        if not modules_data:
            self.display_warning("Must provide at least one module to create.")
            return

        if not rig.exists():
            self.display_warning(
                "The provided rig instance does not exist in the scene."
            )
            return

        selection = list(selected(filter_types=[OpenMaya.MFn.kTransform]))
        if selection:
            arguments["parent_node"] = selection[0]

        self._rig = rig
        self._modules = modules_data
        self._parent_node = arguments.get("parent_node")

    def do(
        self,
        rig: api.Rig | None = None,
        modules: list[dict[str, Any]] | None = None,
        build_guides: bool = False,
        build_rigs: bool = False,
        parent_node: DagNode | None = None,
    ) -> list[api.Module]:
        """Execute the command functionality."""

        created_modules: list[api.Module] = []

        for module_data in self._modules:
            # Create the module in the scene.
            new_module = rig.create_module(
                module_type=module_data["type"],
                name=module_data["name"],
                side=module_data["side"],
                descriptor=module_data.get("descriptor"),
            )
            module_data["name"] = new_module.name()
            module_data["side"] = new_module.side()
            if new_module:
                created_modules.append(new_module)

        if build_guides:
            self._rig.build_guides()

            # If a parent node was specified, move the guide roots to the
            # position of that node.
            if self._parent_node:
                parent_transform = self._parent_node.translation()
                for module in created_modules:
                    root = module.guide_layer().guide_root()
                    if root:
                        root.setTranslation(
                            parent_transform, space=OpenMaya.MSpace.kWorld
                        )

            # Retrieve the guide roots of the created modules and select them.
            root_guides: list[api.GuideNode] = []
            for module in created_modules:
                root = module.guide_layer().guide_root()
                if root is not None:
                    root_guides.append(root)
            if root_guides:
                select(root_guides)

        if build_rigs:
            self._rig.build_rigs(created_modules)

        return created_modules

    def undo(self) -> None:
        """Reverse the operation done by the `do` method."""

        if not self._rig or not self._rig.exists():
            return

        for module_data in self._modules:
            self._rig.delete_module(module_data["name"], module_data["side"])
