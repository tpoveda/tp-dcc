"""MetaHuman body rig metanode system.

This package provides the metanode infrastructure for MetaHuman body rigs,
enabling queryable meta connections, versioning, and clean lifecycle management.
"""

from __future__ import annotations

from .constants import (
    METAHUMAN_CONTROLS_LAYER_TYPE,
    METAHUMAN_FKIK_LAYER_TYPE,
    METAHUMAN_LAYER_TYPE,
    METAHUMAN_REVERSE_FOOT_LAYER_TYPE,
    METAHUMAN_RIG_TYPE,
    METAHUMAN_SKELETON_LAYER_TYPE,
    METAHUMAN_SPACE_SWITCH_LAYER_TYPE,
)
from .layer import MetaHumanLayer
from .layers import (
    MetaHumanControlsLayer,
    MetaHumanFKIKLayer,
    MetaHumanReverseFootLayer,
    MetaHumanSkeletonLayer,
    MetaHumanSpaceSwitchLayer,
)
from .rig import MetaMetaHumanRig

__all__ = [
    # Constants
    "METAHUMAN_RIG_TYPE",
    "METAHUMAN_LAYER_TYPE",
    "METAHUMAN_CONTROLS_LAYER_TYPE",
    "METAHUMAN_SKELETON_LAYER_TYPE",
    "METAHUMAN_FKIK_LAYER_TYPE",
    "METAHUMAN_SPACE_SWITCH_LAYER_TYPE",
    "METAHUMAN_REVERSE_FOOT_LAYER_TYPE",
    # Classes
    "MetaHumanLayer",
    "MetaHumanControlsLayer",
    "MetaHumanSkeletonLayer",
    "MetaHumanFKIKLayer",
    "MetaHumanSpaceSwitchLayer",
    "MetaHumanReverseFootLayer",
    "MetaMetaHumanRig",
]
