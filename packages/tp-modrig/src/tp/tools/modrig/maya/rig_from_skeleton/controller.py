from __future__ import annotations

import typing

from tp.dcc.scene import FnScene
from tp.libs.maya.om import nodes
from tp.libs.qt.mvc import Controller

if typing.TYPE_CHECKING:
    from . import events


class RigFromSkeletonController(Controller):
    """Controller class for Rig from Skeleton tool."""

    @staticmethod
    def get_scene_selection(event: events.GetSelectionFromSceneEvent):
        """Get the scene selection from the event.

        Args:
            event: Get selection from a scene event.
        """

        selection = FnScene().active_selection()
        event.selection = [nodes.name(node, partial_name=True) for node in selection]

    @staticmethod
    def build_rig_from_skeleton(event: events.BuildRigFromSkeletonEvent):
        """Function that builds guides for a skeleton.

        :param event: build guides for skeleton event instance.
        """

        builder = matchguides.BuildMatchGuidesFromSkeleton(
            event.source_joints,
            event.target_ids,
            event.order,
            rig_name=event.rig_name,
            source_namespace=event.source_namespace,
            source_prefix=event.source_prefix,
            source_suffix=event.source_suffix,
        )

        event.update_function(0, "Status: Running Basic Checks.")
        builder.stage1_basic_checks()

        event.update_function(10, "Status: Building the Noddle Guide Template.")
        builder.stage2_build_rig()

        event.success = True
