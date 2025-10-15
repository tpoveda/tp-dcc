from __future__ import annotations

import re
from collections.abc import Callable, Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, TypeAlias

from .errors import TypeValidationError

__all__ = [
    "DType",
    "JSONLike",
    "dict_of",
    "dtype_from_string",
    "get_dtype",
    "is_dtype_compatible",
    "list_of",
    "register_dtype",
]

# ---- JSON typing

JSONPrimitive: TypeAlias = str | int | float | bool | None
JSONLike: TypeAlias = JSONPrimitive | list["JSONLike"] | dict[str, "JSONLike"]

# ---- DType core

Validator = Callable[[Any, str], None]
SchemaBuilder = Callable[[], Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class DType:
    """Runtime-validated, serializable data type descriptor.

    - `validator(value, path)` raises TypeValidationError on failure.
    - `to_schema()` returns a JSON Schema snippet usable for docs/validation.
    """

    name: str
    _validator: Validator
    _schema: SchemaBuilder

    # --- API ---

    def validate(self, value: Any, path: str = "value") -> None:
        """Validate a value against this data type.

        Args:
            value: The value to validate.
            path: The path to the value in a nested structure
                (for error messages).
        """

        self._validator(value, path)

    def to_schema(self) -> Mapping[str, Any]:
        """Return a JSON Schema snippet describing this data type.

        Returns:
            A mapping representing the JSON Schema for this data type.
            This can be used for documentation or validation.
        """

        return dict(self._schema())  # defensive copy

    # --- helpers ---

    def __str__(self) -> str:
        """Return a string representation of the data type."""

        return self.name


# ---- Registry

_REGISTRY: MutableMapping[str, DType] = {}


def register_dtype(dtype: DType) -> None:
    """Register a new `DType` in the global registry.

    Raises:
        ValueError: If a dtype with the same name is already registered.
    """

    if dtype.name in _REGISTRY:
        raise ValueError(f"DType '{dtype.name}' already registered.")

    _REGISTRY[dtype.name] = dtype


def get_dtype(name: str) -> DType:
    """Get a registered `DType` by name.

    Args:
        name: The name of the data type to retrieve.

    Returns:
        The `DType` instance registered under the given name.

    Raises:
        KeyError: If no dtype with the given name is registered.
    """

    try:
        return _REGISTRY[name]
    except KeyError as exc:  # pragma: no cover - exercised via dtype_from_string tests
        raise KeyError(f"Unknown dtype: '{name}'") from exc


# ---- Primitive constructors


def _primitive_dtype(name: str, py_types: tuple[type, ...], json_type: str) -> DType:
    """Create a primitive `DType` for basic Python types."""

    def _v(value: Any, path: str) -> None:
        """Validate that `value` is of the expected Python type(s).

        Args:
            value: The value to validate.
            path: The path to the value in a nested structure
                (for error messages).
        """

        if not isinstance(value, py_types):
            raise TypeValidationError(
                message=f"Expected {name}",
                expected=name,
                actual=type(value).__name__,
                path=path,
            )

    def _s() -> Mapping[str, Any]:
        """Return a JSON Schema snippet for this primitive type."

        Returns:
            A mapping representing the JSON Schema for this primitive type.
        """

        return {"type": json_type}

    return DType(name=name, _validator=_v, _schema=_s)


# ---- Path dtype (can accept str or Path)


def _path_dtype() -> DType:
    """Create a `DType` for path-like values (str or pathlib.Path)."""

    name = "path"

    def _v(value: Any, path: str) -> None:
        """Validate that `value` is a path-like object (str or Path).

        Args:
            value: The value to validate.
            path: The path to the value in a nested structure
                (for error messages).
        """

        if not isinstance(value, str | Path):
            raise TypeValidationError(
                message="Expected path-like (str or pathlib.Path)",
                expected=name,
                actual=type(value).__name__,
                path=path,
            )

    def _s() -> Mapping[str, Any]:
        """Return a JSON Schema snippet for path-like values.

        Returns:
            A mapping representing the JSON Schema for path-like values.
        """

        # Non-standard "format": "path" hint; useful for UIs
        return {"type": "string", "format": "path"}

    return DType(name=name, _validator=_v, _schema=_s)


# ---- JSON dtype


def _is_json_like(value: Any, path: str) -> None:
    """Recursively validate that `value` is JSON-compatible.

    Args:
        value: The value to validate.
        path: The path to the value in a nested structure
            (for error messages).
    """

    # Fast path for primitives
    if value is None or isinstance(value, str | int | float | bool):
        return
    # list/tuple
    if isinstance(value, list | tuple):
        for i, item in enumerate(value):
            _is_json_like(item, f"{path}[{i}]")
        return
    # dict with str keys
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise TypeValidationError(
                    message="JSON object keys must be strings",
                    expected="str key",
                    actual=type(k).__name__,
                    path=f"{path}[{str(k)!r}]",
                )
            _is_json_like(v, f"{path}[{str(k)!r}]")
        return
    # everything else is not JSON-serializable (by our contract)
    raise TypeValidationError(
        message="Value is not JSON-compatible",
        expected="JSON-serializable",
        actual=type(value).__name__,
        path=path,
    )


def _json_dtype() -> DType:
    """Create a `DType` for JSON-like values.

    Returns:
        A `DType` instance that validates JSON-like structures.
    """

    def _v(value: Any, path: str) -> None:
        """Validate that `value` is JSON-compatible.

        Args:
            value: The value to validate.
            path: The path to the value in a nested structure
                (for error messages).
        """

        _is_json_like(value, path)

    def _s() -> Mapping[str, Any]:
        """Return a JSON Schema snippet for JSON-like values."""

        # Broad JSON schema union.
        return {"type": ["string", "number", "boolean", "object", "array", "null"]}

    return DType(name="json", _validator=_v, _schema=_s)


# ---- Containers


def list_of(item: DType) -> DType:
    """Create a `DType` for lists/tuples of a specific item type.

    Args:
        item: The `DType` of the items in the list/tuple.
    """

    name = f"list[{item.name}]"

    def _v(value: Any, path: str) -> None:
        """Validate that `value` is a list or tuple of the specified item type.

        Args:
            value: The value to validate.
            path: The path to the value in a nested structure
                (for error messages).
        """

        if not isinstance(value, list | tuple):
            raise TypeValidationError(
                message=f"Expected array (list/tuple) of {item.name}",
                expected=name,
                actual=type(value).__name__,
                path=path,
            )

        for i, elem in enumerate(value):
            item.validate(elem, f"{path}[{i}]")

    def _s() -> Mapping[str, Any]:
        """Return a JSON Schema snippet for lists/tuples of the specified
        item type.

        Returns:
            A mapping representing the JSON Schema for lists/tuples of the
                specified item type.
        """

        return {"type": "array", "items": item.to_schema()}

    return DType(name=name, _validator=_v, _schema=_s)


def dict_of(value_dtype: DType) -> DType:
    """Create a `DType` for dictionaries with string keys and specific
    value type.

    Args:
        value_dtype: The `DType` of the values in the dictionary.

    Returns:
        A `DType` instance that validates dictionaries with string keys
        and values of the specified type.
    """

    name = f"dict[str,{value_dtype.name}]"

    def _v(value: Any, path: str) -> None:
        """Validate that `value` is a dictionary with string keys and
        values of the specified type.

        Args:
            value: The value to validate.
            path: The path to the value in a nested structure
        """

        if not isinstance(value, dict):
            raise TypeValidationError(
                message=(
                    f"Expected object with string keys and {value_dtype.name} values"
                ),
                expected=name,
                actual=type(value).__name__,
                path=path,
            )
        for k, v in value.items():
            if not isinstance(k, str):
                raise TypeValidationError(
                    message="Object key must be str",
                    expected="str",
                    actual=type(k).__name__,
                    path=f"{path}[{str(k)!r}]",
                )
            value_dtype.validate(v, f"{path}[{str(k)!r}]")

    def _s() -> Mapping[str, Any]:
        """Return a JSON Schema snippet for dictionaries with string keys
        and values of the specified type.

        Returns:
            A mapping representing the JSON Schema for dictionaries with
            string keys and values of the specified type.
        """

        return {"type": "object", "additionalProperties": value_dtype.to_schema()}

    return DType(name=name, _validator=_v, _schema=_s)


# ---- Built-ins registration

_INT = _primitive_dtype("int", (int,), "integer")
_FLOAT = _primitive_dtype("float", (float, int), "number")  # accept int as number
_BOOL = _primitive_dtype("bool", (bool,), "boolean")
_STR = _primitive_dtype("str", (str,), "string")
_PATH = _path_dtype()
_JSON = _json_dtype()

for _dt in (_INT, _FLOAT, _BOOL, _STR, _PATH, _JSON):
    register_dtype(_dt)


# ---- String parsing for simple generic expressions

# Supports:
#  - "int", "float", "bool", "str", "path", "json"
#  - "list[T]"
#  - "dict[str,T]"
# noinspection RegExpRedundantEscape
_DTYPE_NAME_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    ^
    (?P<base>int|float|bool|str|path|json|list|dict)      # base type, incl. containers
    (?:\[(?P<a>[^,\[\]]+)(?:,(?P<b>[^,\[\]]+))?\])?       # optional generic args
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)


