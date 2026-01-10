"""Constants for MetaHuman body rig metanode system.

This module defines all metanode type identifiers, attribute names, and other
constants used throughout the MetaHuman rig meta system.
"""

from __future__ import annotations

# === MetaClass Types ===
# These are the unique identifiers for each metanode type in the system.
# They are used to register and lookup metanode classes.

METAHUMAN_RIG_TYPE = "metaHumanRig"
"""Type identifier for the root MetaHuman rig metanode."""

METAHUMAN_LAYER_TYPE = "metaHumanLayer"
"""Base type identifier for MetaHuman rig layers."""

METAHUMAN_CONTROLS_LAYER_TYPE = "metaHumanControlsLayer"
"""Type identifier for the controls layer (FK spine, head, etc.)."""

METAHUMAN_SKELETON_LAYER_TYPE = "metaHumanSkeletonLayer"
"""Type identifier for the motion skeleton layer."""

METAHUMAN_FKIK_LAYER_TYPE = "metaHumanFKIKLayer"
"""Type identifier for FK/IK limb systems layer."""

METAHUMAN_SPACE_SWITCH_LAYER_TYPE = "metaHumanSpaceSwitchLayer"
"""Type identifier for space switching systems layer."""

METAHUMAN_REVERSE_FOOT_LAYER_TYPE = "metaHumanReverseFootLayer"
"""Type identifier for reverse foot setup layer."""

# === Shared Attribute Names ===
# Common attributes used across multiple metanode types.

ID_ATTR = "id"
"""Unique identifier attribute for the metanode."""

NAME_ATTR = "name"
"""Human-readable name attribute."""

IS_METAHUMAN_RIG_ATTR = "isMetaHumanRig"
"""Boolean flag indicating this is a MetaHuman rig metanode."""

IS_ROOT_ATTR = "isRoot"
"""Boolean flag indicating this is a root metanode."""

# === Rig Attribute Names ===
# Attributes specific to the MetaMetaHumanRig class.

RIG_VERSION_ATTR = "rigVersion"
"""Version string for the rig (e.g., '1.0.0')."""

RIG_ROOT_TRANSFORM_ATTR = "rootTransform"
"""Message connection to the root transform node."""

RIG_CONTROLS_GROUP_ATTR = "controlsGroup"
"""Message connection to the rig_ctrls group."""

RIG_SETUP_GROUP_ATTR = "setupGroup"
"""Message connection to the rig_setup group."""

RIG_MOTION_SKELETON_ATTR = "motionSkeleton"
"""Message connection to the motion skeleton root joint."""

RIG_CONTROL_DISPLAY_LAYER_ATTR = "controlDisplayLayer"
"""Message connection to the control display layer."""

RIG_IS_MOTION_MODE_ATTR = "isMotionMode"
"""Boolean flag indicating motion skeleton mode."""

# === Layer Attribute Names ===
# Attributes used by MetaHumanLayer and its subclasses.

LAYER_ROOT_TRANSFORM_ATTR = "layerRootTransform"
"""Message connection to the layer's root transform."""

LAYER_CONTROLS_ATTR = "controls"
"""Array of message connections to control nodes."""

LAYER_JOINTS_ATTR = "joints"
"""Array of message connections to joint nodes."""

LAYER_SETTINGS_NODES_ATTR = "settingNodes"
"""Array of message connections to settings nodes."""

# === Control Node Attribute Names ===
# Attributes added to control nodes for identification.

CONTROL_ID_ATTR = "controlId"
"""Unique identifier for the control."""

CONTROL_SIDE_ATTR = "controlSide"
"""Side indicator (l, r, c) for the control."""

CONTROL_TYPE_ATTR = "controlType"
"""Type of control (fk, ik, pole, etc.)."""

# === Transform Attributes ===
# Standard transform attributes for locking/hiding.

TRANSFORM_ATTRS = ("translate", "rotate", "scale", "visibility")
"""Standard transform attributes to lock on setup nodes."""

LOCAL_TRANSFORM_ATTRS = (
    "translateX",
    "translateY",
    "translateZ",
    "rotateX",
    "rotateY",
    "rotateZ",
    "scaleX",
    "scaleY",
    "scaleZ",
)
"""Individual transform channel attributes."""

# === Default Values ===

DEFAULT_RIG_VERSION = "1.0.0"
"""Default version string for new rigs."""

DEFAULT_RIG_NAME = "metahuman_body_rig"
"""Default name for new rigs."""
