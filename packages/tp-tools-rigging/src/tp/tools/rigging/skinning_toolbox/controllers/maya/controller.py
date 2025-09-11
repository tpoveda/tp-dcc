from __future__ import annotations

from ..abstract import ASkinningToolboxController

from tp.libs.maya.cmds.skin import bindskin
from tp.libs.maya.cmds.decorators import undo


class MayaSkinningToolboxController(ASkinningToolboxController):
    @undo
    def skin_transfer(self) -> None:
        """Transfers the skin weights from the first selected object to the
        rest of selected objects.
        """

        bindskin.transfer_skin_weights_for_selection()

    @undo
    def skin_toggle(self) -> None:
        """Toggles the state of the first skin cluster on the selected meshes."""

        bindskin.toggle_skin_cluster_for_selection()
