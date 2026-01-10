"""Finger controls builder for MetaHuman rig.

This module provides classes for building finger control systems
with curl and spread functionality. Uses tp.libs.maya.wrapper for OpenMaya operations.
"""

from __future__ import annotations

from dataclasses import dataclass

import maya.cmds as cmds

from ..data.skeleton_config import (
    CONTROL_CONFIGS,
    FINGER_SPREAD_MULTIPLIERS,
    RigColors,
    Side,
)
from ..utils.attribute_utils import (
    ATTR_CONFIG_SWITCH,
    add_float_attribute,
    cleanup_attributes,
    connect_attribute,
    delete_if_exists,
)
from ..utils.maya_utils import (
    create_control_shape,
    freeze_transforms,
    object_exists,
    set_color_override,
)


@dataclass
class FingerControlResult:
    """Result of finger control creation."""

    main_control: str
    finger_offsets: dict[str, list[str]]
    curl_attributes: list[str]
    spread_attribute: str


def _connect_spread_attributes(main_ctrl: str, side: Side) -> None:
    """Connect spread attribute to finger base rotations.

    Args:
        main_ctrl: Name of the main finger control.
        side: Body side.
    """
    s = side.value

    for finger in ["index", "middle", "ring", "pinky"]:
        offset_b = f"{finger}_01_{s}_offsetB"

        if not object_exists(offset_b):
            continue

        multiplier = FINGER_SPREAD_MULTIPLIERS.get(finger, 1.0)

        if finger == "middle":
            # Direct connection for the middle finger.
            connect_attribute(
                f"{main_ctrl}.spread_fingers",
                f"{offset_b}.rotateY",
                force=True,
            )
        else:
            # Use multiply node for the other fingers.
            mult_node = f"{finger}_01_{s}_multiplyDivide"
            delete_if_exists(mult_node)

            cmds.shadingNode("multiplyDivide", asUtility=True, name=mult_node)
            cmds.setAttr(f"{mult_node}.input2X", multiplier)

            connect_attribute(
                f"{main_ctrl}.spread_fingers",
                f"{mult_node}.input1X",
                force=True,
            )
            connect_attribute(
                f"{mult_node}.outputX", f"{offset_b}.rotateY", force=True
            )


