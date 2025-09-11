from __future__ import annotations

from .base.rig import Rig, iterate_scene_rigs, iterate_scene_rig_meta_nodes
from .base.module import Module, ModuleUiData
from .base.configuration import RigConfiguration
from .managers.modules import ModulesManager, RegisteredModule
from .meta.rig import MetaRig
from .meta.nodes import GuideNode
from .services.naming import unique_name_for_rig
from .descriptors import ModuleDescriptor


__all__ = [
    "Rig",
    "Module",
    "ModuleUiData",
    "RigConfiguration",
    "ModulesManager",
    "RegisteredModule",
    "MetaRig",
    "GuideNode",
    "ModuleDescriptor",
    "iterate_scene_rigs",
    "iterate_scene_rig_meta_nodes",
    "unique_name_for_rig",
]
