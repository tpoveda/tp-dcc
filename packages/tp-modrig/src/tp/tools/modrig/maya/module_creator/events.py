from __future__ import annotations

import typing
from dataclasses import dataclass, field

if typing.TYPE_CHECKING:
    from tp.libs.modrig.maya.api import Rig
    from tp.tools.modrig.maya.builder.models.rig import RigModel


@dataclass
class NeedRefreshEvent:
    rig_models: tuple[RigModel, ...]
    result: bool = False


@dataclass
class RefreshFromSceneEvent:
    rigs: list[Rig] = field(default_factory=list)


@dataclass
class AddRigEvent:
    name: str = ""
    set_current: bool = True
    rig: Rig | None = None


@dataclass
class AddModuleEvent:
    module_id: str
    rig_model: RigModel | None
