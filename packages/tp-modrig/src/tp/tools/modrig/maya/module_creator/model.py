from __future__ import annotations

from loguru import logger
from Qt.QtCore import Signal

from tp.libs.qt import Model, UiProperty
from tp.libs.modrig.maya.api import RigConfiguration, ModulesManager
from tp.tools.modrig.maya.builder.models import RigModel, ModuleModel
from tp.tools.modrig.maya.builder.managers.modules import ModulesModelsManager

from . import events


class ModuleCreatorModel(Model):
    """Model class that stores all the data related to the module creator tool."""

    needRefresh = Signal(events.NeedRefreshEvent)
    refreshFromScene = Signal(events.RefreshFromSceneEvent)
    addRig = Signal(events.AddRigEvent)
    addModule = Signal(events.OpenModuleEvent)

    rigAdded = Signal()
    rigDeleted = Signal()

    # noinspection PyAttributeOutsideInit
    def initialize_properties(self) -> list[UiProperty]:
        """Initialize the properties associated with the instance.

        Returns:
            A list of initialized UI properties.
        """

        self._config = RigConfiguration()
        self._modules_manager = ModulesModelsManager(
            modules_manager=self._config.modules_manager()
        )
        self._modules_manager.discover_modules()

        return [
            UiProperty("editor_mode", 0, type=int),
            UiProperty("rigs", [], type=list[RigModel]),
            UiProperty("current_rig", None, type=RigModel),
            UiProperty("current_module", None, type=ModuleModel),
        ]

    @property
    def rigs(self) -> list[RigModel]:
        """The list of rig models."""

        return self.properties.rigs.value

    @property
    def current_rig(self) -> RigModel | None:
        """The current rig model instance."""

        return self.properties.current_rig.value

    @property
    def current_module(self) -> ModuleModel | None:
        """The current module model instance."""

        return self.properties.current_module.value

    @property
    def configuration(self) -> RigConfiguration:
        """The rig configuration used."""

        return self._config

    @property
    def modules_models_manager(self) -> ModulesModelsManager:
        """The modules model manager instance."""

        return self._modules_manager

    @property
    def modules_manager(self) -> ModulesManager:
        """The modules manager instance."""

        return self.modules_models_manager.modules_manager

    def needs_refresh(self):
        event = events.NeedRefreshEvent(rig_models=tuple(self.rigs))
        self.needRefresh.emit(event)
        return event.result

    def refresh_from_scene(self, force: bool = False) -> None:
        """Refresh the model from the current scene state.

        Args:
            force: Whether to force the refresh.
        """

        # Avoid refreshing if not needed.
        if not force and not self.needs_refresh():
            return

        logger.debug("Refreshing model from scene ...")

        event = events.RefreshFromSceneEvent()
        self.refreshFromScene.emit(event)

        rig_models: list[RigModel] = []

        for rig in event.rigs:
            rig_model = RigModel(rig=rig)
            for module in rig.modules():
                module_model = self._modules_manager.create_module_model(
                    rig_model, module
                )
                rig_model.add_module_model(module_model)
            rig_models.append(rig_model)

        self.update_property("rigs", rig_models)

        if not rig_models:
            self.update_property("current_rig", None)
        else:
            if self.current_rig:
                self.update_property("current_rig", self.current_rig)
            else:
                self.update_property("current_rig", rig_models[0])

    def set_editor_mode(self, mode: int):
        """Set the editor mode.

        Args:
            mode: The editor mode to set.
        """

        self.update_property("editor_mode", mode)

        if not self.current_module_exists():
            return

        if mode == 1:
            self.current_module.module.build_guides()

    # region === Rig === #

    def current_rig_exists(self) -> bool:
        """Return whether the current rig exists in the scene."""

        current_rig: RigModel | None = self.current_rig
        return current_rig is not None and current_rig.exists()

    def set_current_rig_by_name(self, rig_name: str):
        """Set the current rig by its name.

        Args:
            rig_name: Name of the rig to set as current.
        """

        found_rig_model: RigModel | None = None
        for rig_model in self.rigs:
            if rig_model.name == rig_name:
                found_rig_model = rig_model
                break
        if found_rig_model is None:
            logger.warning(f"Rig '{rig_name}' not found")
            return

        self.update_property("current_rig", found_rig_model)

    def add_rig(self, set_current: bool = True) -> RigModel | None:
        """Add a new rig to the scene.

        Args:
            set_current: Whether to set the newly created rig as the current
                one.

        Returns:
            The newly created rig model instance, or `None` if the rig could
        """

        event = events.AddRigEvent()
        self.addRig.emit(event)
        if event.rig is None:
            logger.error("No rig was created")
            return None

        rig_model = RigModel(rig=event.rig)

        rig_models = self.rigs
        rig_models.append(rig_model)
        self.update_property("rigs", rig_models)

        if set_current:
            self.update_property("current_rig", rig_model)

        self.rigAdded.emit()

        return rig_model

    # endregion

    # === Module === #

    def current_module_exists(self) -> bool:
        """Return whether the current module exists in the scene."""

        current_module: ModuleModel | None = self.current_module
        return current_module is not None and current_module.exists()

    def open_module(
        self,
        module_id: str,
    ):
        """Add a new module to the current rig.

        Args:
            module_id: ID of the module to add.

        Notes:
            - If no current rig exists, a new one will be created.
        """

        if not self.current_rig_exists():
            self.add_rig(set_current=True)

        rig_model = self.current_rig
        if rig_model is None:
            logger.error("No current rig to add module to")
            return

        module_model_class, module_type = self.modules_models_manager.find_module_model(
            module_id
        )
        if not module_model_class:
            logger.error(f"Module model with id '{module_id}' not found")
            return

        event = events.OpenModuleEvent(
            rig=self.current_rig.rig,
            module_id=module_type,
        )
        self.addModule.emit(event)

        if event.module is None:
            logger.error(f"Failed to create module with id '{module_id}'")
            return

        module_model = self.modules_models_manager.create_module_model(
            rig_model, event.module
        )
        rig_model.add_module_model(module_model)

        self.update_property("current_module", module_model)

    def create_guide_for_current_module(self) -> bool:
        """Creates the guide for the current module.

        Returns:
            Whether the guide was created successfully.
        """

        if not self.current_module_exists():
            logger.error("No current module to create guide for")
            return False

        return self.current_module.create_guide()

    # endregion
