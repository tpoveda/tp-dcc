from __future__ import annotations

import typing
from abc import ABC
from typing import Any, ClassVar
from weakref import ReferenceType

from ..views import NodeView
from .interfaces import INode
from ..models import NodeModel
from .port import InputPort, OutputPort

from tp.libs.python.decorators import classproperty

if typing.TYPE_CHECKING:
    from . import NodeId
    from .graph import Graph


class AbstractNode(INode, ABC):
    """Base class for all nodes in the node graph."""

    # Package where this node belongs to.
    __package__ = "tp.nodegraph.nodes"

    # Initial base node name.
    NODE_NAME: str | None = None

    def __init__(self, view_class: type[NodeView]):
        super().__init__()

        self._graph: ReferenceType[Graph] | None = None
        self._model = NodeModel()
        self._view_class = view_class
        self._view = view_class()

    # noinspection PyMethodParameters
    @classproperty
    def type_name(cls) -> str:
        """The unique type name of the node."""

        return f"{cls.__package__}.{cls.__name__}"

    @property
    def id(self) -> NodeId:
        """The unique identifier of the node."""

        return self._model.id

    @property
    def graph(self) -> Graph | None:
        """The parent graph this node belongs to."""

        return self._graph

    @graph.setter
    def graph(self, value: Graph | None) -> None:
        """Set the parent graph for this node."""

        self._graph = value

    @property
    def model(self) -> NodeModel:
        """The model associated with this node."""

        return self._model

    def name(self):
        """Return the name of the node.

        Returns:
            Name of the node.
        """

        return self.model.name

    def update_model(self) -> None:
        """Update the node model from the node view."""

    def update_view(self) -> None:
        """Update the node view from the node model."""


class Node(AbstractNode):
    """Class that defines a node in the node graph."""

    NODE_NAME = "Node"

    # Class-level dictionaries to store port definitions
    __declared_inputs__: ClassVar[dict[str, dict[str, Any]]] = {}
    __declared_outputs__: ClassVar[dict[str, dict[str, Any]]] = {}

    def __init__(self, view_class: type[NodeView]) -> None:
        super().__init__(view_class=view_class or NodeView)

    # === Ports === #

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Collect and merge port declarations from base classes."""

        super().__init_subclass__(**kwargs)

        inputs: dict[str, dict[str, Any]] = {}
        outputs: dict[str, dict[str, Any]] = {}

        # Inherit base declarations (preserve order).
        for base in cls.__mro__[1:]:
            if hasattr(base, "__declared_inputs__"):
                inputs.update(base.__declared_inputs__)
            if hasattr(base, "__declared_outputs__"):
                outputs.update(base.__declared_outputs__)

        # Collect this class' descriptors.
        for name, attr in cls.__dict__.items():
            if isinstance(attr, InputPort):
                inputs[name] = {
                    "spec": attr.spec,
                    "kind": attr.kind,
                    "direction": attr.direction,
                    "required": attr.is_required(),
                    "doc": attr.doc,
                    "contract": True,
                }
            elif isinstance(attr, OutputPort):
                outputs[name] = {
                    "spec": attr.spec,
                    "kind": attr.kind,
                    "direction": attr.direction,
                    "doc": attr.doc,
                    "contract": True,
                }

        cls.__declared_inputs__ = inputs
        cls.__declared_outputs__ = outputs

    # === Serialization === #

    def deserialize(self, data: dict[str, Any]) -> None:
        pass

    def serialize(self) -> dict[str, Any]:
        pass
