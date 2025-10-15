from __future__ import annotations

import typing
from typing import Any
from abc import ABC, abstractmethod

if typing.TYPE_CHECKING:
    from Qt.QtWidgets import QGraphicsItem


class ISerializable(ABC):
    """Interface for serializable objects."""

    @abstractmethod
    def serialize(self) -> dict[str, Any]:
        """Serializes the object to a dictionary.

        Returns:
            Dictionary representation of the object.
        """

    @abstractmethod
    def deserialize(self, data: dict[str, Any]) -> None:
        """Deserializes the object from a dictionary.

        Args:
            data: Dictionary representation of the object.
        """


class IItemBase(ISerializable, ABC):
    """Interface for items in the node graph with views."""

    def get_view(self) -> QGraphicsItem | None:
        """Returns the graphics item view for this item.

        Returns:
            `QGraphicsItem` instance.
        """

    def set_view(self, view: QGraphicsItem) -> None:
        """Sets the graphics item view for this item.

        Args:
            view: `QGraphicsItem` instance.
        """


class INode(IItemBase, ABC):
    """Interface for node items in the node graph."""