def dtype_from_string(expr: str) -> DType:
    """Parse a string expression into a `DType`.

    Args:
        expr: The string expression to parse,
            e.g. "int", "list[str]", "dict[str, int]".

    Returns:
        A `DType` instance corresponding to the parsed expression.
    """

    expr = expr.strip()
    m = _DTYPE_NAME_RE.match(expr)
    if not m:
        raise KeyError(f"Cannot parse dtype expression: '{expr}'")
    base = m.group("base").lower()
    a = m.group("a")
    b = m.group("b")

    if base in _REGISTRY and not a and not b:
        return get_dtype(base)

    # list[T]
    if base == "list" and a and not b:
        return list_of(dtype_from_string(a))

    # dict[str,T]
    if base == "dict" and a and b:
        key = a.strip().lower()
        if key != "str":
            raise KeyError("Only 'dict[str,T]' is supported for keys.")
        return dict_of(dtype_from_string(b))

    # If someone writes "List[int]" or "Dict[str,int]" with caps -> normalize:
    if (
        base == "int"
        or base == "float"
        or base == "bool"
        or base == "str"
        or base == "path"
        or base == "json"
    ):
        # Already handled above; this branch shouldn't occur.
        return get_dtype(base)

    # Extras: allow capitalized generics (dict is handled above).
    if base == "list" and a:
        return list_of(dtype_from_string(a))

    raise KeyError(f"Unknown dtype expression: '{expr}'")


