"""Data module for MetaHuman rig.

This module provides data structures and configuration for the rig system.
"""

from __future__ import annotations

from .skeleton_config import (
    ARM_LIMB,
    CLAVICLE_JOINTS,
    CONSTRAINABLE_PARTS,
    CONTROL_CONFIGS,
    CORE_SKELETON,
    FINGER_JOINTS,
    FINGER_SPREAD_MULTIPLIERS,
    FULL_METAHUMAN_SKELETON,
    HAND_SPACE_SWITCH,
    LEG_LIMB,
    TOE_JOINTS,
    Color,
    ControlShapeConfig,
    FingerConfig,
    FootRollConfig,
    JointConfig,
    LimbConfig,
    RigColors,
    RigType,
    ShapeType,
    Side,
    SpaceSwitchConfig,
    get_skeleton_joints_with_radius,
    is_constrainable_joint,
)

__all__ = [
    # Enums
    "Side",
    "RigType",
    "ShapeType",
    # Color
    "Color",
    "RigColors",
    # Config classes
    "JointConfig",
    "LimbConfig",
    "FingerConfig",
    "FootRollConfig",
    "SpaceSwitchConfig",
    "ControlShapeConfig",
    # Data
    "CORE_SKELETON",
    "CLAVICLE_JOINTS",
    "TOE_JOINTS",
    "FINGER_JOINTS",
    "FINGER_SPREAD_MULTIPLIERS",
    "ARM_LIMB",
    "LEG_LIMB",
    "CONSTRAINABLE_PARTS",
    "HAND_SPACE_SWITCH",
    "FULL_METAHUMAN_SKELETON",
    "CONTROL_CONFIGS",
    # Functions
    "get_skeleton_joints_with_radius",
    "is_constrainable_joint",
]
