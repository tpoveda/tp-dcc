from __future__ import annotations

from tp.dcc import node
from tp.dcc.abstract import mesh


class StandaloneMesh(node.Node, mesh.AbstractMesh):
    """
    Overload of skin.AbstractSkin used to interface with meshes for standalone applications.
    """

    pass
