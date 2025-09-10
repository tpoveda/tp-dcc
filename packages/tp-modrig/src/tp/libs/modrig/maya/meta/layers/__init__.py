from __future__ import annotations

from typing import Union

from ..layer import MetaLayer
from .guide_layer import MetaGuidesLayer
from .modules_layer import MetaModulesLayer
from .geometry_layer import MetaGeometryLayer
from .skeleton_layer import MetaSkeletonLayer


MetaLayerType = Union[
    MetaLayer,
    MetaGuidesLayer,
    MetaModulesLayer,
    MetaGeometryLayer,
    MetaSkeletonLayer,
]

__all__ = [
    "MetaLayerType",
    "MetaLayer",
    "MetaGuidesLayer",
    "MetaModulesLayer",
    "MetaGeometryLayer",
    "MetaSkeletonLayer",
]
