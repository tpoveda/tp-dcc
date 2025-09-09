from __future__ import annotations

from abc import ABC

from tp.libs.python.helpers import ObjectDict


class LayerDescriptor(ObjectDict, ABC):
    """Base layer descriptor class.

    Layers are containers or organized data for a single scene
    structure (such as guides, rig, skeleton, ...).
    """


