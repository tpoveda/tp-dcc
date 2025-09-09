from __future__ import annotations

from typing import Union

from .dg import DGNodeDescriptor
from .transform import TransformDescriptor
from .joint import JointDescriptor
from .input import InputDescriptor
from .output import OutputDescriptor
from .control import ControlDescriptor
from .guide import GuideDescriptor

NodeDescriptorType = Union[
    DGNodeDescriptor,
    TransformDescriptor,
    JointDescriptor,
    InputDescriptor,
    OutputDescriptor,
    ControlDescriptor,
    GuideDescriptor,
]

__all__ = [
    "NodeDescriptorType",
    "DGNodeDescriptor",
    "TransformDescriptor",
    "JointDescriptor",
    "InputDescriptor",
    "OutputDescriptor",
    "ControlDescriptor",
    "GuideDescriptor",
]
