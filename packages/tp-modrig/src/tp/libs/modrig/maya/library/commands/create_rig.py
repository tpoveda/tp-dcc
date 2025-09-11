from __future__ import annotations

from typing import Any

from maya import cmds

from tp.libs.commands import Command
from tp.libs.modrig.maya import api


class CreateRigCommand(Command):
    """Command that creates a new rig instance in the scene."""

    id = "modrig.rig.create"
    is_undoable = False

    _rig: api.Rig | None = None

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

        arguments["namespace"] = arguments.get("namespace")
        name = arguments.get("name") or "ModRig"
        arguments["name"] = api.unique_name_for_rig(api.iterate_scene_rigs(), name)

        return arguments

    def do(
        self, name: str | None = None, namespace: str | None = None
    ) -> api.Rig | None:
        """Execute the command functionality.

        Args:
            name: Name for the new rig instance. If None or empty string
                provided, 'ModRig' will be used.
            namespace: Optional namespace to create the rig in.

        Returns:
            The newly created rig instance.
        """

        current_display_layer = cmds.editDisplayLayerGlobals(
            query=True, useCurrent=False
        )
        try:
            cmds.editDisplayLayerGlobals(useCurrent=False)
            rig = api.Rig()
            self._rig = rig
            rig.start_session(name=name, namespace=namespace)
        finally:
            cmds.editDisplayLayerGlobals(useCurrent=current_display_layer)

        return rig
