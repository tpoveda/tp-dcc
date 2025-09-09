from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field, asdict

from ..attributes import AttributeDescriptor


@dataclass
class DGNodeDescriptor:
    """Dataclass that represents a Maya DG node descriptor."""

    # === Core === #
    id: str = ""
    name: str = ""
    parent: str | None = None
    type: str = "transform"
    modType: str = "transform"

    # === Attributes === #
    attributes: list[AttributeDescriptor] = field(default_factory=list)

    def attribute(self, name: str) -> AttributeDescriptor | None:
        """Get an attribute by its name.

        Args:
            name: The name of the attribute.

        Returns:
            The attribute descriptor if found; `None` otherwise.
        """

        found_attr: AttributeDescriptor | None = None
        for attr in self.attributes:
            if attr.name == name:
                found_attr = attr
                break

        return found_attr

    def to_dict(self) -> dict:
        """Convert the node descriptor to a dictionary.

        Returns:
            A dictionary representation of the node descriptor.
        """

        out = asdict(self)
        out["attributes"] = [a.to_dict() for a in self.attributes]
        return out
