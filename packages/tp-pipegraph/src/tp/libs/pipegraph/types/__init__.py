"""Type system for PipeGraph.

Provides type-safe port connections with compatibility checking.
"""

from .base import PortType
from .primitives import ANY, BOOL, EXEC, FLOAT, INT, STRING, PrimitiveType
from .wildcard import WildcardType

__all__ = [
    # Base
    "PortType",
    # Primitives
    "PrimitiveType",
    "BOOL",
    "INT",
    "FLOAT",
    "STRING",
    "ANY",
    "EXEC",
    # Wildcard
    "WildcardType",
]
