from __future__ import annotations

from dataclasses import dataclass

from .transform import TransformDescriptor


@dataclass
class JointDescriptor(TransformDescriptor):
    """Class that defines a joint descriptor."""

    name: str = "joint"
    modType: str = "joint"
