from __future__ import annotations

from typing import Any

from tp.libs.commands import Command
from tp.libs.modrig.maya import api


class DeleteRigCommand(Command):
    """Command that deletes a rig instance from the scene."""

    _rig: api.Rig | None = None
    _template: dict[str, Any] | None = None

    id = "modrig.rig.delete"
    is_undoable = True

    def do(self, rig: api.Rig | None = None) -> bool:
        """Execute the command functionality.

        Args:
            rig: Rig instance to delete.

        Returns:
            The newly created rig instance.
        """

        return rig.delete()

    def undo(self) -> None:
        """Reverse the operation done by the `do` method."""

        if not self._template:
            return

        print('Undoing rig deletion is not implemented yet.')