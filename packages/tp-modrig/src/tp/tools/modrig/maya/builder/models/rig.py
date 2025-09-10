from __future__ import annotations

import typing

from tp.libs.python import profiler
from tp.libs.modrig.commands import modrig

if typing.TYPE_CHECKING:
    from tp.libs.modrig.maya.api import Rig, RigConfiguration, MetaRig
    from .module import ModuleModel


class RigModel:
    def __init__(self, rig: Rig | None = None):
        super().__init__()

        self._rig = rig
        self._module_models: list[ModuleModel] = []

    @property
    def configuration(self) -> RigConfiguration | None:
        """The rig configuration instance."""

        return self._rig.configuration if self._rig else None

    @property
    def name(self) -> str:
        """The rig name."""

        return self._rig.name() if self._rig else ""

    @property
    def meta(self) -> MetaRig | None:
        """The rig metanode instance."""

        return self._rig.meta if self._rig else None

    @property
    def rig(self) -> Rig | None:
        """The rig instance."""

        return self._rig

    @property
    def module_models(self) -> list[ModuleModel]:
        """The list of module models associated with the rig."""

        return self._module_models

    def exists(self) -> bool:
        """Return whether the rig exists in the scene."""

        return self._rig is not None and self._rig.exists()

    def add_module_model(self, module_model: ModuleModel) -> None:
        """Adds a module model to the rig model.

        Args:
            module_model: The module model to add.
        """

        self._module_models.append(module_model)

    def module(self, name: str, side: str) -> ModuleModel | None:
        """Returns the module model with the given name and side.

        Args:
            name: Name of the module.
            side: Side of the module.

        Returns:
            The module model instance if found; `None` otherwise.
        """

        found_module_model: ModuleModel | None = None
        for module_model in self._module_models:
            if module_model.name == name and module_model.side == side:
                found_module_model = module_model
                break

        return found_module_model

    @profiler.fn_timer
    def delete(self):
        """Deletes the rig from the scene."""

        if not self._rig:
            return False

        success = modrig.delete_rig(rig=self._rig)
        if success:
            self._rig = None
            self._module_models = []

        return success
