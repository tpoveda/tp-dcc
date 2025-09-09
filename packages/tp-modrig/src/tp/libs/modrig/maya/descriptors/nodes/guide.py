from __future__ import annotations

from typing import Iterable
from dataclasses import dataclass, field

from maya.api import OpenMaya

from tp.libs.maya.om.constants import kRotateOrders
from tp.libs.maya.om import attributetypes, apitypes, mathlib

from .control import ControlDescriptor
from ..attributes import AttributeDescriptor, VectorAttributeDescriptor
from ...base import constants


# noinspection PyPep8Naming
@dataclass
class GuideDescriptor(ControlDescriptor):
    """Dataclass that represents a guide descriptor."""

    name = "GUIDE_RENAME"
    modType: str = "guide"

    # === Visuals === #
    pivotColor: tuple[int, int, int] | tuple[float, float, float] = field(
        default_factory=lambda: constants.DEFAULT_GUIDE_PIVOT_COLOR
    )
    pivotShape: str = "sphere_arrow"
    pivotShapeType: int = constants.GUIDE_TYPE_NURBS_CURVE
    internal: bool = False
    mirror: bool = True
    connectorParent: str | None = None

    # === Attributes === #
    attributes: list[AttributeDescriptor] = field(
        default_factory=lambda: [
            VectorAttributeDescriptor(
                name=constants.GUIDE_AUTO_ALIGN_AIM_VECTOR_ATTR,
                type=attributetypes.kMFnNumeric3Float,
                value=constants.DEFAULT_AIM_VECTOR,
                default=constants.DEFAULT_UP_VECTOR,
            ),
            VectorAttributeDescriptor(
                name=constants.GUIDE_AUTO_ALIGN_UP_VECTOR_ATTR,
                type=attributetypes.kMFnNumeric3Float,
                value=constants.DEFAULT_UP_VECTOR,
                default=constants.DEFAULT_UP_VECTOR,
            ),
        ]
    )

    # noinspection PyTypeChecker,PyPep8Naming
    def update(
        self,
        *,
        parent: str | None = None,
        shape: dict | None = None,
        shapeTransform: dict | None = None,
        rotateOrder: int | None = None,
        pivotShapeType: int | None = None,
        pivotShape: str | None = None,
        worldMatrix: OpenMaya.MMatrix | Iterable[Iterable[float]] | None = None,
        translate: Iterable[float] | OpenMaya.MVector | None = None,
        rotate: Iterable[float] | OpenMaya.MQuaternion | None = None,
        scale: Iterable[float] | OpenMaya.MVector | None = None,
        connectorParent: str | None = None,
        attributes: list[AttributeDescriptor] | None = None,
    ) -> None:
        if not self.internal and parent is not None:
            self.parent = parent
        if shape is not None:
            self.shape = shape
        if shapeTransform is not None:
            self.shapeTransform = shapeTransform
        if rotateOrder is not None:
            self.rotateOrder = int(rotateOrder)
        if pivotShapeType is not None:
            self.pivotShapeType = int(pivotShapeType)
        if pivotShape is not None:
            self.pivotShape = pivotShape

        if (
            worldMatrix is not None
            and translate is None
            and rotate is None
            and scale is None
        ):
            self.worldMatrix = worldMatrix
        else:
            if translate is not None:
                self.translate = _tuple3(translate)
            if rotate is not None:
                self.rotate = _tuple4(rotate)
            if scale is not None:
                self.scale = _tuple3(scale, default=(1.0, 1.0, 1.0))

        if connectorParent is not None:
            self.connectorParent = connectorParent

        if attributes is not None:
            if not all(isinstance(a, AttributeDescriptor) for a in attributes):
                raise TypeError(
                    "GuideDescriptor.update(attributes=...) requires AttributeDescriptor instances."
                )
            by_name = {a.name: a for a in self.attributes}
            for a in attributes:
                by_name[a.name] = a
            self.attributes = list(by_name.values())

    @property
    def shapeTransformMatrix(self) -> OpenMaya.MMatrix:
        """The shape transform as an MMatrix."""

        st = self.shapeTransform
        transformation_matrix = OpenMaya.MTransformationMatrix()
        transformation_matrix.setTranslation(
            OpenMaya.MVector(st["translate"]), apitypes.kWorldSpace
        )
        transformation_matrix.setRotation(OpenMaya.MQuaternion(st["rotate"]))
        transformation_matrix.setScale(st["scale"], apitypes.kWorldSpace)

        return transformation_matrix.asMatrix()

    @shapeTransformMatrix.setter
    def shapeTransformMatrix(
        self, value: OpenMaya.MMatrix | Iterable[Iterable[float]]
    ) -> None:
        transformation_matrix = OpenMaya.MTransformationMatrix(value)
        self.shapeTransform = {
            "translate": tuple(transformation_matrix.translation(apitypes.kWorldSpace)),
            "rotate": tuple(transformation_matrix.rotation(asQuaternion=True)),
            "scale": transformation_matrix.scale(apitypes.kWorldSpace),
            "rotateOrder": kRotateOrders.get(transformation_matrix.rotationOrder(), 0),
        }

    def aim_vector(self) -> OpenMaya.MVector:
        """Return the aim vector of the guide.

        Returns:
            The aim vector as an `MVector`.
        """

        attr = self.attribute(constants.GUIDE_AUTO_ALIGN_AIM_VECTOR_ATTR)
        if attr is None or not isinstance(attr, VectorAttributeDescriptor):
            raise KeyError(
                f"Missing vector attribute: {constants.GUIDE_AUTO_ALIGN_AIM_VECTOR_ATTR}"
            )
        return attr.value

    def up_vector(self) -> OpenMaya.MVector:
        """Returns the up vector of the guide.

        Returns:
            The up vector as an `MVector`.
        """

        attr = self.attribute(constants.GUIDE_AUTO_ALIGN_UP_VECTOR_ATTR)
        if attr is None or not isinstance(attr, VectorAttributeDescriptor):
            raise KeyError(
                f"Missing vector attribute: {constants.GUIDE_AUTO_ALIGN_UP_VECTOR_ATTR}"
            )
        return attr.value

    def perpendicular_vector_index(self) -> tuple[int, bool]:
        """Returns the index of the perpendicular vector to the aim and up
        vectors.

        Returns:
            A tuple with the index of the perpendicular vector and a boolean
                indicating whether the up vector is parallel to the aim vector.
        """

        return mathlib.perpendicular_axis_from_align_vector(
            self.aim_vector(), self.up_vector()
        )

    def mirror_scale_vector(
        self,
        *,
        invertUpVector: bool = False,
        scale: Iterable[float] | OpenMaya.MVector = (1.0, 1.0, 1.0),
        mirrorAxisIndex: int | None = None,
    ) -> tuple[OpenMaya.MVector, bool]:
        """Returns the scale vector taking into account the guide mirroring
        and if the up vector should be inverted.

        Args:
            invertUpVector: Whether to invert the up vector.
            scale: The scale vector.
            mirrorAxisIndex: Optional index of the axis to mirror. If not
                provided, it will be calculated from the aim and up vectors.

        Returns:
            A tuple with the mirrored scale vector and a boolean indicating
                whether the scale was mirrored or not.
        """

        up = self.up_vector()
        scale_out = list(_tuple3(scale, default=(1.0, 1.0, 1.0)))
        if invertUpVector:
            scale_out[mathlib.primary_axis_index_from_vector(up)] *= -1.0

        mirrored_attr = self.attribute(constants.GUIDE_MIRROR_SCALED_ATTR)
        if mirrored_attr is None:
            raise KeyError(f"Missing attribute: {constants.GUIDE_MIRROR_SCALED_ATTR}")
        is_mirrored_scaled = bool(mirrored_attr.value)

        if is_mirrored_scaled:
            if mirrorAxisIndex is None:
                mirrorAxisIndex, _ = mathlib.perpendicular_axis_from_align_vector(
                    self.aim_vector(), up
                )
            scale_out[mirrorAxisIndex] *= -1.0

        return OpenMaya.MVector(scale_out), is_mirrored_scaled


