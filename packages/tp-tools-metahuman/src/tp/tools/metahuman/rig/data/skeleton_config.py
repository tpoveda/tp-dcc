"""MetaHuman skeleton configuration data.

This module contains all the data-driven configuration for MetaHuman skeleton
joint definitions, control radii, colors, and other rig-related constants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple


class Side(Enum):
    """Enumeration for body sides."""

    LEFT = "l"
    RIGHT = "r"
    CENTER = "c"


class RigType(Enum):
    """Enumeration for rig types (FK/IK)."""

    FK = "fk"
    IK = "ik"


class ShapeType(Enum):
    """Enumeration for control shape types."""

    CIRCLE = "circle"
    SQUARE = "square"
    CUBE = "cube"
    SPHERE = "sphere"
    DIAMOND = "diamond"
    ARROW = "arrow"
    CROSS = "cross"
    COG = "cog"
    LOCATOR = "locator"
    FOUR_ARROW = "four_arrow"
    DIRECTION_ARROW = "direction_arrow"
    HAND = "hand"


@dataclass(frozen=True)
class Color:
    """RGB color representation with values from 0.0 to 1.0."""

    r: float
    g: float
    b: float

    def as_tuple(self) -> Tuple[float, float, float]:
        """Return color as RGB tuple."""
        return (self.r, self.g, self.b)


# Standard rig colors
class RigColors:
    """Standard colors used throughout the rig."""

    LEFT = Color(0.0, 0.0, 0.5)
    LEFT_BRIGHT = Color(0.0, 0.0, 0.75)
    RIGHT = Color(0.5, 0.0, 0.0)
    RIGHT_BRIGHT = Color(0.75, 0.0, 0.0)
    CENTER = Color(1.0, 0.25, 0.0)
    GLOBAL = Color(0.75, 0.75, 0.0)
    BODY = Color(0.75, 0.5, 0.0)


@dataclass
class JointConfig:
    """Configuration for a single joint in the skeleton."""

    name: str
    ctrl_radius: float = 1.15
    is_constrainable: bool = False
    rename_to: str | None = None  # For special cases like pelvis -> hips


@dataclass
class LimbConfig:
    """Configuration for a limb chain."""

    parts: List[str]
    parent_joint: str
    ik_handle_name: str
    pole_vector_offset: float = 25.0


@dataclass
class FingerConfig:
    """Configuration for finger controls."""

    name: str
    joints: List[str]
    spread_multiplier: float = 1.0


@dataclass
class FootRollConfig:
    """Configuration for reverse foot setup."""

    heel_offset: float = 5.0
    toe_offset: float = -7.0
    roll_min: float = -30.0
    roll_max: float = 70.0
    bend_limit_angle: float = 45.0
    toe_straight_angle: float = 75.0


@dataclass
class SpaceSwitchConfig:
    """Configuration for space switching."""

    spaces: List[str]
    controls: List[str]


# Core skeleton joints with their control radii
CORE_SKELETON: List[JointConfig] = [
    JointConfig("root", ctrl_radius=20.0, is_constrainable=True),
    JointConfig(
        "pelvis", ctrl_radius=30.0, is_constrainable=True, rename_to="hips"
    ),
    JointConfig("spine_01", ctrl_radius=20.0, is_constrainable=True),
    JointConfig("spine_02", ctrl_radius=20.0, is_constrainable=True),
    JointConfig("spine_03", ctrl_radius=20.0, is_constrainable=True),
    JointConfig("spine_04", ctrl_radius=20.0, is_constrainable=True),
    JointConfig("spine_05", ctrl_radius=20.0, is_constrainable=True),
    JointConfig("neck_01", ctrl_radius=12.0, is_constrainable=True),
    JointConfig("neck_02", ctrl_radius=8.0, is_constrainable=True),
    JointConfig("head", ctrl_radius=15.0, is_constrainable=True),
]

# Clavicle joints
CLAVICLE_JOINTS: List[JointConfig] = [
    JointConfig("clavicle", ctrl_radius=15.0, is_constrainable=True),
]

# Toe joints (per side)
TOE_JOINTS: List[str] = [
    "bigtoe_01",
    "bigtoe_02",
    "indextoe_01",
    "indextoe_02",
    "middletoe_01",
    "middletoe_02",
    "ringtoe_01",
    "ringtoe_02",
    "littletoe_01",
    "littletoe_02",
]

# Finger definitions (per side)
FINGER_JOINTS: Dict[str, List[str]] = {
    "pinky": ["pinky_metacarpal", "pinky_01", "pinky_02", "pinky_03"],
    "ring": ["ring_metacarpal", "ring_01", "ring_02", "ring_03"],
    "middle": ["middle_metacarpal", "middle_01", "middle_02", "middle_03"],
    "index": ["index_metacarpal", "index_01", "index_02", "index_03"],
    "thumb": ["thumb_01", "thumb_02", "thumb_03"],
}

# Finger spread multipliers
FINGER_SPREAD_MULTIPLIERS: Dict[str, float] = {
    "index": 2.0,
    "middle": 1.0,
    "ring": -1.0,
    "pinky": -2.0,
}

# Arm limb configuration
ARM_LIMB = LimbConfig(
    parts=["upperarm", "lowerarm", "hand"],
    parent_joint="clavicle",
    ik_handle_name="hand",
    pole_vector_offset=25.0,
)

# Leg limb configuration
LEG_LIMB = LimbConfig(
    parts=["thigh", "calf", "foot", "ball"],
    parent_joint="pelvis",
    ik_handle_name="foot",
    pole_vector_offset=25.0,
)

# Parts that should use constraints instead of direct connections
CONSTRAINABLE_PARTS: List[str] = [
    "root",
    "pelvis",
    "spine",
    "neck",
    "head",
    "clavicle",
    "toe",
    "metacarpal",
    "thumb",
    "index",
    "middle",
    "ring",
    "pinky",
    "_ik_",
]

# Space switch configuration for IK hands
HAND_SPACE_SWITCH = SpaceSwitchConfig(
    spaces=["world", "chest", "body", "head"],
    controls=["global_ctrl", "spine_04_ctrl", "body_ctrl", "head_ctrl"],
)

# Full metahuman skeleton for motion skeleton creation
FULL_METAHUMAN_SKELETON: List[str] = [
    "root",
    "pelvis",
    "spine_01",
    "spine_02",
    "spine_03",
    "spine_04",
    "spine_05",
    "neck_01",
    "neck_02",
    "head",
    "clavicle_l",
    "upperarm_l",
    "lowerarm_l",
    "hand_l",
    "middle_metacarpal_l",
    "middle_01_l",
    "middle_02_l",
    "middle_03_l",
    "pinky_metacarpal_l",
    "pinky_01_l",
    "pinky_02_l",
    "pinky_03_l",
    "ring_metacarpal_l",
    "ring_01_l",
    "ring_02_l",
    "ring_03_l",
    "thumb_01_l",
    "thumb_02_l",
    "thumb_03_l",
    "index_metacarpal_l",
    "index_01_l",
    "index_02_l",
    "index_03_l",
    "clavicle_r",
    "upperarm_r",
    "lowerarm_r",
    "hand_r",
    "middle_metacarpal_r",
    "middle_01_r",
    "middle_02_r",
    "middle_03_r",
    "pinky_metacarpal_r",
    "pinky_01_r",
    "pinky_02_r",
    "pinky_03_r",
    "ring_metacarpal_r",
    "ring_01_r",
    "ring_02_r",
    "ring_03_r",
    "thumb_01_r",
    "thumb_02_r",
    "thumb_03_r",
    "index_metacarpal_r",
    "index_01_r",
    "index_02_r",
    "index_03_r",
    "thigh_l",
    "calf_l",
    "foot_l",
    "ball_l",
    "thigh_r",
    "calf_r",
    "foot_r",
    "ball_r",
    "bigtoe_01_l",
    "bigtoe_02_l",
    "indextoe_01_l",
    "indextoe_02_l",
    "middletoe_01_l",
    "middletoe_02_l",
    "ringtoe_01_l",
    "ringtoe_02_l",
    "littletoe_01_l",
    "littletoe_02_l",
    "bigtoe_01_r",
    "bigtoe_02_r",
    "indextoe_01_r",
    "indextoe_02_r",
    "middletoe_01_r",
    "middletoe_02_r",
    "ringtoe_01_r",
    "ringtoe_02_r",
    "littletoe_01_r",
    "littletoe_02_r",
]

# Additional parts for non-motion mode (wings, tentacles, etc.)
ADDITIONAL_PARTS: Dict[str, List[str]] = {
    "wing1": [f"wing1_{i:02d}" for i in range(1, 9)],
    "wing2": [f"wing2_{i:02d}" for i in range(1, 9)],
    "wing3": [f"wing3_{i:02d}" for i in range(1, 7)],
    "extra_toes": [
        "littletoe_03",
        "ringtoe_03",
        "indextoe_03",
        "bigtoe_03",
        "middletoe_03",
    ],
    "tentacles": [f"tentacle_{i}" for i in range(1, 49)],
    "extra_pinky": [
        "pinkyB_metacarpal",
        "pinkyB_01",
        "pinkyB_02",
        "pinkyB_03",
        "pinkyC_metacarpal",
        "pinkyC_01",
        "pinkyC_02",
        "pinkyC_03",
    ],
    "jaw": ["jaw_01"],
}


# Control shape configurations
@dataclass
class ControlShapeConfig:
    """Configuration for control curve shapes."""

    radius: float = 10.0
    degree: int = 3
    sections: int = 8
    line_width: float = 2.0
    normal: Tuple[float, float, float] = (0, 0, 1)
    shape_type: ShapeType = ShapeType.CIRCLE


# Default control configurations by type
CONTROL_CONFIGS: Dict[str, ControlShapeConfig] = {
    "root": ControlShapeConfig(
        radius=18.0, shape_type=ShapeType.DIRECTION_ARROW, line_width=3.0
    ),
    "global": ControlShapeConfig(
        radius=50.0, shape_type=ShapeType.COG, line_width=3.0
    ),
    "body_offset": ControlShapeConfig(
        radius=30.0, shape_type=ShapeType.FOUR_ARROW, line_width=2.5
    ),
    "body": ControlShapeConfig(
        radius=35.0, shape_type=ShapeType.COG, line_width=2.5
    ),
    "limb_fk": ControlShapeConfig(
        radius=10.0, shape_type=ShapeType.CIRCLE, line_width=2.0
    ),
    "limb_fk_thigh": ControlShapeConfig(
        radius=15.0, shape_type=ShapeType.CIRCLE, line_width=2.0
    ),
    "limb_ik": ControlShapeConfig(
        radius=10.0, shape_type=ShapeType.CUBE, line_width=2.5
    ),
    "limb_ik_leg": ControlShapeConfig(
        radius=15.0, shape_type=ShapeType.CUBE, line_width=2.5
    ),
    "pole_vector": ControlShapeConfig(
        radius=3.0, shape_type=ShapeType.SPHERE, line_width=2.0
    ),
    "toe_twist": ControlShapeConfig(
        radius=3.0, shape_type=ShapeType.ARROW, line_width=2.0
    ),
    "ball_lift": ControlShapeConfig(
        radius=5.0, shape_type=ShapeType.ARROW, line_width=2.0
    ),
    "fingers": ControlShapeConfig(
        radius=8.0, shape_type=ShapeType.CIRCLE, line_width=2.5
    ),
    "additional": ControlShapeConfig(
        radius=7.0, shape_type=ShapeType.CIRCLE, sections=8
    ),
    "tentacle": ControlShapeConfig(
        radius=0.5, shape_type=ShapeType.CIRCLE, sections=8
    ),
    "toe": ControlShapeConfig(
        radius=1.5, shape_type=ShapeType.CIRCLE, sections=8
    ),
}


def get_skeleton_joints_with_radius() -> List[Tuple[str, float]]:
    """Generate full skeleton joint list with their control radii.

    Returns:
        List of tuples containing (joint_name, radius).
    """
    result: List[Tuple[str, float]] = []

    # Add core skeleton
    for joint_cfg in CORE_SKELETON:
        result.append((joint_cfg.name, joint_cfg.ctrl_radius))

    # Add clavicles for both sides
    for side in [Side.LEFT, Side.RIGHT]:
        for joint_cfg in CLAVICLE_JOINTS:
            result.append(
                (f"{joint_cfg.name}_{side.value}", joint_cfg.ctrl_radius)
            )

    # Add toes for both sides
    for side in [Side.LEFT, Side.RIGHT]:
        for toe in TOE_JOINTS:
            result.append((f"{toe}_{side.value}", 1.15))

    # Add fingers for both sides
    for side in [Side.LEFT, Side.RIGHT]:
        for finger_name, joints in FINGER_JOINTS.items():
            for joint in joints:
                result.append((f"{joint}_{side.value}", 1.15))

    return result


def is_constrainable_joint(joint_name: str) -> bool:
    """Check if a joint should use constraints instead of direct connections.

    Args:
        joint_name: Name of the joint to check.

    Returns:
        True if the joint should use constraints.
    """
    return any(part in joint_name for part in CONSTRAINABLE_PARTS)
