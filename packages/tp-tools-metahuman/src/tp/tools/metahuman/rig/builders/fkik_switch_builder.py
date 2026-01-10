"""FK/IK switch builder for MetaHuman rig.

This module provides classes for building FK/IK switch controls
and their connection systems. Uses tp.libs.maya.wrapper for OpenMaya operations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import maya.cmds as cmds

from ..data.skeleton_config import RigColors, Side
from ..utils.attribute_utils import (
    ATTR_CONFIG_SWITCH,
    add_float_attribute,
    cleanup_attributes,
    connect_attribute,
    delete_if_exists,
)
from ..utils.maya_utils import (
    freeze_transforms,
    object_exists,
    set_color_override,
)

logger = logging.getLogger(__name__)


# Mapping of limb parts to their FK/IK switch control.
LIMB_PART_TO_SWITCH: dict[str, str] = {
    "upperarm": "hand",
    "lowerarm": "hand",
    "hand": "hand",
    "thigh": "foot",
    "calf": "foot",
    "foot": "foot",
    "ball": "foot",
}


@dataclass
class FKIKSwitchResult:
    """Result of FK/IK switch creation."""

    switch_control: str
    switch_attribute: str
    nodes: dict[str, str]


class FKIKSwitchBuilder:
    """Builder class for creating FK/IK switch systems.

    This class handles the creation of FK/IK switch controls and their
    connection nodes for blending between FK and IK modes.
    """

    def __init__(self, rig_ctrls_group: str = "rig_ctrls"):
        """Initialize the FK/IK switch builder.

        Args:
            rig_ctrls_group: Group for rig controls.
        """
        self.rig_ctrls_group = rig_ctrls_group

    def create_arm_switch(
        self, side: Side, skel_type: str = "_motion"
    ) -> FKIKSwitchResult:
        """Create FK/IK switch for the arm.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.

        Returns:
            FKIKSwitchResult with created nodes.
        """

        return self._create_limb_switch(
            side=side,
            limb_type="hand",
            position_joint=f"upperarm_{side.value}_fk{skel_type}",
            parent_joint=f"spine_01{skel_type}",
        )

    def create_leg_switch(
        self, side: Side, skel_type: str = "_motion"
    ) -> FKIKSwitchResult:
        """Create FK/IK switch for the leg.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.

        Returns:
            `FKIKSwitchResult` with created nodes.
        """

        return self._create_limb_switch(
            side=side,
            limb_type="foot",
            position_joint=f"thigh_{side.value}_fk{skel_type}",
            parent_joint=f"spine_05{skel_type}",
        )

    def _create_limb_switch(
        self,
        side: Side,
        limb_type: str,
        position_joint: str,
        parent_joint: str,
    ) -> FKIKSwitchResult:
        """Create a limb FK/IK switch control.

        Args:
            side: Body side.
            limb_type: Type of limb ("hand" or "foot").
            position_joint: Joint to position the switch near.
            parent_joint: Joint to constrain the switch to.

        Returns:
            `FKIKSwitchResult` with created nodes.
        """

        s = side.value
        switch_name = f"{limb_type}_fkik_{s}_switch"

        # Create an empty group if needed.
        if not object_exists(switch_name):
            cmds.group(name=switch_name, empty=True)

        # Create text curves for the switch.
        cmds.textCurves(text="+", name=switch_name, object=True)

        # Parent shape nodes to the switch.
        shape_parent = f"{switch_name}Shape"
        if object_exists(shape_parent):
            shapes = cmds.listRelatives(
                shape_parent, allDescendents=True, type="nurbsCurve"
            )
            if shapes:
                for shape in shapes:
                    cmds.parent(shape, switch_name, shape=True, relative=True)
            cmds.delete(shape_parent)

        # Colorize the switch based on side.
        color = (
            RigColors.LEFT_BRIGHT
            if side == Side.LEFT
            else RigColors.RIGHT_BRIGHT
        )
        switch_shapes = cmds.listRelatives(
            switch_name, shapes=True, type="nurbsCurve"
        )
        if switch_shapes:
            for shape in switch_shapes:
                set_color_override(shape, color)

        # Center the pivot point to the control.
        cmds.xform(switch_name, centerPivots=True)

        # Rotate 90 degrees on X.
        cmds.setAttr(f"{switch_name}.rx", 90)

        # Freeze transforms FIRST (before positioning).
        freeze_transforms(switch_name)

        # Now position to joint using parentConstraint.
        cmds.parentConstraint(
            position_joint,
            switch_name,
            maintainOffset=False,
            name="delete_con",
        )
        cmds.delete("delete_con")

        # Apply scale.
        cmds.setAttr(f"{switch_name}.sx", 10)
        cmds.setAttr(f"{switch_name}.sy", 10)
        cmds.setAttr(f"{switch_name}.sz", 10)

        # Offset position based on the side.
        offset = 30 if side == Side.LEFT else -30
        cmds.setAttr(f"{switch_name}.tx", offset)

        # Freeze transforms again.
        freeze_transforms(switch_name)

        # Parent and constrain
        cmds.parent(switch_name, self.rig_ctrls_group)
        cmds.parentConstraint(
            parent_joint,
            switch_name,
            maintainOffset=True,
            name=f"{switch_name}_parentCon",
        )

        # Add FK/IK attribute.
        attr_name = add_float_attribute(
            switch_name,
            long_name="limb_fkik_switch",
            short_name="limb_fk_ik",
            default_value=0.0,
            min_value=0.0,
            max_value=1.0,
        )

        # Clean up attributes.
        cleanup_attributes(switch_name, ATTR_CONFIG_SWITCH)

        # Set attribute to be keyable.
        cmds.setAttr(
            f"{switch_name}.limb_fkik_switch", keyable=True, channelBox=True
        )

        return FKIKSwitchResult(
            switch_control=switch_name, switch_attribute=attr_name, nodes={}
        )

    @staticmethod
    def connect_fkik_blend(
        part: str, side: Side, skel_type: str = "_motion"
    ) -> dict[str, str]:
        """Connect FK/IK blend for a limb part.

        Args:
            part: Limb part name (e.g., "upperarm", "hand").
            side: Body side.
            skel_type: Skeleton type suffix.

        Returns:
            Dictionary of created node names.
        """

        s = side.value
        switch_type = LIMB_PART_TO_SWITCH.get(part, "hand")
        switch_name = f"{switch_type}_fkik_{s}_switch"
        constraint_name = f"{part}_{s}_ikfk{skel_type}_orient_con"

        nodes = {}

        # Create plus minus average node for FK weight (1 - IK weight).
        pmavg_name = f"plusMinusAverage_{part}_{s}"
        delete_if_exists(pmavg_name)
        pmavg = cmds.shadingNode(
            "plusMinusAverage", asUtility=True, name=pmavg_name
        )
        cmds.setAttr(f"{pmavg}.operation", 2)  # Subtract.
        nodes["plusMinusAverage"] = pmavg

        # Create float constant node (value of 1).
        float_const_name = f"floatConstant_{part}_{s}"
        delete_if_exists(float_const_name)
        float_const = cmds.shadingNode(
            "floatConstant", asUtility=True, name=float_const_name
        )
        nodes["floatConstant"] = float_const

        # Connect nodes.
        connect_attribute(f"{float_const}.outFloat", f"{pmavg}.input1D[0]")

        # Connect switch to IK weight.
        ik_joint = f"{part}_{s}_ik{skel_type}"
        fk_joint = f"{part}_{s}_fk{skel_type}"

        connect_attribute(
            f"{switch_name}.limb_fkik_switch",
            f"{constraint_name}.{ik_joint}W0",
        )

        # Connect `plusMinusAverage` output to FK weight.
        connect_attribute(
            f"{pmavg}.output1D", f"{constraint_name}.{fk_joint}W1"
        )

        # Connect switch to `plusMinusAverage` input.
        connect_attribute(
            f"{switch_name}.limb_fkik_switch", f"{pmavg}.input1D[1]"
        )

        # Connect visibility for FK control offset.
        fk_offset = f"{part}_{s}_fk_offset"
        if object_exists(fk_offset):
            connect_attribute(f"{pmavg}.output1D", f"{fk_offset}.visibility")

        # Connect visibility for IK control offset.
        ik_offset = f"{part}_{s}_ik_offset"
        if object_exists(ik_offset):
            connect_attribute(
                f"{switch_name}.limb_fkik_switch", f"{ik_offset}.visibility"
            )

        return nodes

    def connect_all_fkik_blends(
        self, side: Side, skel_type: str = "_motion"
    ) -> dict[str, dict[str, str]]:
        """Connect FK/IK blends for all limb parts on a side.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.

        Returns:
            Dictionary mapping part names to their created nodes.
        """

        all_nodes: dict[str, dict[str, str]] = {}

        # Arm parts
        for part in ["upperarm", "lowerarm", "hand"]:
            all_nodes[part] = self.connect_fkik_blend(part, side, skel_type)

        # Leg parts
        for part in ["thigh", "calf", "foot", "ball"]:
            all_nodes[part] = self.connect_fkik_blend(part, side, skel_type)

        return all_nodes

    @staticmethod
    def connect_pole_vector_visibility(side: Side) -> None:
        """Connect pole vector visibility to FK/IK switch.

        Args:
            side: Body side.
        """

        s = side.value

        # Arm pole vector.
        arm_pv_offset = f"arm_pole_vector_{s}_offset"
        if object_exists(arm_pv_offset):
            connect_attribute(
                f"hand_fkik_{s}_switch.limb_fkik_switch",
                f"{arm_pv_offset}.visibility",
            )

        # Leg pole vector.
        leg_pv_offset = f"leg_pole_vector_{s}_offset"
        if object_exists(leg_pv_offset):
            connect_attribute(
                f"foot_fkik_{s}_switch.limb_fkik_switch",
                f"{leg_pv_offset}.visibility",
            )

        # Hide pole vector match controls.
        arm_pv_match = f"arm_pole_vector_{s}_match_offset"
        if object_exists(arm_pv_match):
            cmds.setAttr(f"{arm_pv_match}.visibility", 0)

        leg_pv_match = f"leg_pole_vector_{s}_match_offset"
        if object_exists(leg_pv_match):
            cmds.setAttr(f"{leg_pv_match}.visibility", 0)

    @staticmethod
    def set_default_fkik_states(side: Side) -> None:
        """Set default FK/IK states.

        Args:
            side: Body side.
        """

        s = side.value

        # Set arm to FK by default.
        hand_switch = f"hand_fkik_{s}_switch"
        if object_exists(hand_switch):
            cmds.setAttr(f"{hand_switch}.limb_fkik_switch", channelBox=True)
            cmds.setAttr(f"{hand_switch}.limb_fkik_switch", 0)

        # Set leg to IK by default.
        foot_switch = f"foot_fkik_{s}_switch"
        if object_exists(foot_switch):
            cmds.setAttr(f"{foot_switch}.limb_fkik_switch", channelBox=True)
            cmds.setAttr(f"{foot_switch}.limb_fkik_switch", 1)
