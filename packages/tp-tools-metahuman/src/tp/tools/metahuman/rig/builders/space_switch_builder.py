"""Space switch builder for MetaHuman rig.

This module provides classes for building space switching systems
for IK controls and pole vectors. Uses tp.libs.maya.wrapper for OpenMaya operations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import maya.cmds as cmds

from ..data.skeleton_config import HAND_SPACE_SWITCH, Side
from ..utils.attribute_utils import (
    add_enum_attribute,
    add_float_attribute,
    connect_attribute,
    delete_if_exists,
)
from ..utils.maya_utils import freeze_transforms

logger = logging.getLogger(__name__)


@dataclass
class SpaceSwitchResult:
    """Result of space switch setup."""

    attribute_name: str
    locators: list[str]
    constraint: str


class SpaceSwitchBuilder:
    """Builder class for creating space switching systems.

    This class handles the creation of space switches for IK controls
    and pole vectors, allowing animators to switch between different
    parent spaces.
    """

    def __init__(self, rig_ctrls_group: str = "rig_ctrls"):
        """Initialize the space switch builder.

        Args:
            rig_ctrls_group: Group for rig controls.
        """
        self.rig_ctrls_group = rig_ctrls_group

    def create_hand_space_switch(self, side: Side) -> SpaceSwitchResult:
        """Create space switch for IK hand control.

        Args:
            side: Body side.

        Returns:
            SpaceSwitchResult with created nodes.
        """

        s = side.value
        ik_ctrl = f"hand_{s}_ik_ctrl"
        ik_offset = f"hand_{s}_ik_offset"
        config = HAND_SPACE_SWITCH

        # Add an enum attribute for space switching.
        enum_attr = add_enum_attribute(
            ik_ctrl,
            long_name="Follow",
            short_name="follow",
            enum_names=config.spaces,
        )

        # Create locators for each space.
        locators = []
        for idx, (space, ctrl) in enumerate(
            zip(config.spaces, config.controls)
        ):
            loc_name = f"{space}_{s}_switch"
            delete_if_exists(loc_name)

            cmds.spaceLocator(name=loc_name)

            # Match to IK control.
            cmds.parentConstraint(
                ik_ctrl,
                loc_name,
                maintainOffset=False,
                name="delete_ParentCon",
            )
            cmds.delete("delete_ParentCon")

            # Parent to space control.
            cmds.parent(loc_name, ctrl)
            cmds.setAttr(f"{loc_name}.visibility", 0)

            locators.append(loc_name)

        # Create the parent constraint with all spaces.
        constraint_name = f"hand_{s}_switch_parentCon"
        cmds.parentConstraint(
            locators, ik_offset, maintainOffset=False, name=constraint_name
        )
        # Set the interpolation type to No Flip (0) to prevent flipping issues.
        cmds.setAttr(f"{constraint_name}.interpType", 0)

        # Get constraint weight attributes.
        constraint_attrs = []
        for attr in cmds.listAttr(constraint_name):
            if "_switchW" in attr:
                constraint_attrs.append(attr)

        # Create set driven keys for space switching.
        self._create_space_driven_keys(
            driver=f"{ik_ctrl}.Follow",
            constraint=constraint_name,
            attrs=constraint_attrs,
            num_spaces=len(config.spaces),
        )

        # Set default to the world.
        cmds.setAttr(f"{ik_ctrl}.Follow", 0)

        return SpaceSwitchResult(
            attribute_name=enum_attr,
            locators=locators,
            constraint=constraint_name,
        )

    @staticmethod
    def create_pole_vector_space_switch(
        side: Side, limb_type: str, ik_ctrl: str
    ) -> str:
        """Create a space switch for pole vector control.

        This creates a simple world/IK control space switch for pole vectors.

        Args:
            side: Body side.
            limb_type: Type of limb ("arm" or "leg").
            ik_ctrl: IK control name.

        Returns:
            Name of the space switch attribute.
        """

        s = side.value
        pv_ctrl = f"{limb_type}_pole_vector_{s}_ctrl"
        pv_offset = f"{limb_type}_pole_vector_{s}_offset"

        # Create locator parented to IK control
        pv_loc = f"{limb_type}_pv_{s}"
        cmds.spaceLocator(name=pv_loc)

        cmds.parentConstraint(
            pv_ctrl, pv_loc, maintainOffset=False, name="delete_con"
        )
        cmds.delete("delete_con")

        cmds.parent(pv_loc, ik_ctrl)
        cmds.setAttr(f"{pv_loc}.visibility", 0)

        # Create an offset-offset group for space switching.
        offset_offset = f"{limb_type}_pole_vector_{s}_offset_offset"
        cmds.group(empty=True, name=offset_offset)

        cmds.parentConstraint(
            pv_ctrl, offset_offset, maintainOffset=False, name="deleteCon"
        )
        cmds.delete("deleteCon")

        freeze_transforms(offset_offset)

        # Reparent
        cmds.parent(offset_offset, pv_offset)
        cmds.parent(pv_ctrl, offset_offset)

        # Create constraint.
        constraint_name = f"{pv_loc}_parentCon"
        cmds.parentConstraint(
            ik_ctrl, offset_offset, maintainOffset=True, name=constraint_name
        )

        # Add a space switch attribute.
        part_type = "hand" if limb_type == "arm" else "foot"
        attr_name = f"space_world_{part_type}_switch"

        add_float_attribute(
            ik_ctrl,
            long_name=attr_name,
            short_name=f"space_world_{part_type}",
            default_value=0.0,
            min_value=0.0,
            max_value=1.0,
        )

        # Connect attribute to constraint weight.
        connect_attribute(
            f"{ik_ctrl}.space_world_{part_type}",
            f"{constraint_name}.{ik_ctrl}W0",
        )

        cmds.setAttr(f"{ik_ctrl}.{attr_name}", 0)

        return attr_name

    @staticmethod
    def _create_space_driven_keys(
        driver: str, constraint: str, attrs: list[str], num_spaces: int
    ) -> None:
        """Create set driven keys for space switching.

        Args:
            driver: Driver attribute.
            constraint: Constraint name.
            attrs: List of constraint weight attributes.
            num_spaces: Number of spaces.
        """

        for driver_val in range(num_spaces):
            for attr_idx in range(len(attrs)):
                # Set weight to 1 if this is the active space, 0 otherwise
                driven_val = 1 if driver_val == attr_idx else 0

                driven_attr = f"{constraint}.{attrs[attr_idx]}"
                cmds.setDrivenKeyframe(
                    driven_attr,
                    currentDriver=driver,
                    driverValue=driver_val,
                    value=driven_val,
                )
