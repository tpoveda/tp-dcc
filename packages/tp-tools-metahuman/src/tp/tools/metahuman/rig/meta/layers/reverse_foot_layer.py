"""MetaHuman Reverse Foot Layer metanode class.

This module provides the reverse foot layer class for MetaHuman body rigs.
The reverse foot layer manages reverse foot IK systems for leg controls.
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


class MetaHumanReverseFootLayer(MetaHumanLayer):
    """Layer class for MetaHuman reverse foot systems.

    This layer manages reverse foot IK controls for leg rigs. It tracks
    the foot IK control, toe controls, heel pivots, and other reverse
    foot components.

    Example:
        >>> # Reverse foot layers are typically created via the rig
        >>> layer = meta_rig.create_layer(
        ...     METAHUMAN_REVERSE_FOOT_LAYER_TYPE,
        ...     "reverse_foot_layer",
        ...     "reverse_foot_meta"
        ... )
        >>> layer.add_foot_control(foot_ik_ctrl)
        >>> layer.add_pivot_locator(heel_pivot)
    """

    ID = constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE
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
                    name=constants.REVERSE_FOOT_LAYER_FOOT_CONTROLS_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.REVERSE_FOOT_LAYER_PIVOT_LOCATORS_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.REVERSE_FOOT_LAYER_IK_HANDLES_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.REVERSE_FOOT_LAYER_SETTINGS_NODE_ATTR,
                    type=attributetypes.kMFnMessageAttribute,
                ),
            ]
        )

        return attrs

    # =========================================================================
    # Foot Controls
    # =========================================================================

    def add_foot_control(self, control: DagNode) -> None:
        """Add a foot IK control to this layer.

        Args:
            control: The foot IK control node to add.
        """

        plug = self.attribute(constants.REVERSE_FOOT_LAYER_FOOT_CONTROLS_ATTR)
        next_plug = plug.nextAvailableDestElementPlug()
        self.connect_to_by_plug(next_plug, control)

    def iterate_foot_controls(self) -> Generator[DagNode, None, None]:
        """Iterate over all foot IK controls.

        Yields:
            Foot IK control nodes.
        """

        plug = self.attribute(constants.REVERSE_FOOT_LAYER_FOOT_CONTROLS_ATTR)
        for element in plug:
            source = element.sourceNode()
            if source is not None:
                yield source

    def foot_controls(self) -> list[DagNode]:
        """Return all foot IK controls.

        Returns:
            List of foot IK control nodes.
        """

        return list(self.iterate_foot_controls())

    def foot_control_count(self) -> int:
        """Return the number of foot IK controls.

        Returns:
            Number of foot IK controls.
        """

        return len(self.foot_controls())

    # =========================================================================
    # Pivot Locators
    # =========================================================================

    def add_pivot_locator(self, locator: DagNode) -> None:
        """Add a pivot locator (heel, toe, ball) to this layer.

        Args:
            locator: The pivot locator node to add.
        """

        plug = self.attribute(constants.REVERSE_FOOT_LAYER_PIVOT_LOCATORS_ATTR)
        next_plug = plug.nextAvailableDestElementPlug()
        self.connect_to_by_plug(next_plug, locator)

    def iterate_pivot_locators(self) -> Generator[DagNode, None, None]:
        """Iterate over all pivot locators.

        Yields:
            Pivot locator nodes.
        """

        plug = self.attribute(constants.REVERSE_FOOT_LAYER_PIVOT_LOCATORS_ATTR)
        for element in plug:
            source = element.sourceNode()
            if source is not None:
                yield source

    def pivot_locators(self) -> list[DagNode]:
        """Return all pivot locators.

        Returns:
            List of pivot locator nodes.
        """

        return list(self.iterate_pivot_locators())

    # =========================================================================
    # IK Handles
    # =========================================================================

    def add_ik_handle(self, ik_handle: DagNode) -> None:
        """Add an IK handle to this layer.

        Args:
            ik_handle: The IK handle node to add.
        """

        plug = self.attribute(constants.REVERSE_FOOT_LAYER_IK_HANDLES_ATTR)
        next_plug = plug.nextAvailableDestElementPlug()
        self.connect_to_by_plug(next_plug, ik_handle)

    def iterate_ik_handles(self) -> Generator[DagNode, None, None]:
        """Iterate over all IK handles.

        Yields:
            IK handle nodes.
        """

        plug = self.attribute(constants.REVERSE_FOOT_LAYER_IK_HANDLES_ATTR)
        for element in plug:
            source = element.sourceNode()
            if source is not None:
                yield source

    def ik_handles(self) -> list[DagNode]:
        """Return all IK handles.

        Returns:
            List of IK handle nodes.
        """

        return list(self.iterate_ik_handles())

    # =========================================================================
    # Settings Node
    # =========================================================================

    def settings_node(self) -> DagNode | None:
        """Return the reverse foot settings node.

        Returns:
            The settings node, or None if not connected.
        """

        return self.sourceNodeByName(
            constants.REVERSE_FOOT_LAYER_SETTINGS_NODE_ATTR
        )

    def connect_settings_node(self, node: DagNode) -> None:
        """Connect the reverse foot settings node.

        Args:
            node: The settings node to connect.
        """

        self.connect_to(constants.REVERSE_FOOT_LAYER_SETTINGS_NODE_ATTR, node)

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def delete(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Delete the reverse foot layer and its components.

        Args:
            mod: Optional modifier for batched operations.
            apply: Whether to apply the modifier.

        Returns:
            True if deletion was successful.
        """

        settings = self.settings_node()
        if settings is not None:
            try:
                settings.lock(False)
                settings.delete()
            except Exception:
                pass

        # Delete IK handles
        for ik_handle in self.ik_handles():
            try:
                ik_handle.delete()
            except Exception:
                pass

        # Delete pivot locators
        for locator in self.pivot_locators():
            try:
                locator.lock(False)
                locator.delete()
            except Exception:
                pass

        return super().delete(mod=mod, apply=apply)
