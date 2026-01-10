"""MetaHuman base layer metanode class.

This module provides the base layer class for MetaHuman rig components.
Layers are used to organize and track different parts of the rig such as
controls, skeleton, FK/IK systems, etc.
"""

from __future__ import annotations

from collections.abc import Generator

from maya.api import OpenMaya

from tp.libs.maya import factory
from tp.libs.maya.meta.base import MetaBase
from tp.libs.maya.om import attributetypes
from tp.libs.maya.wrapper import DagNode

from . import constants


class MetaHumanLayer(MetaBase):
    """Base layer class for MetaHuman rig components.

    Layers are used to organize different parts of the rig and track
    their associated nodes. Each layer has a root transform and can
    store references to controls and joints.

    This is the base class - specific layer types (controls, skeleton,
    FK/IK, etc.) inherit from this class.

    Example:
        >>> # Layers are typically created via MetaMetaHumanRig.create_layer()
        >>> layer = meta_rig.create_layer(
        ...     METAHUMAN_CONTROLS_LAYER_TYPE,
        ...     "controls_layer",
        ...     "controls_meta"
        ... )
        >>> layer.add_control(some_control_node)
    """

    ID = constants.METAHUMAN_LAYER_TYPE
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
                    name=constants.LAYER_ROOT_TRANSFORM_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.LAYER_CONTROLS_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.LAYER_JOINTS_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
            ]
        )

        return attrs

    # =========================================================================
    # Transform Management
    # =========================================================================

    def root_transform(self) -> DagNode | None:
        """Return the root transform node for this layer.

        Returns:
            The root transform node, or None if not connected.
        """

        return self.sourceNodeByName(constants.LAYER_ROOT_TRANSFORM_ATTR)

    def create_transform(
        self, name: str, parent: DagNode | None = None
    ) -> DagNode:
        """Create the root transform node for this layer.

        Args:
            name: Name for the transform node.
            parent: Optional parent node.

        Returns:
            The newly created transform node.
        """

        existing = self.root_transform()
        if existing is not None:
            return existing

        transform = factory.create_dag_node(
            name=name, node_type="transform", parent=parent
        )
        self.connect_to(constants.LAYER_ROOT_TRANSFORM_ATTR, transform)

        return transform

    # =========================================================================
    # Control Management
    # =========================================================================

    def add_control(self, control: DagNode) -> None:
        """Register a control node to this layer.

        Args:
            control: The control node to add.
        """

        controls_plug = self.attribute(constants.LAYER_CONTROLS_ATTR)
        next_plug = controls_plug.nextAvailableDestElementPlug()
        self.connect_to_by_plug(next_plug, control)

    def iterate_controls(self) -> Generator[DagNode, None, None]:
        """Iterate over all controls in this layer.

        Yields:
            Control nodes connected to this layer.
        """

        controls_plug = self.attribute(constants.LAYER_CONTROLS_ATTR)
        for element in controls_plug:
            source = element.sourceNode()
            if source is not None:
                yield source

    def controls(self) -> list[DagNode]:
        """Return all controls in this layer.

        Returns:
            List of control nodes.
        """

        return list(self.iterate_controls())

    def control_count(self) -> int:
        """Return the number of controls in this layer.

        Returns:
            Number of controls.
        """

        return len(self.controls())

    # =========================================================================
    # Joint Management
    # =========================================================================

    def add_joint(self, joint: DagNode) -> None:
        """Register a joint node to this layer.

        Args:
            joint: The joint node to add.
        """

        joints_plug = self.attribute(constants.LAYER_JOINTS_ATTR)
        next_plug = joints_plug.nextAvailableDestElementPlug()
        self.connect_to_by_plug(next_plug, joint)

    def iterate_joints(self) -> Generator[DagNode, None, None]:
        """Iterate over all joints in this layer.

        Yields:
            Joint nodes connected to this layer.
        """

        joints_plug = self.attribute(constants.LAYER_JOINTS_ATTR)
        for element in joints_plug:
            source = element.sourceNode()
            if source is not None:
                yield source

    def joints(self) -> list[DagNode]:
        """Return all joints in this layer.

        Returns:
            List of joint nodes.
        """

        return list(self.iterate_joints())

    def joint_count(self) -> int:
        """Return the number of joints in this layer.

        Returns:
            Number of joints.
        """

        return len(self.joints())

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def delete(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Delete the layer and its root transform.

        Note: This does NOT delete the controls or joints connected to the
        layer - only the layer metanode and its root transform.

        Args:
            mod: Optional modifier for batched operations.
            apply: Whether to apply the modifier.

        Returns:
            True if deletion was successful.
        """

        root = self.root_transform()
        if root is not None:
            try:
                root.lock(False)
                root.delete()
            except Exception:
                pass

        return super().delete(mod=mod, apply=apply)