class FingerControlBuilder:
    """Builder class for creating finger control systems.

    This class handles the creation of finger controls with curl and spread
    functionality for hand animation.
    """

    def __init__(self, rig_ctrls_group: str = "rig_ctrls"):
        """Initialize the finger control builder.

        Args:
            rig_ctrls_group: Group for rig controls.
        """

        self.rig_ctrls_group = rig_ctrls_group
        self.finger_list = ["thumb", "index", "middle", "ring", "pinky"]

    def build_finger_controls(
        self, side: Side, skel_type: str = "_motion"
    ) -> FingerControlResult:
        """Build a complete finger control system for a hand.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.

        Returns:
            `FingerControlResult` with created controls.
        """

        s = side.value

        # Create the main finger control.
        main_ctrl = self._create_main_finger_control(side, skel_type)

        # Add curl attributes.
        curl_attrs = self._add_curl_attributes(main_ctrl)

        # Add a spread attribute.
        spread_attr = self._add_spread_attribute(main_ctrl)

        # Create offset groups for each finger.
        finger_offsets = self._create_finger_offset_groups(side, skel_type)

        # Connect curl attributes to finger rotations.
        self._connect_curl_attributes(main_ctrl, side, skel_type)

        # Connect spread attributes.
        _connect_spread_attributes(main_ctrl, side)

        # Clean up main control attributes.
        cleanup_attributes(main_ctrl, ATTR_CONFIG_SWITCH)
        cmds.setAttr(
            f"{main_ctrl}.visibility", keyable=False, channelBox=False
        )

        return FingerControlResult(
            main_control=main_ctrl,
            finger_offsets=finger_offsets,
            curl_attributes=curl_attrs,
            spread_attribute=spread_attr,
        )

    def _create_main_finger_control(self, side: Side, skel_type: str) -> str:
        """Create the main finger control.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.

        Returns:
            Name of the created control.
        """

        s = side.value
        ctrl_name = f"fingers_{s}_ctrl"
        config = CONTROL_CONFIGS["fingers"]

        # Create control using configured shape type.
        create_control_shape(ctrl_name, config)

        # Get all shapes for coloring.
        shapes = (
            cmds.listRelatives(ctrl_name, shapes=True, type="nurbsCurve") or []
        )

        # Position at hand.
        cmds.parentConstraint(
            f"hand_{s}{skel_type}",
            ctrl_name,
            maintainOffset=False,
            name="delete_con",
        )
        cmds.delete("delete_con")

        # Fine-tune position at middle fingertip.
        cmds.parentConstraint(
            f"middle_03_{s}_ctrl",
            ctrl_name,
            maintainOffset=False,
            name="delete_con",
        )
        cmds.delete("delete_con")

        # Rotate and scale.
        cmds.setAttr(f"{ctrl_name}.rx", -105)
        cmds.setAttr(f"{ctrl_name}.sx", 0.25)

        # Freeze transforms.
        freeze_transforms(ctrl_name)

        # Constrain to hand.
        cmds.parentConstraint(
            f"hand_{s}{skel_type}",
            ctrl_name,
            maintainOffset=True,
            name=f"{ctrl_name}_con",
        )

        # Parent to rig controls.
        cmds.parent(ctrl_name, self.rig_ctrls_group)

        # Color all shapes.
        color = (
            RigColors.LEFT_BRIGHT
            if side == Side.LEFT
            else RigColors.RIGHT_BRIGHT
        )
        for shape in shapes:
            set_color_override(shape, color)

        return ctrl_name

    def _add_curl_attributes(self, ctrl_name: str) -> list[str]:
        """Add curl attributes to the main finger control.

        Args:
            ctrl_name: Name of the control.

        Returns:
            List of created attribute names.
        """

        curl_attrs = []

        for finger in self.finger_list:
            attr = add_float_attribute(
                ctrl_name,
                long_name=f"{finger}_curl",
                short_name=finger,
                default_value=0.0,
                min_value=-30.0,
                max_value=90.0,
            )
            curl_attrs.append(attr)

        return curl_attrs

    @staticmethod
    def _add_spread_attribute(ctrl_name: str) -> str:
        """Add the spread attribute to the main finger control.

        Args:
            ctrl_name: Name of the control.

        Returns:
            Created attribute name.
        """

        return add_float_attribute(
            ctrl_name,
            long_name="spread_fingers",
            short_name="spread",
            default_value=0.0,
            min_value=-10.0,
            max_value=10.0,
        )

    def _create_finger_offset_groups(
        self, side: Side, skel_type: str
    ) -> dict[str, list[str]]:
        """Create offset groups for each finger joint.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.

        Returns:
            Dictionary mapping finger names to lists of offset group names.
        """

        s = side.value
        finger_offsets: dict[str, list[str]] = {}

        for finger in self.finger_list:
            finger_offsets[finger] = []

            for joint_num in range(1, 3):  # 01 and 02
                joint_name = f"{finger}_0{joint_num}_{s}{skel_type}"
                ctrl_name = f"{finger}_0{joint_num}_{s}_ctrl"
                offset_a = f"{finger}_0{joint_num}_{s}_offsetA"
                offset_b = f"{finger}_0{joint_num}_{s}_offsetB"

                if not object_exists(joint_name):
                    continue

                # Create an offset A if it doesn't exist.
                if not object_exists(offset_a):
                    cmds.group(name=offset_a, empty=True)

                    # Match to joint.
                    cmds.parentConstraint(
                        joint_name,
                        offset_a,
                        maintainOffset=False,
                        name="delete_con",
                    )
                    cmds.delete("delete_con")

                # Parent offset A.
                if joint_num == 1:
                    if finger != "thumb":
                        cmds.parent(offset_a, self.rig_ctrls_group)
                        cmds.parentConstraint(
                            f"{finger}_metacarpal_{s}{skel_type}",
                            offset_a,
                            maintainOffset=True,
                        )
                    else:
                        cmds.parentConstraint(
                            f"hand_{s}{skel_type}",
                            offset_a,
                            maintainOffset=True,
                        )
                        cmds.parent(offset_a, self.rig_ctrls_group)
                else:
                    prev_ctrl = f"{finger}_0{joint_num - 1}_{s}_ctrl"
                    if object_exists(prev_ctrl):
                        cmds.parent(offset_a, prev_ctrl)

                # Create offset B.
                cmds.duplicate(offset_a, name=offset_b, parentOnly=True)
                cmds.parent(offset_b, offset_a)

                # Reparent control to offset B.
                if object_exists(ctrl_name):
                    current_parent = cmds.listRelatives(ctrl_name, parent=True)
                    if not current_parent or current_parent[0] != offset_b:
                        cmds.parent(ctrl_name, offset_b)

                finger_offsets[finger].extend([offset_a, offset_b])

        return finger_offsets

    def _connect_curl_attributes(
        self, main_ctrl: str, side: Side, skel_type: str
    ) -> None:
        """Connect curl attributes to finger offset rotations.

        Args:
            main_ctrl: Name of the main finger control.
            side: Body side.
            skel_type: Skeleton type suffix.
        """

        s = side.value

        for finger in self.finger_list:
            for joint_num in range(1, 3):
                offset_b = f"{finger}_0{joint_num}_{s}_offsetB"

                if object_exists(offset_b):
                    connect_attribute(
                        f"{main_ctrl}.{finger}_curl",
                        f"{offset_b}.rotateZ",
                        force=True,
                    )
