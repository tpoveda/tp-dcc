from __future__ import annotations

from tp.dcc import node
from tp.dcc.abstract import skin


class StandaloneSkin(node.Node, skin.AbstractSkin):
    """
    Overload of skin.AbstractSkin used to interface with skinning in standalone applications.
    """

    pass
