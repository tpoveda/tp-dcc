from __future__ import annotations

from dataclasses import dataclass

from .transform import TransformDescriptor


@dataclass
class InputDescriptor(TransformDescriptor):
    """Class that defines an input descriptor."""

    name: str = "input"
    modType: str = "input"
    root: bool = False
