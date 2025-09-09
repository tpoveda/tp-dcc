from __future__ import annotations

from tp.libs.maya.wrapper import DagNode

from ...base import constants


class ControlNode(DagNode):

    def id(self) -> str:
        """Return the ID of this settings node.

        The ID is a UUID (Unique Universal Identifier) assigned to the node
        when it is created. Used to uniquely identify the node within the
        scene.

        Returns:
            The node ID as a string.
        """

        id_attr = self.attribute(constants.ID_ATTR)
        return id_attr.value() if id_attr is not None else ""
