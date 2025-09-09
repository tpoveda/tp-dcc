from __future__ import annotations

from typing import Union

from .abstract_layer import LayerDescriptor
from .guide_layer import GuideLayerDescriptor

LayerDescriptorType = Union[
    LayerDescriptor,
    GuideLayerDescriptor,
]


__all__ = [
    "LayerDescriptorType",
    "LayerDescriptor",
    "GuideLayerDescriptor",
]