# ===
# Assignability / compatibility
# ===


# noinspection PyBroadException
def is_dtype_compatible(src: DType | Any, dst: DType | Any) -> bool:
    """Structural, assignment-style compatibility:
    - exact match by name
    - custom hooks (dst.accepts(src) | src.is_assignable_to(dst) |
        dst.is_supertype_of(src))
    - numeric widening: int -> float
    - path acceptance: str -> path
    - containers: list[S] -> list[D] iff S -> D ; dict[str,S]
        -> dict[str,D] iff S -> D
    - JSON top-type: T -> json iff T is guaranteed JSON-compatible
    """

    if src is dst or src.name == dst.name:
        return True

    # 1) Duck-typed custom relations (allow domain-specific DTYPES to override)
    if hasattr(dst, "accepts"):
        try:
            if bool(dst.accepts(src)):
                return True
        except Exception:
            pass
    if hasattr(src, "is_assignable_to"):
        try:
            if bool(src.is_assignable_to(dst)):
                return True
        except Exception:
            pass
    if hasattr(dst, "is_supertype_of"):
        try:
            if bool(dst.is_supertype_of(src)):
                return True
        except Exception:
            pass

    s_base, s_args = _decompose_type_name(src.name)
    d_base, d_args = _decompose_type_name(dst.name)

    # 2) Special widenings
    # int -> float
    if s_base == "int" and d_base == "float":
        return True
    # str -> path (path values may be str or pathlib.Path; safe to accept strings)
    if s_base == "str" and d_base == "path":
        return True

    # 3) Containers (recursive)
    if s_base == d_base == "list":
        if len(s_args) == len(d_args) == 1:
            return _compatible_by_names(s_args[0], d_args[0])
        return False
    if s_base == d_base == "dict":
        # Only dict[str, T] supported by our type system
        if (
            len(s_args) == len(d_args) == 2
            and s_args[0].lower() == d_args[0].lower() == "str"
        ):
            return _compatible_by_names(s_args[1], d_args[1])
        return False

    # 4) JSON as a top type (but only when source is guaranteed JSON-compatible)
    if d_base == "json" and _is_json_compatible_name(src.name):
        return True

    # Default: nominal typing by (lowercased) name
    return s_base == d_base and s_args == d_args


