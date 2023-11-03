from __future__ import annotations

import abc
import enum
import dataclasses

from tp.dcc.abstract import base
from tp.dcc.dataclasses import vector


class ComponentType(enum.IntEnum):
    """
    Enumerator that holds all available mesh components.
    """

    Vertex = 0
    Edge = 1
    Face = 2


@dataclasses.dataclass
class Hit:
    """
    Data class to store hit related data
    """

    point: vector.Vector = dataclasses.field(default_factory=lambda: vector.Vector())
    face_index: int = 0
    face_vertex_indices: list[int] = dataclasses.field(default_factory=lambda: [])
    bi_coords: tuple[float, float] = dataclasses.field(default_factory=lambda: (0.0, 0.0))
    triangle_index: int = 0
    triangle_vertex_indices: list[int] = dataclasses.field(default_factory=lambda: [])
    bary_coords: tuple[float, float, float] = dataclasses.field(default_factory=lambda: (0.0, 0.0, 0.0))


class AbstractMesh(base.AbstractBase):
    """
    Overloads of base.AbstractBase that outlines DCC context behaviour for meshes.
    """

    __slots__ = ()
    __face_triangles__ = {}     # Lookup optimization

    ComponentType = ComponentType
    Hit = Hit
