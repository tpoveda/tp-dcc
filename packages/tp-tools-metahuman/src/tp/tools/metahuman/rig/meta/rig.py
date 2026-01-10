"""MetaHuman Rig metanode class.

This module provides the root metanode class for MetaHuman body rigs.
It manages the rig hierarchy, groups, layers, and provides methods for
rig creation and deletion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from loguru import logger
from maya.api import OpenMaya

from tp.libs.maya import factory
from tp.libs.maya.meta.base import MetaBase
from tp.libs.maya.om import attributetypes
from tp.libs.maya.wrapper import DagNode, DisplayLayer

from . import constants

if TYPE_CHECKING:
    from .layer import MetaHumanLayer


class MetaMetaHumanRig(MetaBase):
    """Metaclass for a MetaHuman body rig.

    This is the root metanode for a MetaHuman body rig. It stores references
    to all rig components including groups, layers, and settings. It provides
    methods for creating and managing the rig hierarchy.

    Example:
        >>> # Create a new rig
        >>> meta_rig = MetaMetaHumanRig(name="myCharacter_rig_meta")
        >>> meta_rig.attribute(constants.NAME_ATTR).set("myCharacter")
        >>>
        >>> # Create rig groups
        >>> meta_rig.create_setup_group("rig_setup")
        >>> meta_rig.create_controls_group("rig_ctrls")
        >>>
        >>> # Query rig components
        >>> setup_grp = meta_rig.setup_group()
        >>> controls_grp = meta_rig.controls_group()
    """

    ID = constants.METAHUMAN_RIG_TYPE
    VERSION = "1.0.0"

    def meta_attributes(self) -> list[dict]:
        """Return the list of default metanode attributes.

        These attributes are automatically created when the metanode is
        instantiated.

        Returns:
            List of dictionaries with attribute definitions.
        """

        attrs = super().meta_attributes()

        attrs.extend(
            [
                dict(
                    name=constants.RIG_VERSION_ATTR,
                    type=attributetypes.kMFnDataString,
                    value=constants.DEFAULT_RIG_VERSION,
                ),
                dict(
                    name=constants.NAME_ATTR,
                    type=attributetypes.kMFnDataString,
                    value="",
                ),
                dict(
                    name=constants.ID_ATTR,
                    type=attributetypes.kMFnDataString,
                    value="",
                ),
                dict(
                    name=constants.IS_METAHUMAN_RIG_ATTR,
                    value=True,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.IS_ROOT_ATTR,
                    value=True,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.RIG_IS_MOTION_MODE_ATTR,
                    value=True,
                    type=attributetypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.RIG_ROOT_TRANSFORM_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.RIG_CONTROLS_GROUP_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.RIG_SETUP_GROUP_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.RIG_MOTION_SKELETON_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.RIG_CONTROL_DISPLAY_LAYER_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
            ]
        )

        return attrs

    # =========================================================================
    # Properties and Getters
    # =========================================================================

    def rig_name(self) -> str:
        """Return the name of the rig.

        Returns:
            The rig name string.
        """

        return self.attribute(constants.NAME_ATTR).asString()

    def rig_version(self) -> str:
        """Return the version of the rig.

        Returns:
            The rig version string.
        """

        return self.attribute(constants.RIG_VERSION_ATTR).asString()

    def is_motion_mode(self) -> bool:
        """Return whether the rig uses motion skeleton mode.

        Returns:
            True if motion mode is enabled.
        """

        return self.attribute(constants.RIG_IS_MOTION_MODE_ATTR).value()

    # =========================================================================
    # Group Management
    # =========================================================================

    def root_transform(self) -> DagNode | None:
        """Return the root transform node for the rig.

        Returns:
            The root transform node, or None if not connected.
        """

        return self.sourceNodeByName(constants.RIG_ROOT_TRANSFORM_ATTR)

    def controls_group(self) -> DagNode | None:
        """Return the controls group node.

        Returns:
            The controls group node, or None if not connected.
        """

        return self.sourceNodeByName(constants.RIG_CONTROLS_GROUP_ATTR)

    def setup_group(self) -> DagNode | None:
        """Return the setup group node.

        Returns:
            The setup group node, or None if not connected.
        """

        return self.sourceNodeByName(constants.RIG_SETUP_GROUP_ATTR)

    def motion_skeleton(self) -> DagNode | None:
        """Return the motion skeleton root joint.

        Returns:
            The motion skeleton root joint, or None if not connected.
        """

        return self.sourceNodeByName(constants.RIG_MOTION_SKELETON_ATTR)

    def create_transform(
        self, name: str, parent: DagNode | None = None
    ) -> DagNode:
        """Create the root transform node and connect it to this metanode.

        Args:
            name: Name for the transform node.
            parent: Optional parent node.

        Returns:
            The newly created transform node.
        """

        transform = factory.create_dag_node(
            name=name, node_type="transform", parent=parent
        )
        transform.setLockStateOnAttributes(list(constants.TRANSFORM_ATTRS))
        transform.showHideAttributes(list(constants.TRANSFORM_ATTRS))
        self.connect_to(constants.RIG_ROOT_TRANSFORM_ATTR, transform)

        return transform

    def create_controls_group(
        self, name: str, parent: DagNode | None = None
    ) -> DagNode:
        """Create the controls group and connect it to this metanode.

        Args:
            name: Name for the controls group.
            parent: Optional parent node.

        Returns:
            The newly created controls group node.
        """

        existing = self.controls_group()
        if existing is not None:
            return existing

        group = factory.create_dag_node(
            name=name, node_type="transform", parent=parent
        )
        self.connect_to(constants.RIG_CONTROLS_GROUP_ATTR, group)

        return group

    def create_setup_group(
        self, name: str, parent: DagNode | None = None
    ) -> DagNode:
        """Create the setup group and connect it to this metanode.

        Args:
            name: Name for the setup group.
            parent: Optional parent node.

        Returns:
            The newly created setup group node.
        """

        existing = self.setup_group()
        if existing is not None:
            return existing

        group = factory.create_dag_node(
            name=name, node_type="transform", parent=parent
        )
        self.connect_to(constants.RIG_SETUP_GROUP_ATTR, group)

        return group

    def connect_motion_skeleton(self, root_joint: DagNode) -> None:
        """Connect the motion skeleton root joint to this metanode.

        Args:
            root_joint: The root joint of the motion skeleton.
        """

        self.connect_to(constants.RIG_MOTION_SKELETON_ATTR, root_joint)

    # =========================================================================
    # Display Layer Management
    # =========================================================================

    def display_layer(self) -> DisplayLayer | None:
        """Return the control display layer.

        Returns:
            The display layer, or None if not connected.
        """

        source = self.sourceNodeByName(
            constants.RIG_CONTROL_DISPLAY_LAYER_ATTR
        )
        return cast(DisplayLayer, source) if source is not None else None

    def create_display_layer(self, name: str) -> DisplayLayer:
        """Create a display layer for controls and connect it.

        If a display layer already exists, returns the existing one.

        Args:
            name: Name for the display layer.

        Returns:
            The display layer.
        """

        existing = self.display_layer()
        if existing is not None:
            return existing

        layer = cast(DisplayLayer, factory.create_display_layer(name))
        layer.hideOnPlayback.set(True)
        layer.message.connect(
            self.attribute(constants.RIG_CONTROL_DISPLAY_LAYER_ATTR)
        )

        return layer

    def delete_display_layer(self) -> bool:
        """Delete the control display layer.

        Returns:
            True if deleted successfully, False otherwise.
        """

        layer = self.display_layer()
        if layer is not None:
            return layer.delete()

        return False

    # =========================================================================
    # Layer Management
    # =========================================================================

    def create_layer(
        self,
        layer_type: str,
        hierarchy_name: str,
        meta_name: str,
        parent: DagNode | None = None,
    ) -> MetaHumanLayer | None:
        """Create a new layer of the specified type.

        If a layer of this type already exists, returns the existing one.

        Args:
            layer_type: The type identifier of the layer to create.
            hierarchy_name: Name for the layer's transform node.
            meta_name: Name for the layer's metanode.
            parent: Optional parent for the layer's transform.

        Returns:
            The newly created or existing layer, or None if creation failed.
        """

        # Check for existing layer
        existing = self.layer(layer_type)
        if existing is not None:
            return existing

        # Import here to avoid circular imports
        from tp.libs.maya.meta.base import create_meta_node_by_type

        new_layer = cast(
            "MetaHumanLayer",
            create_meta_node_by_type(layer_type, name=meta_name, parent=self),
        )
        if new_layer is None:
            logger.warning(
                f"Failed to create layer of type: {layer_type}. "
                f"Make sure the layer class is registered."
            )
            return None

        new_layer.create_transform(hierarchy_name, parent=parent)
        self.add_meta_child(new_layer)

        return new_layer

    def layer(self, layer_type: str) -> MetaHumanLayer | None:
        """Get a layer by its type identifier.

        Args:
            layer_type: The type identifier of the layer to find.

        Returns:
            The layer if found, None otherwise.
        """

        layers = self.find_children_by_class_type(layer_type, depth_limit=1)
        if not layers:
            return None

        return cast("MetaHumanLayer", layers[0])

    def layers(self) -> list[MetaHumanLayer]:
        """Get all layers attached to this rig.

        Returns:
            List of all layer metanodes.
        """

        # Find all layer types
        layer_types = [
            constants.METAHUMAN_LAYER_TYPE,
            constants.METAHUMAN_CONTROLS_LAYER_TYPE,
            constants.METAHUMAN_SKELETON_LAYER_TYPE,
            constants.METAHUMAN_FKIK_LAYER_TYPE,
            constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE,
            constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE,
        ]

        all_layers: list[MetaHumanLayer] = []
        for layer_type in layer_types:
            found = self.find_children_by_class_type(layer_type, depth_limit=1)
            all_layers.extend(cast(list["MetaHumanLayer"], found))

        return all_layers

    def controls_layer(self) -> MetaHumanLayer | None:
        """Get the controls layer.

        Returns:
            The controls layer if it exists.
        """

        return self.layer(constants.METAHUMAN_CONTROLS_LAYER_TYPE)

    def skeleton_layer(self) -> MetaHumanLayer | None:
        """Get the skeleton layer.

        Returns:
            The skeleton layer if it exists.
        """

        return self.layer(constants.METAHUMAN_SKELETON_LAYER_TYPE)

    def fkik_layer(self) -> MetaHumanLayer | None:
        """Get the FK/IK layer.

        Returns:
            The FK/IK layer if it exists.
        """

        return self.layer(constants.METAHUMAN_FKIK_LAYER_TYPE)

    # =========================================================================
    # Lifecycle Management
    # =========================================================================

    def delete(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Delete the rig and all connected nodes.

        This method cleans up all layers, groups, and the metanode itself.

        Args:
            mod: Optional modifier for batched operations.
            apply: Whether to apply the modifier.

        Returns:
            True if deletion was successful.
        """

        # Delete all layers first
        for layer in self.layers():
            try:
                layer.delete()
            except Exception as e:
                logger.warning(f"Failed to delete layer: {e}")

        # Delete display layer
        self.delete_display_layer()

        # Delete groups (in order: controls, setup, root)
        for group in [
            self.controls_group(),
            self.setup_group(),
            self.root_transform(),
        ]:
            if group is not None:
                try:
                    group.lock(False)
                    group.delete()
                except Exception as e:
                    logger.warning(f"Failed to delete group: {e}")

        return super().delete(mod=mod, apply=apply)