def _decompose_type_name(name: str) -> tuple[str, list[str]]:
    """Return (base, args) from a dtype name. Supports nesting by scanning
    brackets.

    Examples:
      "int" -> ("int", [])
      "list[str]" -> ("list", ["str"])
      "dict[str,int]" -> ("dict", ["str", "int"])
      "list[dict[str,float]]" -> ("list", ["dict[str,float]"])
    """

    name = name.strip()
    if "[" not in name:
        return name.lower(), []
    # base[args...]
    lb = name.find("[")
    rb = name.rfind("]")
    base = name[:lb].strip().lower()
    inner = name[lb + 1 : rb].strip()
    # split inner on top-level commas
    args: list[str] = []
    depth = 0
    token = []
    for ch in inner:
        if ch == "[":
            depth += 1
            token.append(ch)
        elif ch == "]":
            depth -= 1
            token.append(ch)
        elif ch == "," and depth == 0:
            args.append("".join(token).strip())
            token = []
        else:
            token.append(ch)
    if token:
        args.append("".join(token).strip())
    return base, args


def _compatible_by_names(src_name: str, dst_name: str) -> bool:
    """Name-only recursive compatibility (used for containers)."""

    # fast path exact
    if src_name == dst_name:
        return True
    s_base, s_args = _decompose_type_name(src_name)
    d_base, d_args = _decompose_type_name(dst_name)
    # int->float, str->path
    if s_base == "int" and d_base == "float":
        return True
    if s_base == "str" and d_base == "path":
        return True
    # list[T] variance
    if s_base == d_base == "list":
        if len(s_args) == len(d_args) == 1:
            return _compatible_by_names(s_args[0], d_args[0])
        return False
    # dict[str,T] variance
    if s_base == d_base == "dict" and len(s_args) == len(d_args) == 2:
        if s_args[0].lower() != "str" or d_args[0].lower() != "str":
            return False
        return _compatible_by_names(s_args[1], d_args[1])
    # json as top type
    if d_base == "json" and _is_json_compatible_name(src_name):
        return True
    return s_base == d_base and s_args == d_args


def _is_json_compatible_name(name: str) -> bool:
    """True iff all values of this dtype are JSON-serializable by our contract."""

    base, args = _decompose_type_name(name)
    if base in {"int", "float", "bool", "str", "json"}:
        return True
    if base == "list" and len(args) == 1:
        return _is_json_compatible_name(args[0])
    if base == "dict" and len(args) == 2 and args[0].lower() == "str":
        return _is_json_compatible_name(args[1])
    # 'path' can be pathlib.Path -> not guaranteed JSON
    return False
