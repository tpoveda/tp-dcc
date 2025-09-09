from __future__ import annotations

from dataclasses import dataclass

from .transform import TransformDescriptor


@dataclass
class OutputDescriptor(TransformDescriptor):
    """Class that defines an output descriptor."""

    name: str = "output"
    modType: str = "output"
    root: bool = False
