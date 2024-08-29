from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DropNodeEvent:
    """
    Event class that defines a drop node event.
    """

    node_id: str
    json_data: dict
    position: tuple[float, float]
