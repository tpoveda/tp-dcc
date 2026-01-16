"""Variable classes for graph-scoped named values.

Variables allow storing and retrieving values by name within a graph.
"""

import typing
from dataclasses import dataclass, field
from typing import Any

from ..types import ANY, PortType
from .base import Identifiable

if typing.TYPE_CHECKING:
    from .graph import Graph


@dataclass
class Variable(Identifiable):
    """A named variable stored at graph scope.

    Variables can be:
    - Read by GetVariable nodes
    - Written by SetVariable nodes
    - Watched for changes
    """

    name: str
    var_type: PortType = field(default=ANY)
    _value: Any = field(default=None, repr=False)
    description: str = ""
    _graph: Graph | None = field(default=None, repr=False)
