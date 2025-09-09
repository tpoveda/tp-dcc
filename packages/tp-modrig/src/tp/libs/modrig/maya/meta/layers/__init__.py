from __future__ import annotations

from typing import Union

from ..layer import MetaLayer
from .modules_layer import MetaModulesLayer
from .geometry_layer import MetaGeometryLayer


MetaLayerType = Union[MetaLayer, MetaModulesLayer, MetaGeometryLayer]

__all__ = [
    "MetaLayerType",
    "MetaLayer",
    "MetaModulesLayer",
    "MetaGeometryLayer",
]
