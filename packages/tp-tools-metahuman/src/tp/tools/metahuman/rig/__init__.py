"""MetaHuman rig module.

This module provides classes and functions for building MetaHuman body rigs.

For most use cases, the high-level API is recommended:

    >>> from tp.tools.metahuman.rig import RigAPI, RigOptions
    >>>
    >>> # Build with defaults
    >>> result = RigAPI.build_quick()
    >>>
    >>> # Build with custom options
    >>> options = RigOptions(motion=True, scale=1.5)
    >>> result = RigAPI.build(options)
"""

from __future__ import annotations

from .api import (
    BuildMode,
    ProgressCallback,
    ProgressInfo,
    RigAPI,
    RigOptions,
    ValidationResult,
)
from .body_rig_builder import (
    MetaHumanBodyRigBuilder,
    RigBuildResult,
    build_metahuman_body_rig,
)
from .builders import (
    ControlBuilder,
    FingerControlBuilder,
    FKIKSwitchBuilder,
    ReverseFootBuilder,
    SkeletonBuilder,
    SpaceSwitchBuilder,
)
from .data.skeleton_config import (
    Color,
    RigColors,
    RigType,
    Side,
)

__all__ = [
    # High-level API
    "RigAPI",
    "RigOptions",
    "BuildMode",
    "ValidationResult",
    "ProgressInfo",
    "ProgressCallback",
    # Main builder
    "MetaHumanBodyRigBuilder",
    "RigBuildResult",
    "build_metahuman_body_rig",
    # Enums
    "Side",
    "RigType",
    "Color",
    "RigColors",
    # Builders
    "ControlBuilder",
    "SkeletonBuilder",
    "ReverseFootBuilder",
    "SpaceSwitchBuilder",
    "FingerControlBuilder",
    "FKIKSwitchBuilder",
]
