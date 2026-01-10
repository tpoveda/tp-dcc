"""MetaHuman Skeleton Layer metanode class.

This module provides the skeleton layer class for MetaHuman body rigs.
The skeleton layer manages the motion skeleton and bind skeleton connections.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

from maya.api import OpenMaya

from tp.libs.maya.om import attributetypes
from tp.libs.maya.wrapper import DagNode

from .. import constants
from ..layer import MetaHumanLayer

if TYPE_CHECKING:
    pass


class MetaHumanSkeletonLayer(MetaHumanLayer):
    """Layer class for MetaHuman skeleton management.

    This layer manages the motion skeleton and bind skeleton for the
    body rig. It tracks all joints and provides methods for querying
    skeleton structure.

    Example:
        >>> # Skeleton layers are typically created via the rig
        >>> layer = meta_rig.create_layer(
        ...     METAHUMAN_SKELETON_LAYER_TYPE,
        ...     "skeleton_layer",
        ...     "skeleton_meta"
        ... )
        >>> layer.connect_root_joint(root_joint)
        >>> layer.add_joint(spine_joint)
    """

    ID = constants.METAHUMAN_SKELETON_LAYER_TYPE
    VERSION = "1.0.0"

    def meta_attributes(self) -> list[dict]:
        """Return the list of default metanode attributes.

        Returns:
            List of dictionaries with attribute definitions.
        """

        attrs = super().meta_attributes()

        attrs.extend(
            [
                dict(
                    name=constants.SKELETON_LAYER_ROOT_JOINT_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.SKELETON_LAYER_BIND_ROOT_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.SKELETON_LAYER_IS_MOTION_SKELETON_ATTR,
                    type=attributetypes.kMFnNumericBoolean,
                    value=True,
                ),
            ]
        )

        return attrs

    # =========================================================================
    # Root Joint Management
    # =========================================================================

    def root_joint(self) -> DagNode | None:
        """Return the root joint of the skeleton.

        Returns:
            The root joint node, or None if not connected.
        """

        return self.sourceNodeByName(constants.SKELETON_LAYER_ROOT_JOINT_ATTR)

    def connect_root_joint(self, joint: DagNode) -> None:
        """Connect the root joint of the skeleton.

        Args:
            joint: The root joint node to connect.
        """

        self.connect_to(constants.SKELETON_LAYER_ROOT_JOINT_ATTR, joint)

    def bind_root_joint(self) -> DagNode | None:
        """Return the root joint of the bind skeleton.

        Returns:
            The bind root joint node, or None if not connected.
        """

        return self.sourceNodeByName(constants.SKELETON_LAYER_BIND_ROOT_ATTR)

    def connect_bind_root(self, joint: DagNode) -> None:
        """Connect the bind skeleton root joint.

        Args:
            joint: The bind root joint node to connect.
        """

        self.connect_to(constants.SKELETON_LAYER_BIND_ROOT_ATTR, joint)

    # =========================================================================
    # Skeleton Properties
    # =========================================================================

    def is_motion_skeleton(self) -> bool:
        """Return whether this is a motion skeleton.

        Returns:
            True if this is a motion skeleton.
        """

        return self.attribute(
            constants.SKELETON_LAYER_IS_MOTION_SKELETON_ATTR
        ).value()

    def set_is_motion_skeleton(self, is_motion: bool) -> None:
        """Set whether this is a motion skeleton.

        Args:
            is_motion: True if this is a motion skeleton.
        """

        self.attribute(constants.SKELETON_LAYER_IS_MOTION_SKELETON_ATTR).set(
            is_motion
        )

    # =========================================================================
    # Joint Query Methods
    # =========================================================================

    def iterate_joints_by_side(
        self, side: str
    ) -> Generator[DagNode, None, None]:
        """Iterate over joints filtered by side.

        Args:
            side: Side indicator ('l', 'r', 'c' for left/right/center).

        Yields:
            Joint nodes matching the specified side.
        """

        for joint in self.iterate_joints():
            name = joint.name()
            if f"_{side}" in name or name.endswith(f"_{side}"):
                yield joint

    def left_joints(self) -> list[DagNode]:
        """Return all left-side joints.

        Returns:
            List of left-side joint nodes.
        """

        return list(self.iterate_joints_by_side("l"))

    def right_joints(self) -> list[DagNode]:
        """Return all right-side joints.

        Returns:
            List of right-side joint nodes.
        """

        return list(self.iterate_joints_by_side("r"))

    def center_joints(self) -> list[DagNode]:
        """Return all center joints (no side suffix).

        Returns:
            List of center joint nodes.
        """

        result = []
        for joint in self.iterate_joints():
            name = joint.name()
            if "_l" not in name and "_r" not in name:
                result.append(joint)
        return result
