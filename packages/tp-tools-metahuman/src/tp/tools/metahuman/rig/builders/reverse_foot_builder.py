"""Reverse foot builder for MetaHuman rig.

This module provides classes for building reverse foot setups with foot roll,
toe twist, and ball lift controls. Uses tp.libs.maya.wrapper for OpenMaya operations.
"""

from __future__ import annotations

from dataclasses import dataclass

import maya.cmds as cmds

from tp.libs.maya import wrapper

from ..data.skeleton_config import (
    CONTROL_CONFIGS,
    FootRollConfig,
    RigColors,
    Side,
)
from ..utils.attribute_utils import (
    add_float_attribute,
    connect_attribute,
    delete_if_exists,
    set_attribute_value_om2,
)
from ..utils.maya_utils import (
    create_offset_group,
    freeze_transforms,
    set_color_override,
)


@dataclass
class FootRollResult:
    """Result of foot roll setup."""

    foot_loc: str
    ball_loc: str
    toe_loc: str
    ball_ik_handle: str
    toe_ik_handle: str
    nodes: dict[str, str]


class ReverseFootBuilder:
    """Builder class for creating reverse foot setups.

    This class handles the creation of reverse foot rigs with foot roll,
    toe twist, and ball lift functionality.
    """

    def __init__(
        self,
        rig_setup_group: str = "rig_setup",
        rig_ctrls_group: str = "rig_ctrls",
    ):
        """Initialize the reverse foot builder.

        Args:
            rig_setup_group: Group for rig setup nodes.
            rig_ctrls_group: Group for rig controls.
        """
        self.rig_setup_group = rig_setup_group
        self.rig_ctrls_group = rig_ctrls_group
        self.config = FootRollConfig()

    def build_reverse_foot(
        self, side: Side, skel_type: str = "_motion"
    ) -> FootRollResult:
        """Build a complete reverse foot setup.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.

        Returns:
            `FootRollResult` with created nodes.
        """

        s = side.value

        # Create locators.
        foot_loc = self._create_foot_locator(side, skel_type)
        ball_loc = self._create_ball_locator(side, skel_type)
        toe_loc = self._create_toe_locator(side, skel_type)

        # Create toe IK joint.
        self._create_toe_ik_joint(side, skel_type)

        # Create IK handles.
        ball_ik = self._create_ball_ik_handle(side, skel_type)
        toe_ik = self._create_toe_ik_handle(side, skel_type)

        # Connect the foot IK handle to the ball locator.
        delete_if_exists(f"foot_{s}_ik_ctrl_parentCon")
        cmds.parentConstraint(
            f"ball_{s}_loc",
            f"foot_{s}_ikHandle",
            maintainOffset=True,
            name=f"foot_{s}_ikHandle_Con",
        )

        # Parent ball offset to toe locator.
        cmds.parent(f"ball_{s}_offset", f"toe_{s}_loc")

        # Add foot roll attributes and nodes.
        nodes = self._setup_foot_roll_nodes(side)

        return FootRollResult(
            foot_loc=foot_loc,
            ball_loc=ball_loc,
            toe_loc=toe_loc,
            ball_ik_handle=ball_ik,
            toe_ik_handle=toe_ik,
            nodes=nodes,
        )

    def _create_foot_locator(self, side: Side, skel_type: str) -> str:
        """Create the foot (heel) locator.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.
        """

        s = side.value
        loc_name = f"foot_{s}_loc"

        cmds.spaceLocator(name=loc_name)

        # Match to foot IK joint.
        cmds.parentConstraint(
            f"foot_{s}_ik{skel_type}",
            loc_name,
            maintainOffset=False,
            name="delete_con",
        )
        cmds.delete("delete_con")

        # Parent to rig setup.
        cmds.parent(loc_name, self.rig_setup_group)

        # Offset to heel position.
        current_y = cmds.getAttr(f"{loc_name}.translateY")
        cmds.setAttr(
            f"{loc_name}.translateY", current_y + self.config.heel_offset
        )
        cmds.setAttr(f"{loc_name}.translateZ", 0)

        freeze_transforms(loc_name)

        # Create the offset group.
        offset_name = f"foot_{s}_offset"
        cmds.group(loc_name, name=offset_name)

        # Constrain offset to IK control.
        cmds.parentConstraint(
            f"foot_{s}_ik_ctrl", offset_name, maintainOffset=True
        )

        return loc_name

    @staticmethod
    def _create_ball_locator(side: Side, skel_type: str) -> str:
        """Create the ball locator.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.
        """

        s = side.value
        loc_name = f"ball_{s}_loc"

        cmds.spaceLocator(name=loc_name)

        # Match to ball IK joint.
        cmds.parentConstraint(
            f"ball_{s}_ik{skel_type}",
            loc_name,
            maintainOffset=False,
            name="delete_con",
        )
        cmds.delete("delete_con")

        # Parent to foot locator.
        cmds.parent(loc_name, f"foot_{s}_loc")

        freeze_transforms(loc_name)

        # Create an offset group.
        cmds.group(loc_name, name=f"ball_{s}_offset")

        return loc_name

    def _create_toe_locator(self, side: Side, skel_type: str) -> str:
        """Create the toe locator.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.
        """

        s = side.value
        loc_name = f"toe_{s}_loc"

        cmds.spaceLocator(name=loc_name)

        # Match to ball IK joint (toe tip is forward of ball).
        cmds.parentConstraint(
            f"ball_{s}_ik{skel_type}",
            loc_name,
            maintainOffset=False,
            name="delete_con",
        )
        cmds.delete("delete_con")

        # Parent to foot locator.
        cmds.parent(loc_name, f"foot_{s}_loc")

        # Offset to the toe tip position.
        current_y = cmds.getAttr(f"{loc_name}.translateY")
        cmds.setAttr(
            f"{loc_name}.translateY", current_y + self.config.toe_offset
        )
        cmds.setAttr(f"{loc_name}.translateZ", 0)

        freeze_transforms(loc_name)

        # Create an offset group.
        cmds.group(loc_name, name=f"toe_{s}_offset")

        return loc_name

    @staticmethod
    def _create_toe_ik_joint(side: Side, skel_type: str) -> str:
        """Create the toe IK joint for the reverse foot.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.
        """

        s = side.value
        joint_name = f"toe_{s}_ik{skel_type}"

        cmds.joint(name=joint_name, position=(0, 0, 0))

        # Match to toe offset
        cmds.parentConstraint(
            f"toe_{s}_offset",
            joint_name,
            maintainOffset=False,
            name="delete_con",
        )
        cmds.delete("delete_con")

        # Parent to ball IK joint.
        cmds.parent(joint_name, f"ball_{s}_ik{skel_type}")

        return joint_name

    @staticmethod
    def _create_ball_ik_handle(side: Side, skel_type: str) -> str:
        """Create an IK handle for the ball.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.
        """

        s = side.value
        handle_name = f"ball_rev_{s}_ikHandle"

        cmds.ikHandle(
            startJoint=f"foot_{s}_ik{skel_type}",
            endEffector=f"ball_{s}_ik{skel_type}",
            priority=2,
            weight=0.5,
            sticky="sticky",
            name=handle_name,
        )

        cmds.parent(handle_name, f"ball_{s}_loc")

        return handle_name

    @staticmethod
    def _create_toe_ik_handle(side: Side, skel_type: str) -> str:
        """Create an IK handle for toe.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.
        """

        s = side.value
        handle_name = f"toe_rev_{s}_ikHandle"

        cmds.ikHandle(
            startJoint=f"ball_{s}_ik{skel_type}",
            endEffector=f"toe_{s}_ik{skel_type}",
            priority=2,
            weight=0.5,
            sticky="sticky",
            name=handle_name,
        )

        cmds.parent(handle_name, f"foot_{s}_loc")

        return handle_name

    def _setup_foot_roll_nodes(self, side: Side) -> dict[str, str]:
        """Set up the foot roll attribute and node network.

        Args:
            side: Body side.

        Returns:
            Dictionary of created node names.
        """

        s = side.value
        ctrl_name = f"foot_{s}_ik_ctrl"
        nodes = {}

        # Add custom attributes
        add_float_attribute(
            ctrl_name,
            "Roll",
            "Roll",
            default_value=0.0,
            min_value=self.config.roll_min,
            max_value=self.config.roll_max,
        )

        add_float_attribute(
            ctrl_name,
            "Bend_Limit_Angle",
            "BendLimitAngle",
            default_value=self.config.bend_limit_angle,
            min_value=-180.0,
            max_value=180.0,
            locked=True,
        )

        add_float_attribute(
            ctrl_name,
            "Toe_Straight",
            "ToeStraight",
            default_value=self.config.toe_straight_angle,
            min_value=-180.0,
            max_value=180.0,
            locked=True,
        )

        # Create a foot rotation clamp (heel roll).
        nodes["foot_rot_clamp"] = self._create_node_if_not_exists(
            f"foot_rot_clamp_{s}", "clamp"
        )
        self._set_node_attr_om2(nodes["foot_rot_clamp"], "minR", -90)
        self._set_node_attr_om2(nodes["foot_rot_clamp"], "maxR", 0)
        connect_attribute(
            f"{ctrl_name}.Roll", f"{nodes['foot_rot_clamp']}.inputR"
        )
        connect_attribute(
            f"{nodes['foot_rot_clamp']}.outputR", f"foot_{s}_loc.rotateX"
        )

        # Ball zero to blend clamp.
        nodes["ball_clamp"] = self._create_node_if_not_exists(
            f"ball_zeroToBlend_clamp_{s}", "clamp"
        )
        self._set_node_attr_om2(nodes["ball_clamp"], "minR", 0)
        connect_attribute(f"{ctrl_name}.Roll", f"{nodes['ball_clamp']}.inputR")
        connect_attribute(
            f"{ctrl_name}.Bend_Limit_Angle", f"{nodes['ball_clamp']}.maxR"
        )

        # Toe set range (zero to bend percent).
        nodes["toe_range_zero"] = self._create_node_if_not_exists(
            f"toe_setRange_zeroToBendPercent{s}", "setRange"
        )
        connect_attribute(
            f"{nodes['ball_clamp']}.minR", f"{nodes['toe_range_zero']}.oldMinX"
        )
        connect_attribute(
            f"{nodes['ball_clamp']}.maxR", f"{nodes['toe_range_zero']}.oldMaxX"
        )
        self._set_node_attr_om2(nodes["toe_range_zero"], "maxX", 1)
        self._set_node_attr_om2(nodes["toe_range_zero"], "minX", 0)
        connect_attribute(
            f"{nodes['ball_clamp']}.inputR",
            f"{nodes['toe_range_zero']}.valueX",
        )

        # Toe rotation clamp.
        nodes["toe_rot_clamp"] = self._create_node_if_not_exists(
            f"toe_rot_clamp_{s}", "clamp"
        )
        connect_attribute(
            f"{ctrl_name}.Bend_Limit_Angle", f"{nodes['toe_rot_clamp']}.minR"
        )
        connect_attribute(
            f"{ctrl_name}.Toe_Straight", f"{nodes['toe_rot_clamp']}.maxR"
        )
        connect_attribute(
            f"{ctrl_name}.Roll", f"{nodes['toe_rot_clamp']}.inputR"
        )

        # Toe set range (bend to straight percent).
        nodes["toe_range_bend"] = self._create_node_if_not_exists(
            f"toe_setRange_bendToStraightPercent_{s}", "setRange"
        )
        connect_attribute(
            f"{nodes['toe_rot_clamp']}.minR",
            f"{nodes['toe_range_bend']}.oldMinX",
        )
        connect_attribute(
            f"{nodes['toe_rot_clamp']}.maxR",
            f"{nodes['toe_range_bend']}.oldMaxX",
        )
        self._set_node_attr_om2(nodes["toe_range_bend"], "maxX", 1)
        self._set_node_attr_om2(nodes["toe_range_bend"], "minX", 0)
        connect_attribute(
            f"{nodes['toe_rot_clamp']}.inputR",
            f"{nodes['toe_range_bend']}.valueX",
        )

        # Toe invert percentage.
        nodes["toe_invert"] = self._create_node_if_not_exists(
            f"toe_invertPercentage_{s}", "plusMinusAverage"
        )
        # For array attributes, we still need cmds.
        cmds.setAttr(f"{nodes['toe_invert']}.input1D[0]", 1)
        self._set_node_attr_om2(
            nodes["toe_invert"], "operation", 2
        )  # Subtract
        connect_attribute(
            f"{nodes['toe_range_bend']}.outValueX",
            f"{nodes['toe_invert']}.input1D[1]",
        )

        # Ball percent multiply.
        nodes["ball_percent_mult"] = self._create_node_if_not_exists(
            f"ball_percentMult_multiplydivide_{s}", "multiplyDivide"
        )
        connect_attribute(
            f"{nodes['toe_range_zero']}.outValueX",
            f"{nodes['ball_percent_mult']}.input1X",
        )
        connect_attribute(
            f"{nodes['toe_invert']}.output1D",
            f"{nodes['ball_percent_mult']}.input2X",
        )

        # Ball roll multiply.
        nodes["ball_roll_mult"] = self._create_node_if_not_exists(
            f"ball_rollMult_multiplydivide_{s}", "multiplyDivide"
        )
        connect_attribute(
            f"{nodes['ball_percent_mult']}.outputX",
            f"{nodes['ball_roll_mult']}.input1X",
        )
        connect_attribute(
            f"{ctrl_name}.Roll", f"{nodes['ball_roll_mult']}.input2X"
        )
        connect_attribute(
            f"{nodes['ball_roll_mult']}.outputX", f"ball_{s}_loc.rotateX"
        )

        # Toe rotation multiply.
        nodes["toe_rot_mult"] = self._create_node_if_not_exists(
            f"toe_rot_multiplydivide_{s}", "multiplyDivide"
        )
        connect_attribute(
            f"{nodes['toe_range_bend']}.outValueX",
            f"{nodes['toe_rot_mult']}.input1X",
        )
        connect_attribute(
            f"{nodes['toe_rot_clamp']}.inputR",
            f"{nodes['toe_rot_mult']}.input2X",
        )
        connect_attribute(
            f"{nodes['toe_rot_mult']}.outputX", f"toe_{s}_loc.rotateX"
        )

        return nodes

    @staticmethod
    def _create_node_if_not_exists(name: str, node_type: str) -> str:
        """Create a utility node if it doesn't exist.

        Args:
            name: Node name.
            node_type: Type of node to create.

        Returns:
            Node name.
        """
        delete_if_exists(name)

        # Create using wrapper
        node = wrapper.DGNode()
        node.create(name, node_type)
        return node.name()

    @staticmethod
    def _set_node_attr_om2(node_name: str, attr: str, value: float) -> None:
        """Set a node attribute value using wrapper.

        Args:
            node_name: Node name.
            attr: Attribute name.
            value: Value to set.
        """
        set_attribute_value_om2(node_name, attr, value)

    def create_toe_twist_control(self, side: Side) -> str:
        """Create toe twist control.

        Args:
            side: Body side.

        Returns:
            Name of the created control.
        """
        s = side.value
        ctrl_name = f"toe_twist_{s}_ik_ctrl"
        config = CONTROL_CONFIGS["toe_twist"]

        # Create circle.
        cmds.circle(
            name=ctrl_name, normal=(0, 0, 1), radius=config.radius, tolerance=0
        )

        shape = f"{ctrl_name}Shape"
        cmds.setAttr(f"{shape}.lineWidth", config.line_width)

        # Set to a polygon shape.
        make_node = self._find_make_node(ctrl_name, "makeNurbCircle")
        if make_node:
            cmds.setAttr(f"{make_node}.degree", 1)
            cmds.setAttr(f"{make_node}.sections", 6)

        # Color.
        color = (
            RigColors.LEFT_BRIGHT
            if side == Side.LEFT
            else RigColors.RIGHT_BRIGHT
        )
        set_color_override(shape, color)

        # Position.
        cmds.parentConstraint(
            f"toe_{s}_loc", ctrl_name, maintainOffset=False, name="delete_con"
        )
        cmds.delete("delete_con")
        cmds.delete(ctrl_name, constructionHistory=True)

        # Create offset.
        offset_name = f"toe_twist_{s}_ik_offset"
        create_offset_group(ctrl_name, offset_name)

        # Constrain offset to toe locator.
        cmds.parentConstraint(
            f"toe_{s}_loc",
            offset_name,
            maintainOffset=True,
            name=f"{offset_name}_con",
        )

        cmds.parent(offset_name, self.rig_ctrls_group)

        # Connect rotation.
        connect_attribute(f"{ctrl_name}.rotateZ", f"toe_{s}_loc.rotateZ")

        # Lock unused attributes.
        for axis in ["X", "Y"]:
            cmds.setAttr(f"{ctrl_name}.translate{axis}", keyable=False)
            cmds.setAttr(
                f"{ctrl_name}.rotate{axis}",
                lock=True,
                keyable=False,
                channelBox=False,
            )
        cmds.setAttr(f"{ctrl_name}.translateZ", keyable=False)

        return ctrl_name

    def create_ball_lift_control(
        self, side: Side, skel_type: str = "_motion"
    ) -> str:
        """Create ball lift control for IK toe rotation.

        Args:
            side: Body side.
            skel_type: Skeleton type suffix.

        Returns:
            Name of the created control.
        """

        s = side.value
        ctrl_name = f"ball_lift_{s}_ik_ctrl"
        ball_lift_joint = f"ball_lift_{s}_ik{skel_type}"
        config = CONTROL_CONFIGS["ball_lift"]

        # Duplicate ball IK joint for ball lift.
        cmds.duplicate(
            f"ball_{s}_ik{skel_type}",
            name=ball_lift_joint,
            renameChildren=True,
        )

        # Clean up duplicated children.
        children = cmds.listRelatives(ball_lift_joint) or []
        for child in children:
            if "effector" in child:
                cmds.delete(child)

        # Rename toe child.
        remaining_children = (
            cmds.listRelatives(ball_lift_joint, children=True) or []
        )
        if remaining_children:
            cmds.rename(
                remaining_children[0], ball_lift_joint.replace("ball_", "toe_")
            )

        # Parent to rig setup.
        cmds.parent(ball_lift_joint, self.rig_setup_group)

        # Create offset for ball lift joint
        joint_offset = f"{ball_lift_joint}_offset"
        create_offset_group(ball_lift_joint, joint_offset)
        cmds.parentConstraint(
            f"ball_{s}_ik{skel_type}",
            joint_offset,
            maintainOffset=True,
            name=f"{joint_offset}_con",
        )

        # Create control.
        cmds.circle(
            name=ctrl_name, normal=(0, 0, 1), radius=config.radius, tolerance=0
        )

        shape = f"{ctrl_name}Shape"
        cmds.setAttr(f"{shape}.lineWidth", config.line_width)

        # Set to a polygon shape.
        make_node = self._find_make_node(ctrl_name, "makeNurbCircle")
        if make_node:
            cmds.setAttr(f"{make_node}.degree", 1)
            cmds.setAttr(f"{make_node}.sections", 6)

        # Rotate shape.
        cmds.setAttr(f"{ctrl_name}.ry", 90)
        freeze_transforms(ctrl_name)

        # Color.
        color = (
            RigColors.LEFT_BRIGHT
            if side == Side.LEFT
            else RigColors.RIGHT_BRIGHT
        )
        set_color_override(shape, color)

        # Position.
        cmds.parentConstraint(
            f"ball_{s}_fk_ctrl",
            ctrl_name,
            maintainOffset=False,
            name="delete_con",
        )
        cmds.delete("delete_con")
        cmds.delete(ctrl_name, constructionHistory=True)

        # Parent and create offset.
        cmds.parent(ctrl_name, self.rig_ctrls_group)
        offset_name = f"ball_lift_{s}_ik_offset"
        create_offset_group(ctrl_name, offset_name)

        # Constrain offset.
        delete_if_exists(f"{offset_name}_parentCon")
        cmds.parentConstraint(
            f"ball_{s}_ik{skel_type}",
            offset_name,
            maintainOffset=True,
            name=f"{offset_name}_parentCon",
        )

        # Orient constraint to ball lift joint.
        cmds.orientConstraint(
            ctrl_name,
            ball_lift_joint,
            maintainOffset=True,
            name=f"{ctrl_name}_orient_con",
        )

        # Lock unused attributes.
        for axis in ["X", "Y", "Z"]:
            cmds.setAttr(
                f"{ctrl_name}.translate{axis}", keyable=False, channelBox=False
            )
        for axis in ["X", "Y"]:
            cmds.setAttr(
                f"{ctrl_name}.rotate{axis}",
                lock=True,
                keyable=False,
                channelBox=False,
            )

        return ctrl_name

    @staticmethod
    def _find_make_node(node: str, node_type: str) -> str | None:
        """Find a make node in history.

        Args:
            node: Node name.
            node_type: Node type.
        """

        history = cmds.listHistory(node) or []
        for input_node in history:
            if node_type in str(input_node):
                return str(input_node)

        return None
