from __future__ import annotations

import typing
from abc import ABC
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from .dtype import DType, dtype_from_string, list_of
from .enums import PortKind, PortDirection
from .errors import PortValidationError, ValidationError

if typing.TYPE_CHECKING:
    from .node import Node


from typing import Any


class Port(ABC):
    """A `Port` allows connecting one node to another."""

    def __init__(
        self,
        dtype: DType | str | None = None,
        *,
        multi: bool = False,
        default: Any | None = None,
        validator: Callable[[Any], None] | None = None,
        kind: PortKind = PortKind.Data,
        direction: PortDirection = PortDirection.In,
        required: bool | None = None,
        doc: str = "",
    ):
        super().__init__()

        if kind is PortKind.Data and dtype is None:
            raise ValueError("DATA port requires a dtype.")

        self._dtype = dtype
        self._multi = multi
        self._default = default
        self._validator = validator
        self._kind = kind
        self._direction = direction
        self._required = required
        self._doc = doc
        self._name: str | None = None
        self._spec: PortSpec | None = None

    def __set_name__(self, owner: type[Node], attr_name: str) -> None:
        """Set the name of the port descriptor when it is assigned to a class.

        Args:
            owner: The class that owns this descriptor.
            attr_name: The name of the attribute in the class.

        Raises:
            ValueError: If the port kind is EXEC and a dtype is specified.
            ValueError: If a DATA port is defined without a dtype.
            ValueError: If a DATA port is defined without a dtype, and no spec is given.
        """

        self._name = attr_name

        # Enforce no whitespace and non-empty.
        if not self._name or any(ch.isspace() for ch in self._name):
            raise ValueError(
                f"Invalid port name '{self._name}': whitespace not allowed."
            )

        if self._kind is PortKind.Data:
            # Resolve data type.
            dtype_obj: DType | None
            if isinstance(self._dtype, str):
                dtype_obj = dtype_from_string(self._dtype)
            else:
                dtype_obj = self._dtype
            if dtype_obj is None:
                raise ValueError(
                    f"DATA port '{attr_name}' requires a dtype."
                )  # pragma: no cover
            self._spec = PortSpec(
                name=attr_name,
                dtype=dtype_obj,
                multi=self._multi,
                default=self._default,
                validator=self._validator,
            )
        else:
            # EXEC ports do not carry data or have a spec.
            self._spec = None

    @property
    def kind(self) -> PortKind:
        """The kind of the port (Data or Exec)."""

        return self._kind

    @property
    def direction(self) -> PortDirection:
        """The direction of the port (In or Out)."""

        return self._direction

    @property
    def spec(self) -> PortSpec | None:
        """The port specification, if applicable (None for Exec ports)."""

        return self._spec

    @property
    def doc(self) -> str:
        """Documentation string for the port, describing its purpose."""

        return self._doc

    def is_required(self) -> bool:
        """Determine if this port is required.

        Returns:
            `True` if the port is required; `False` otherwise.
        """

        if self.kind is PortKind.Exec:
            return False

        if self._required is not None:
            return bool(self._required)

        # Inference: Data with no default => required.
        return self._spec is not None and self._spec.default is None


class InputPort(Port):
    """Descriptor for input ports."""

    def __init__(self, dtype: DType | str | None = None, **kwargs: Any) -> None:
        kwargs.setdefault("direction", PortDirection.In)
        super().__init__(dtype, **kwargs)


class OutputPort(Port):
    """Descriptor for output ports."""

    def __init__(self, dtype: DType | str | None = None, **kwargs: Any) -> None:
        kwargs.setdefault("direction", PortDirection.Out)
        super().__init__(dtype, **kwargs)


UserValidator = Callable[[Any], None]  # raise ValueError/TypeValidationError on failure


@dataclass(frozen=True, slots=True)
class PortSpec:
    """Declarative description of a port.

    Args:
        name: Unique port name within the node's input or output namespace.
        dtype: Declared data type of the value carried by this port.
        multi: If True, the port accepts an array of `dtype` values.
        default: Optional default value; validated at construction-time if provided.
        validator: Optional user validator for additional constraints (e.g., ranges).

    Methods:
        validate(value): Validates a candidate value, raising
            `PortValidationError` on failure.
        To_schema(): JSON Schema snippet for this port
            (includes 'default' when set).
    """

    name: str
    dtype: DType
    multi: bool = False
    default: Any | None = None
    validator: UserValidator | None = None

    def __post_init__(self) -> None:
        # Validate default eagerly so bad defaults fail fast at node
        # definition time.
        if self.default is not None:
            try:
                self.validate(self.default)
            except (
                PortValidationError
            ) as e:  # pragma: no cover - construction error path
                raise e

    # --- API ---

    def validate(self, value: Any) -> None:
        """Validate a candidate value against this port's spec.

        Args:
            value: The value to validate against this port's type and
                constraints.
        """

        target_dtype = list_of(self.dtype) if self.multi else self.dtype
        try:
            target_dtype.validate(value, "value")
            if self.validator is not None:
                # Let the user validator raise any
                # ValueError/TypeValidationError with detail
                self.validator(value)
        except (ValidationError, ValueError) as err:
            # Wrap with contextual `PortValidationError` while preserving
            # the underlying cause
            msg = getattr(err, "message", str(err))
            expected = getattr(err, "expected", None)
            actual = getattr(err, "actual", None)
            path = getattr(err, "path", "value")
            raise PortValidationError(
                self.name,
                message=msg,
                expected=expected,
                actual=actual,
                path=path,
            ) from err

    def to_schema(self) -> Mapping[str, Any]:
        """Return a JSON Schema snippet for this port.

        Returns:
            A dictionary representing the JSON Schema for this port,
            including 'title', 'default' (if set), and custom metadata
            for UI tools.
        """

        base = list_of(self.dtype).to_schema() if self.multi else self.dtype.to_schema()
        schema = dict(base)
        schema.setdefault("title", self.name)
        if self.default is not None:
            schema["default"] = self.default
        # Non-standard hint that can help UIs
        schema.setdefault("x-pipegraph", {})
        schema["x-pipegraph"]["multi"] = self.multi
        schema["x-pipegraph"]["dtype"] = self.dtype.name
        return schema
