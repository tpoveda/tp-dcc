from __future__ import annotations

import typing

from Qt.QtCore import QObject

if typing.TYPE_CHECKING:
    from tp.libs.modrig.maya.api import Module
    from .rig import RigModel


class ModuleModel(QObject):

    moduleType: str = ''

    def __init__(self, module: Module | None = None, rig_model: RigModel | None = None):
        super().__init__()

        self._module = module
        self._rig_model = rig_model

    @property
    def module(self) -> Module | None:
        """The module instance."""

        if self._module is None or self._rig_model is None:
            return None

        # Ensure we always have the latest module instance from the scene.
        self._module = self._rig_model.rig.module(
            self._module.name(), self._module.side()
        )

        return self._module

    @property
    def name(self) -> str:
        """The module name."""

        module = self.module
        return module.name() if module is not None else ''

    @property
    def side(self) -> str:
        """The module side."""

        module = self.module
        return module.side() if module is not None else ''
