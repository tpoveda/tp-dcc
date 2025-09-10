from __future__ import annotations

from ..layer import MetaLayer
from ...base import constants


class MetaSkeletonLayer(MetaLayer):
    """Extends the `MetaLayer` class to handle operations related to
    skeleton in a `MetaRig`.

    Attributes:
        ID: A constant identifier representing the type of this meta-layer.
    """

    ID = constants.SKELETON_LAYER_TYPE
