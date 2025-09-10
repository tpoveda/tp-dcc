from __future__ import annotations

import os
import typing
from typing import cast, Type
from dataclasses import dataclass

from tp.libs.plugin import PluginsManager

from ..models import ModuleModel, RigModel

if typing.TYPE_CHECKING:
    from tp.libs.modrig.maya.api import Module, ModulesManager


@dataclass
class ModuleModelData:
    """Dataclass that stores information about a module model."""

    module_model_class: Type[ModuleModel] | None = None
    module_class: Type[Module] | None = None
    type: str = ""


class ModulesModelsManager:
    """Class that manages the discovery and registration of module models."""

    MODULE_MODELS_ENV_VAR = "TP_MODRIG_MODULE_MODELS_PATHS"

    def __init__(self, modules_manager: ModulesManager):
        """Initializes the modules models manager.

        Args:
            modules_manager: The modules manager instance.
        """

        super().__init__()

        self._models: dict[str, ModuleModelData] = {}
        self._modules_manager = modules_manager
        self._manager = PluginsManager(
            interfaces=[ModuleModel], variable_name="moduleType"
        )

    @property
    def modules_manager(self) -> ModulesManager:
        """The modules manager instance."""

        return self._modules_manager

    def discover_modules(self) -> bool:
        """Discovers and registers module models from the specified paths.

        Returns:
            `True` if any module models were discovered and registered;
                `False` otherwise.
        """

        self._models.clear()
        models_paths = os.environ.get(self.MODULE_MODELS_ENV_VAR, "").split(os.pathsep)
        if not models_paths:
            return False
        self._manager.register_paths(models_paths)

        models = {
            module_model_class.moduleType: ModuleModelData(
                module_model_class=module_model_class
            )
            for module_model_class in cast(
                list[type[ModuleModel]], self._manager.plugin_classes
            )
        }
        for module_type, data in self._modules_manager.modules.items():
            if module_type in models:
                model_data = models[module_type]
                model_data.module_class = data["module_class"]
                model_data.type = module_type
            else:
                models[module_type] = ModuleModelData(
                    module_model_class=ModuleModel,
                    module_class=data["module_class"],
                    type=module_type,
                )

        self._models = models

        return True

    def find_module_model(
        self, module_type: str
    ) -> tuple[Type[ModuleModel] | None, str | None]:
        """Finds and returns the module model data for the specified module type.

        Args:
            module_type: The type of the module to find.

        Returns:
            The `ModuleModelData` instance for the specified module type, or
                `None` if not found.
        """

        module_data = self._models.get(module_type)
        if not module_data:
            return None, None

        return module_data.module_model_class, module_data.type

    def find_module(self, module_type: str) -> Type[Module] | None:
        """Finds and returns the module class for the specified module type.

        Args:
            module_type: The type of the module to find.

        Returns:
            The `Module` class for the specified module type, or `None` if not
                found.
        """

        module_data = self._models.get(module_type)
        if not module_data:
            return None

        return module_data.module_class

    def create_module_model(self, rig_model: RigModel, module: Module) -> ModuleModel:
        """Create and return a module model instance for the specified module.

        Args:
            rig_model: The rig model instance the module belongs to.
            module: The module instance to create the model for.

        Returns:
            The created module model instance.
        """

        module_type = module.module_type
        module_model_class, module_model_type = self.find_module_model(module_type)

        # If a specific module model class is found for the module type, use it.
        if module_model_class is not None:
            return module_model_class(module=module, rig_model=rig_model)

        # Fallback to the generic `ModuleModel` if no specific class is found.
        module_model = ModuleModel(module=module, rig_model=rig_model)
        module_model.moduleType = module_model_type

        return module_model
