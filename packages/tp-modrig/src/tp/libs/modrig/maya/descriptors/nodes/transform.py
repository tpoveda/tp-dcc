from __future__ import annotations

from typing import Iterable, Any
from dataclasses import dataclass, field, InitVar

from maya.api import OpenMaya

from tp.libs.maya.om import constants, apitypes

from .dg import DGNodeDescriptor
from ..attributes import attribute_class_for_descriptor, AttributeDescriptor


# noinspection PyPep8Naming,PyRedeclaration
@dataclass
class TransformDescriptor(DGNodeDescriptor):
    """Dataclass that describes a transform node."""

    # === Core === #
    type: str = "transform"
    modType: str = "transform"

    # === Transform data (stored as tuples; properties expose zapi types) === #
    rotateOrder: int = 0
    translate: (
        InitVar[tuple[float, float, float] | Iterable[float] | OpenMaya.MVector] | None
    ) = None
    rotate: (
        InitVar[
            tuple[float, float, float, float]
            | Iterable[float]
            | OpenMaya.MEulerRotation
            | OpenMaya.MQuaternion
        ]
        | None
    ) = None
    scale: (
        InitVar[tuple[float, float, float] | Iterable[float] | OpenMaya.MVector] | None
    ) = None
    matrix: InitVar[tuple[float, ...] | Iterable[float]] | None = None

    # === Hierarchy ===
    children: list[TransformDescriptor] = field(default_factory=list)

    # Private tuple storage (JSON-friendly)
    _translate: tuple[float, float, float] | None = field(default=None, repr=False)
    _rotate: tuple[float, float, float] | tuple[float, float, float, float] | None = (
        field(default=None, repr=False)
    )
    _scale: tuple[float, float, float] | None = field(default=None, repr=False)
    _matrix: tuple[float, ...] | None = field(default=None, repr=False)

    # === Initialization === #

    # noinspection PyTypeChecker,PyDataclass
    def __post_init__(self, translate, rotate, scale, matrix) -> None:
        self._translate = tuple(translate)
        self._rotate = tuple(rotate)
        self._scale = tuple(scale)
        if self._matrix is not None:
            self._matrix = tuple(self._matrix)

    # === Properties === #

    @property
    def translate(self) -> OpenMaya.MVector:
        """The translation as an `MVector`."""

        return OpenMaya.MVector(self._translate)

    @translate.setter
    def translate(self, v: Iterable[float] | OpenMaya.MVector) -> None:
        if isinstance(v, OpenMaya.MVector):
            self._translate = (float(v.x), float(v.y), float(v.z))
        else:
            x, y, z = tuple(v)
            self._translate = (float(x), float(y), float(z))

    @property
    def rotate(self) -> OpenMaya.MEulerRotation | OpenMaya.MQuaternion:
        """The rotation as an `MEulerRotation` or `MQuaternion`."""

        if len(self._rotate) == 3:
            return OpenMaya.MEulerRotation(self._rotate, self.rotateOrder)

        return OpenMaya.MQuaternion(self._rotate)

    @rotate.setter
    def rotate(self, q: Iterable[float] | OpenMaya.MQuaternion) -> None:
        if isinstance(q, OpenMaya.MQuaternion):
            self._rotate = (float(q.x), float(q.y), float(q.z), float(q.w))
        else:
            x, y, z, w = tuple(q)
            self._rotate = (float(x), float(y), float(z), float(w))

    @property
    def scale(self) -> OpenMaya.MVector:
        """The scale as an `MVector`."""

        return OpenMaya.MVector(self._scale)

    @scale.setter
    def scale(self, v: Iterable[float] | OpenMaya.MVector) -> None:
        if isinstance(v, OpenMaya.MVector):
            self._scale = (float(v.x), float(v.y), float(v.z))
        else:
            x, y, z = tuple(v)
            self._scale = (float(x), float(y), float(z))

    @property
    def matrix(self) -> OpenMaya.MMatrix:
        """The local matrix as an `MMatrix`."""

        if self._matrix is not None:
            return OpenMaya.MMatrix(self._matrix)

        transformation_matrix = OpenMaya.MTransformationMatrix()
        transformation_matrix.setTranslation(self.translate, apitypes.kWorldSpace)
        transformation_matrix.setRotation(self.rotate)
        transformation_matrix.setScale(self._scale, apitypes.kWorldSpace)

        return transformation_matrix.asMatrix()

    @matrix.setter
    def matrix(self, value: Iterable[float]) -> None:
        """Set the local matrix from iterable of floats."""

        self._matrix = tuple(value)  # type: ignore[assignment]

    @property
    def worldMatrix(self) -> OpenMaya.MMatrix:
        """Compose world matrix from T/R/S."""

        transformation_matrix = OpenMaya.MTransformationMatrix()
        transformation_matrix.setTranslation(
            OpenMaya.MVector(self._translate), apitypes.kWorldSpace
        )
        if self._rotate:
            quat = (
                self._rotate
                if len(self._rotate) == 4
                else OpenMaya.MEulerRotation(
                    self._rotate, self.rotateOrder
                ).asQuaternion()
            )
            transformation_matrix.setRotation(OpenMaya.MQuaternion(quat))
        transformation_matrix.setScale(self._scale, apitypes.kWorldSpace)

        return transformation_matrix.asMatrix()

    @worldMatrix.setter
    def worldMatrix(self, value: Any) -> None:
        """Decompose and store into translate/rotate/scale."""

        transformation_matrix = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(value))
        self._translate = tuple(transformation_matrix.translation(apitypes.kWorldSpace))  # type: ignore[assignment]
        self._rotate = tuple(transformation_matrix.rotation(asQuaternion=True))  # type: ignore[assignment]
        self._scale = tuple(transformation_matrix.scale(apitypes.kWorldSpace))  # type: ignore[assignment]

    # === Deserialize / Serialize / Copy === #

    @classmethod
    def deserialize(
        cls, data: dict[str, Any], parent: str | None = None
    ) -> TransformDescriptor:
        """Convert a Definition-compatible dict into a
        `TransformDescriptor`, recursively.

        Args:
            data: The input `dict`.
            parent: Optional parent ID to override `data['parent']`.

        Returns:
            The deserialized `TransformDescriptor`.
        """

        # Normalize core transform fields as tuples.
        def _as_tuple(
            x: Iterable[float] | None, fall: Iterable[float]
        ) -> tuple[float, ...]:
            if x is None:
                return tuple(fall)
            return tuple(x)

        translate = _as_tuple(data.get("translate"), (0.0, 0.0, 0.0))
        rotate = _as_tuple(data.get("rotate"), (0.0, 0.0, 0.0, 1.0))
        scale = _as_tuple(data.get("scale"), (1.0, 1.0, 1.0))

        # Convert attributes: dedupe by name.
        attr_defs = data.get("attributes", []) or []
        seen = set()
        attr_instances: list[AttributeDescriptor] = []
        for a in attr_defs:
            name = a.get("name")
            if not name or name in seen:
                continue
            seen.add(name)
            attr_instances.append(attribute_class_for_descriptor(a))

        # Children: recursively deserialize
        raw_children = data.get("children", []) or []
        wm = data.get("worldMatrix")

        # noinspection PyTypeChecker
        d = cls(
            id=data.get("id", "") or data.get("_id", "") or "",
            name=data.get("name", "control"),
            parent=parent,
            children=[],  # fill below
            modType=data.get("modType", "transform"),
            type=data.get("type", "transform"),
            rotateOrder=int(data.get("rotateOrder", 0)),
            _translate=translate,
            _rotate=rotate,
            _scale=scale,
            _matrix=tuple(data["matrix"])
            if "matrix" in data and data["matrix"] is not None
            else None,
            attributes=attr_instances,
        )

        # Decompose `worldMatrix` only if translate wasn't explicitly provided.
        # Setter will decompose to translate/rotate/scale
        if "translate" not in data and wm is not None:
            d.worldMatrix = OpenMaya.MMatrix(wm)

        # Now set children with this node's id as parent.
        d.children = [cls.deserialize(child, parent=d.id) for child in raw_children]

        return d

    def to_dict(self) -> dict:
        """Convert the transform descriptor to a dictionary.

        Returns:
            A dictionary representation of the transform descriptor.
        """

        out = super().to_dict()
        out.update(
            {
                "translate": self._translate,
                "rotate": self._rotate,
                "scale": self._scale,
                "children": [c.to_dict() for c in self.children],
            }
        )
        if self._matrix is not None:
            out["matrix"] = self._matrix

        return out

    # === Utilities === #

    def iterate_children(self, recursive: bool = True) -> Iterable[TransformDescriptor]:
        """Yield children (and optionally descendants) as `TransformDescriptor`."""

        for child in self.children:
            yield child
            if recursive:
                yield from child.iterate_children(recursive=True)

    def delete_child(self, child_id: str) -> bool:
        """Delete a direct child (non-recursive filter).

        Args:
            child_id: ID of the child to delete.

        Returns:
            `True` if a child was deleted; `False` otherwise.
        """

        kept: list[TransformDescriptor] = []
        deleted = False
        for child in self.iterate_children(recursive=False):
            if child.id == child_id:
                deleted = True
            else:
                kept.append(child)

        self.children = kept

        return deleted

    def transformation_matrix(
        self,
        translate: bool = True,
        rotate: bool = True,
        scale: bool = True,
    ) -> OpenMaya.MTransformationMatrix:
        """Build a transformation matrix from stored TRS, honoring rotate order.

        Args:
            translate: Whether to include translation.
            rotate: Whether to include rotation.
            scale: Whether to include scale.

        Returns:
            The composed `MTransformationMatrix`.
        """

        transformation_matrix = OpenMaya.MTransformationMatrix()
        if translate:
            transformation_matrix.setTranslation(
                OpenMaya.MVector(self._translate or (0.0, 0.0, 0.0)),
                apitypes.kWorldSpace,
            )
        if rotate:
            quat = (
                self._rotate
                if len(self._rotate) == 4
                else OpenMaya.MEulerRotation(
                    self._rotate or (0.0, 0.0, 0.0), self.rotateOrder
                ).asQuaternion()
            )
            transformation_matrix.setRotation(OpenMaya.MQuaternion(quat))
            transformation_matrix.reorderRotation(
                constants.kRotateOrders.get(self.rotateOrder, -1)
            )
        if scale:
            transformation_matrix.setScale(
                self._scale or (1.0, 1.0, 1.0), apitypes.kWorldSpace
            )

        return transformation_matrix
