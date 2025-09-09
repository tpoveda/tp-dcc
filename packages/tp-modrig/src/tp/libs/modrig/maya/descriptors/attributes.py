from __future__ import annotations

from typing import Iterable, Any
from dataclasses import dataclass, field, asdict, fields, InitVar

from maya.api import OpenMaya

from tp.libs.maya.om import attributetypes


@dataclass
class AttributeDescriptor:
    """Wrapper class to handle Maya types to dictionary storage. Each key
    requires a Maya data type that will be either returned or converted
    to a JSON compatible data type.
    """

    # === Core === #
    name: str = ""
    type: int = -1

    # === Values === #
    value: Any = None
    default: Any = None

    # === Ranges === #
    # Ranges / UI
    softMin: float | int | tuple | None = None
    softMax: float | int | tuple | None = None
    min: float | int | tuple | None = None
    max: float | int | tuple | None = None

    # === Flags === #
    locked: bool = False
    channelBox: bool = False
    keyable: bool = False

    # noinspection PyPep8Naming
    @property
    def typeStr(self) -> str:
        """The type string of the attribute."""

        return attributetypes.internal_type_to_string(self.type)

    # === Serialize / Deserialize === #

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly snapshot (tuples & scalars only)."""

        return asdict(self)

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> AttributeDescriptor:
        """Construct from a plain dict; ignores unknown keys safely."""

        allowed = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in allowed}

        return cls(**filtered)


# noinspection PyPep8Naming, PyRedeclaration
class VectorAttributeDescriptor(AttributeDescriptor):
    """Wrapper class to handle vector attributes."""

    value: InitVar[
        tuple[float, float, float] | Iterable[float] | OpenMaya.MVector | None
    ] = None
    default: InitVar[
        tuple[float, float, float] | Iterable[float] | OpenMaya.MVector | None
    ] = None
    softMin: InitVar[
        tuple[float, float, float] | Iterable[float] | OpenMaya.MVector | None
    ] = None
    softMax: InitVar[
        tuple[float, float, float] | Iterable[float] | OpenMaya.MVector | None
    ] = None
    min: InitVar[
        tuple[float, float, float] | Iterable[float] | OpenMaya.MVector | None
    ] = None
    max: InitVar[
        tuple[float, float, float] | Iterable[float] | OpenMaya.MVector | None
    ] = None

    # Private tuple storage (JSON-friendly)
    _value: tuple[float, float, float] | None = field(default=None, repr=False)
    _default: tuple[float, float, float] | None = field(default=None, repr=False)
    _softMin: tuple[float, float, float] | None = field(default=None, repr=False)
    _softMax: tuple[float, float, float] | None = field(default=None, repr=False)
    _min: tuple[float, float, float] | None = field(default=None, repr=False)
    _max: tuple[float, float, float] | None = field(default=None, repr=False)

    # === Initialization === #
    # noinspection PyShadowingBuiltins
    def __post_init__(
        self,
        value,
        default,
        softMin,
        softMax,
        min,
        max,
    ) -> None:
        self._value = _to_tuple3_or_none(value)
        self._default = _to_tuple3_or_none(default)
        self._softMin = _to_tuple3_or_none(softMin)
        self._softMax = _to_tuple3_or_none(softMax)
        self._min = _to_tuple3_or_none(min)
        self._max = _to_tuple3_or_none(max)

    @property
    def value(self) -> OpenMaya.MVector:
        raw = self._value or (0.0, 0.0, 0.0)
        return OpenMaya.MVector(raw)

    @value.setter
    def value(
        self, v: Iterable[float] | OpenMaya.MVector | tuple[float, float, float]
    ) -> None:
        self._value = _to_tuple3_or_none(v)

    @property
    def default(self) -> OpenMaya.MVector:
        raw = self._default or (0.0, 0.0, 0.0)
        return OpenMaya.MVector(raw)

    @default.setter
    def default(
        self, v: Iterable[float] | OpenMaya.MVector | tuple[float, float, float]
    ) -> None:
        self._default = _to_tuple3_or_none(v)

    @property
    def softMin(self) -> OpenMaya.MVector | None:
        return None if self._softMin is None else OpenMaya.MVector(self._softMin)

    @softMin.setter
    def softMin(
        self,
        v: Iterable[float] | OpenMaya.MVector | tuple[float, float, float] | None,
    ) -> None:
        self._softMin = _to_tuple3_or_none(v)

    @property
    def softMax(self) -> OpenMaya.MVector | None:
        return None if self._softMax is None else OpenMaya.MVector(self._softMax)

    @softMax.setter
    def softMax(
        self,
        v: Iterable[float] | OpenMaya.MVector | tuple[float, float, float] | None,
    ) -> None:
        self._softMax = _to_tuple3_or_none(v)

    @property
    def min(self) -> OpenMaya.MVector | None:
        return None if self._min is None else OpenMaya.MVector(self._min)

    @min.setter
    def min(
        self,
        v: Iterable[float] | OpenMaya.MVector | tuple[float, float, float] | None,
    ) -> None:
        self._min = _to_tuple3_or_none(v)

    @property
    def max(self) -> OpenMaya.MVector | None:
        return None if self._max is None else OpenMaya.MVector(self._max)

    @max.setter
    def max(
        self, v: Iterable[float] | OpenMaya.MVector | tuple[float, float, float] | None
    ) -> None:
        self._max = _to_tuple3_or_none(v)

    def to_dict(self) -> dict:
        """JSON-friendly snapshot (tuples & scalars only).

        Returns:
            A dictionary representation of the attribute descriptor.
        """

        d = super().to_dict()

        # Overwrite vector-like entries with tuple storage.
        d["value"] = self._value
        d["default"] = self._default
        d["softMin"] = self._softMin
        d["softMax"] = self._softMax
        d["min"] = self._min
        d["max"] = self._max

        return d


def _to_tuple3_or_none(v) -> tuple[float, float, float] | None:
    """Convert a value to a 3-tuple of floats or `None`.

    Args:
        v: The value to convert. Can be a 3-tuple, an iterable of length 3,
            an `OpenMaya.MVector` instance, or `None`.

    Returns:
        A 3-tuple of floats or `None`.

    Raises:
        ValueError: If the input is not a 3-tuple, an iterable of length
            3, an `OpenMaya.MVector` instance, or `None`.
    """

    if v is None:
        return None
    if isinstance(v, OpenMaya.MVector):
        return float(v.x), float(v.y), float(v.z)
    t = tuple(v)
    if len(t) != 3:
        raise ValueError("Expected a 3-tuple or iterable of length 3")
    return float(t[0]), float(t[1]), float(t[2])


def attribute_class_for_type(attr_type: int) -> type[AttributeDescriptor]:
    """Return the appropriate attribute descriptor class for the given
    attribute type.

    Args:
        attr_type: Maya attribute type as defined in
            `maya.api.OpenMaya.MFnData` or `maya.api.OpenMaya.MFnNumericData`.

    Returns:
        The attribute descriptor class.
    """

    return ATTRIBUTE_TYPES.get(attr_type, AttributeDescriptor)


def attribute_class_for_descriptor(descriptor: dict[str, Any]) -> AttributeDescriptor:
    """Return an attribute descriptor instance for the given descriptor
    attribute data.

    Args:
        descriptor: attribute descriptor data.
    """

    instance = attribute_class_for_type(descriptor.get("type", -1))

    return instance.deserialize(descriptor)


ATTRIBUTE_TYPES = {
    attributetypes.kMFnNumericBoolean: AttributeDescriptor,
    attributetypes.kMFnNumericByte: AttributeDescriptor,
    attributetypes.kMFnNumericShort: AttributeDescriptor,
    attributetypes.kMFnNumericInt: AttributeDescriptor,
    attributetypes.kMFnNumericDouble: AttributeDescriptor,
    attributetypes.kMFnNumericFloat: AttributeDescriptor,
    attributetypes.kMFnNumericAddr: AttributeDescriptor,
    attributetypes.kMFnNumericChar: AttributeDescriptor,
    attributetypes.kMFnNumeric2Double: AttributeDescriptor,
    attributetypes.kMFnNumeric2Float: AttributeDescriptor,
    attributetypes.kMFnNumeric2Int: AttributeDescriptor,
    attributetypes.kMFnNumeric2Short: AttributeDescriptor,
    attributetypes.kMFnNumeric3Double: VectorAttributeDescriptor,
    attributetypes.kMFnNumeric3Float: VectorAttributeDescriptor,
    attributetypes.kMFnNumeric3Int: AttributeDescriptor,
    attributetypes.kMFnNumeric3Short: AttributeDescriptor,
    attributetypes.kMFnNumeric4Double: AttributeDescriptor,
    attributetypes.kMFnUnitAttributeDistance: AttributeDescriptor,
    attributetypes.kMFnUnitAttributeAngle: AttributeDescriptor,
    attributetypes.kMFnUnitAttributeTime: AttributeDescriptor,
    attributetypes.kMFnkEnumAttribute: AttributeDescriptor,
    attributetypes.kMFnDataString: AttributeDescriptor,
    attributetypes.kMFnDataMatrix: AttributeDescriptor,
    attributetypes.kMFnDataFloatArray: AttributeDescriptor,
    attributetypes.kMFnDataDoubleArray: AttributeDescriptor,
    attributetypes.kMFnDataIntArray: AttributeDescriptor,
    attributetypes.kMFnDataPointArray: AttributeDescriptor,
    attributetypes.kMFnDataVectorArray: AttributeDescriptor,
    attributetypes.kMFnDataStringArray: AttributeDescriptor,
    attributetypes.kMFnDataMatrixArray: AttributeDescriptor,
    attributetypes.kMFnMessageAttribute: AttributeDescriptor,
}
