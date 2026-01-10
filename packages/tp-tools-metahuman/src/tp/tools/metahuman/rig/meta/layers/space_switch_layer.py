"""MetaHuman Space Switch Layer metanode class.

This module provides the space switch layer class for MetaHuman body rigs.
The space switch layer manages space switching systems for controls.
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


class MetaHumanSpaceSwitchLayer(MetaHumanLayer):
    """Layer class for MetaHuman space switching systems.

    This layer manages space switch controls and constraints. It tracks
    which controls have space switching enabled and stores the driver
    constraints for each.

    Example:
        >>> # Space switch layers are typically created via the rig
        >>> layer = meta_rig.create_layer(
        ...     METAHUMAN_SPACE_SWITCH_LAYER_TYPE,
        ...     "space_layer",
        ...     "space_meta"
        ... )
        >>> layer.add_space_switch_control(hand_ctrl)
        >>> layer.add_constraint(hand_space_con)
    """

    ID = constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE
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
                    name=constants.SPACE_SWITCH_LAYER_CONTROLS_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.SPACE_SWITCH_LAYER_CONSTRAINTS_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.SPACE_SWITCH_LAYER_DRIVER_NODES_ATTR,
                    isArray=True,
                    type=attributetypes.kMFnMessageAttribute,
                ),
            ]
        )

        return attrs

    # =========================================================================
    # Space Switch Controls
    # =========================================================================

    def add_space_switch_control(self, control: DagNode) -> None:
        """Add a control with space switching to this layer.

        Args:
            control: The control node with space switching.
        """

        plug = self.attribute(constants.SPACE_SWITCH_LAYER_CONTROLS_ATTR)
        next_plug = plug.nextAvailableDestElementPlug()
        self.connect_to_by_plug(next_plug, control)

    def iterate_space_switch_controls(self) -> Generator[DagNode, None, None]:
        """Iterate over all space switch controls.

        Yields:
            Control nodes with space switching.
        """

        plug = self.attribute(constants.SPACE_SWITCH_LAYER_CONTROLS_ATTR)
        for element in plug:
            source = element.sourceNode()
            if source is not None:
                yield source

    def space_switch_controls(self) -> list[DagNode]:
        """Return all space switch controls.

        Returns:
            List of control nodes with space switching.
        """

        return list(self.iterate_space_switch_controls())

    def space_switch_control_count(self) -> int:
        """Return the number of space switch controls.

        Returns:
            Number of space switch controls.
        """

        return len(self.space_switch_controls())

    # =========================================================================
    # Constraints
    # =========================================================================

    def add_constraint(self, constraint: DagNode) -> None:
        """Add a space switch constraint to this layer.

        Args:
            constraint: The constraint node to add.
        """

        plug = self.attribute(constants.SPACE_SWITCH_LAYER_CONSTRAINTS_ATTR)
        next_plug = plug.nextAvailableDestElementPlug()
        self.connect_to_by_plug(next_plug, constraint)

    def iterate_constraints(self) -> Generator[DagNode, None, None]:
        """Iterate over all space switch constraints.

        Yields:
            Constraint nodes.
        """

        plug = self.attribute(constants.SPACE_SWITCH_LAYER_CONSTRAINTS_ATTR)
        for element in plug:
            source = element.sourceNode()
            if source is not None:
                yield source

    def constraints(self) -> list[DagNode]:
        """Return all space switch constraints.

        Returns:
            List of constraint nodes.
        """

        return list(self.iterate_constraints())

    # =========================================================================
    # Driver Nodes
    # =========================================================================

    def add_driver_node(self, driver: DagNode) -> None:
        """Add a driver node (locator/null) for space switching.

        Args:
            driver: The driver node to add.
        """

        plug = self.attribute(constants.SPACE_SWITCH_LAYER_DRIVER_NODES_ATTR)
        next_plug = plug.nextAvailableDestElementPlug()
        self.connect_to_by_plug(next_plug, driver)

    def iterate_driver_nodes(self) -> Generator[DagNode, None, None]:
        """Iterate over all driver nodes.

        Yields:
            Driver nodes.
        """

        plug = self.attribute(constants.SPACE_SWITCH_LAYER_DRIVER_NODES_ATTR)
        for element in plug:
            source = element.sourceNode()
            if source is not None:
                yield source

    def driver_nodes(self) -> list[DagNode]:
        """Return all driver nodes.

        Returns:
            List of driver nodes.
        """

        return list(self.iterate_driver_nodes())

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def delete(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Delete the space switch layer and its constraints.

        Args:
            mod: Optional modifier for batched operations.
            apply: Whether to apply the modifier.

        Returns:
            True if deletion was successful.
        """

        # Delete constraints
        for constraint in self.constraints():
            try:
                constraint.delete()
            except Exception:
                pass

        # Delete driver nodes
        for driver in self.driver_nodes():
            try:
                driver.lock(False)
                driver.delete()
            except Exception:
                pass

        return super().delete(mod=mod, apply=apply)
