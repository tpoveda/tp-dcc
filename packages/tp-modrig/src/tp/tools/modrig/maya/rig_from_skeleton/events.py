from __future__ import annotations

from typing import Callable

from dataclasses import dataclass, field


@dataclass
class GetSelectionFromSceneEvent:
    """
    Event class that defines an event to get the selection from the scene.
    """

    selection: list[str] = field(default_factory=list)


@dataclass
class BuildRigFromSkeletonEvent:
    """
    Event class that defines an event to build guides for a skeleton.
    """

    source_joints: list[str]
    target_ids: list[str]
    order: list[str]
    rig_name: str
    source_namespace: str
    source_prefix: str
    source_suffix: str
    update_function: Callable
    success: bool = False
