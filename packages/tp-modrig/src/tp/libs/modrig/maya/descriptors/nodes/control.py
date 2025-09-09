from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field

from .transform import TransformDescriptor


@dataclass
class ControlDescriptor(TransformDescriptor):
    """Class that defines an output descriptor.

    Attributes:
        name: Name of the descriptor.
        modType: Type of the descriptor.
        shape: Shape of the control.
    """

    name: str = "control"
    modType: str = "control"
    srts: list[TransformDescriptor] = field(default_factory=list)

    # === Visuals === #
    shape: str = "circle"
    color: (
        tuple
        | tuple[int, int, int]
        | tuple[float, float, float]
        | tuple[int, int, int, int]
        | tuple[float, float, float, float]
    ) = field(default_factory=tuple)
    shapeTransform: dict | None = field(
        default_factory=lambda: {
            "translate": (0.0, 0.0, 0.0),
            "scale": (1.0, 1.0, 1.0),
            "rotate": (0.0, 0.0, 0.0, 1.0),
            "rotateOrder": 0,
        }
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the descriptor into a dictionary.

        Returns:
            A `dict` compatible with `deserialize()`.
        """

        out = super().to_dict()

        out["srts"] = [s.to_dict() for s in self.srts]

        return out