def _tuple3(
    v: Iterable[float] | OpenMaya.MVector, *, default=(0.0, 0.0, 0.0)
) -> tuple[float, float, float]:
    """Converts an iterable or `MVector` to a length-3 tuple of floats.

    Args:
        v: The input iterable or `MVector`.
        default: The default value to use if v is None.

    Returns:
        A length-3 tuple of floats.
    """

    if isinstance(v, OpenMaya.MVector):
        return float(v.x), float(v.y), float(v.z)

    t = tuple(v) if v is not None else default
    if len(t) != 3:
        raise ValueError("Expected a length-3 vector")
    return float(t[0]), float(t[1]), float(t[2])


def _tuple4(
    v: Iterable[float] | OpenMaya.MQuaternion, *, default=(0.0, 0.0, 0.0, 1.0)
) -> tuple[float, float, float, float]:
    """Converts an iterable or `MQuaternion` to a length-4 tuple of floats.

    Args:
        v: The input iterable or `MQuaternion`.
        default: The default value to use if v is None.

    Returns:
        A length-4 tuple of floats.
    """

    if isinstance(v, OpenMaya.MQuaternion):
        return float(v.x), float(v.y), float(v.z), float(v.w)

    t = tuple(v) if v is not None else default
    if len(t) != 4:
        raise ValueError("Expected a length-4 quaternion")
    return float(t[0]), float(t[1]), float(t[2]), float(t[3])
