from __future__ import annotations

import typing
from typing import Any, Union

from overrides import override

from tp.core import log
from tp.common.qt import api as qt
from tp.common.resources import api as resources

from tp.tools.rig.frag import commands
from tp.libs.rig.frag.core import action, builder, blueprint as bp

if typing.TYPE_CHECKING:
    from tp.libs.rig.frag.core.builder import BlueprintBuilder

logger = log.rigLogger


def all_rigs():
    return []


class BlueprintModel(qt.QObject):
    """
    Class that owns and managers multiple models that represents a Blueprint in the scene.
    All reading/writing operations to a model using UI should be done using this model.
    """

    _INSTANCE: BlueprintModel | None = None

    # Signal that is called when the current blueprint file has changed.
    fileChanged = qt.Signal()

    # Signal that is called when the modified status of the currently opened blueprint file has changed.
    isFileModifiedChanged = qt.Signal(bool)

    # Signal called when the read-only state of the blueprint has changed.
    readOnlyChanged = qt.Signal(bool)

    # Signal called when a blueprint setting has changed
    settingChanged = qt.Signal(str, object)

    # Signal that is called when the presence of a built rig has changed.
    rigExistsChanged = qt.Signal()

    # Signal that is called when validation results have changed.
    validated = qt.Signal()

    def __init__(self, parent: qt.QObject | None = None):
        super().__init__(parent=parent)

        action.BuildActionPackageRegistry().load_actions()

        # Null blueprint used when no blueprint file is opened to allow UIs to still work.
        self._empty_blueprint = bp.Blueprint()

        self._blueprint_file: bp.BlueprintFile | None = None
        self._build_step_tree_model = BuildStepTreeModel(self, parent=self)
        # self._build_step_selection_model = BuildStepSelectionModel(self._build_step_tree_model, parent=self)
        self._does_rig_exist = False
        self._interactive_builder: BlueprintBuilder | None = None
        self._is_changing_scenes = False

    @classmethod
    def get(cls) -> BlueprintModel:
        """
        Returns shared model instance.

        :return: shared model instance.
        :rtype: BlueprintModel
        """

        if cls._INSTANCE is None:
            cls._INSTANCE = BlueprintModel()

        return cls._INSTANCE

    @classmethod
    def delete(cls):
        """
        Deletes shared model instance.
        """

        if cls._INSTANCE is None:
            return

        cls._INSTANCE.cleanup()
        cls._INSTANCE = None

    @property
    def blueprint(self) -> bp.Blueprint:
        """
        Getter method that returns the blueprint of the currently opened blueprint file.

        :return: blueprint instance.
        :rtype: bp.Blueprint
        """

        return self._empty_blueprint if not self._blueprint_file else self._blueprint_file.blueprint

    @property
    def blueprint_file(self) -> bp.BlueprintFile | None:
        """
        Getter method that returns the blueprint being edited.

        :return: blueprint file or None if no Blueprint is currently being edited.
        :rtype: bp.BlueprintFile or None
        """

        return self._blueprint_file

    @property
    def build_step_tree_model(self) -> BuildStepTreeModel:
        """
        Returns model instance used to display build steps in a tree view.

        :return: build step tree model.
        :rtype: BuildStepTreeModel
        """

        return self._build_step_tree_model

    @property
    def does_rig_exist(self) -> bool:
        """
        Getter method that returns whether rig exists within scene. Used to determine which mode we are in.

        :return: True if rig exists within scene; False otherwise.
        :rtype: bool
        """

        return self._does_rig_exist

    @property
    def interactive_builder(self) -> BlueprintBuilder | None:
        """
        Getter method that returns the interactive builder that is currently running.

        :return: interactive builder instance. If no interactive builder is running will return None.
        :rtype: BlueprintBuilder or None
        """

        return self._interactive_builder

    @property
    def is_changing_scenes(self) -> bool:
        """
        Returns whether a scene is being changed.

        :return: True if scene is being changed; False otherwise.
        :rtype: bool
        """

        return self._is_changing_scenes

    def blueprint_file_path(self) -> str | None:
        """
        Returns the full path of the current blueprint file.

        :return: absolute blueprint file path.
        :rtype: str or None
        """

        return self._blueprint_file.file_path if self.is_file_open() else None

    def blueprint_file_name(self) -> str | None:
        """
          Returns the base name of the current blueprint file.

          :return: blueprint base name.
          :rtype: str or None
          """

        return self._blueprint_file.file_name() if self.is_file_open() else None

    def is_file_open(self) -> bool:
        """
        Returns whether blueprint file is currently available.

        :return: True if blueprint file is opened; False otherwise.
        :rtype: bool
        """

        return self._blueprint_file is not None

    def is_file_modified(self) -> bool:
        """
        Returns whether modifications have been made to currently opened blueprint file since it was last saved.

        :return: True if opened blueprint file has been modified; False otherwise.
        :rtype: bool
        """

        return self.is_file_open() and self._blueprint_file.is_modified()

    def modify(self):
        """
        Marks current opened blueprint file as modified.
        """

        if not self.is_file_open() or self.is_read_only():
            return

        self._blueprint_file.modify()
        self.isFileModifiedChanged.emit(self.is_file_modified())

    def is_read_only(self) -> bool:
        """
        Returns whether modifications to blueprint are not allowed.

        :return: True if blueprint cannot be modified; False otherwise.
        :rtype: bool
        """

        if self._does_rig_exist or not self.is_file_open():
            return True

        return self._blueprint_file.is_read_only

    def can_save(self) -> bool:
        """
        Returns whether blueprint file can be saved.

        :return: True if blueprint file can be saved; False otherwise.
        :rtype: bool
        """

        self._refresh_rig_exists()
        return self.is_file_open() and self._blueprint_file.can_save() and not self._does_rig_exist

    def can_load(self) -> bool:
        """
        Returns whether blueprint file can be loaded.

        :return: True if blueprint file can be loaded; False otherwise.
        :rtype: bool
        """

        return self.is_file_open() and self._blueprint_file.can_load()

    def new_file(self):
        """
        Starts a new blueprint file without writing it to disk.
        """

        if self.is_file_open() and not self.close_file():
            return

        self._build_step_tree_model.beginResetModel()
        try:
            self._blueprint_file = bp.BlueprintFile()
            self._blueprint_file.resolve_file_path(allow_existing=True)
            self._blueprint_file.blueprint.set_setting(bp.BlueprintSettings.RigName, 'untitled')
            self._blueprint_file.blueprint.reset_to_default()
        finally:
            self._build_step_tree_model.endResetModel()

        self.fileChanged.emit()
        self.readOnlyChanged.emit(self.is_read_only())

    def save_file(self) -> bool:
        """
        Saves current blueprint file.

        :return: True if the file was saved successfully; False otherwise.
        :rtype: bool
        """

        if not self.can_save():
            return False

        success = self._blueprint_file.save()
        self.isFileModifiedChanged.emit(self.is_file_modified())

        return success

    def save_file_as(self, file_path: str) -> bool:
        """
        Saves the current blueprint file to a different file path.

        :param str file_path: new blueprint file path.
        :return: True if the file was saved successfully; False otherwise.
        :rtype: bool
        """

        if not self.is_file_open():
            return False

        self._blueprint_file.file_path = file_path
        self.fileChanged.emit()
        success = self._blueprint_file.save()
        self.isFileModifiedChanged.emit(self.is_file_modified())

        return success

    def save_file_with_prompt(self) -> bool:
        """
        Saves the current blueprint file, prompting for a file path if None is set.

        :return: True if the file was saved successfully; False otherwise.
        :rtype: bool
        """

        return self._save_file_path_with_prompt()

    def save_file_as_with_prompt(self) -> bool:
        """
        Saves the current blueprint file to a new path, prompting the user for the file path.

        :return: True if the file was saved successfully; False otherwise.
        :rtype: bool
        """

        return self._save_file_path_with_prompt(force_prompt=True)

    def save_or_discard_changes_with_prompt(self) -> bool:
        """
        Saves or discards modifications to the current blueprint file.

        :return: True if the user choose to Save or Not Save; False if the user choose to Cancel the operation.
        :rtype: bool
        """

        file_path = self.blueprint_file_path()
        if file_path:
            message = f'Save changes to {file_path}'
        else:
            message = 'Save changes to unsaved blueprint?'
        response = qt.QMessageBox.question(
            None, 'Save Blueprint Changes', message, qt.QMessageBox.Save | qt.QMessageBox.No, qt.QMessageBox.Cancel)
        if response == qt.QMessageBox.Save:
            return self.save_file_with_prompt()
        elif response == qt.QMessageBox.No:
            return True

        return False

    def close_file(self, prompt_save_changes: bool = True) -> bool:
        """
        Closes the current blueprint file.

        :param bool prompt_save_changes: whether to show prompt if there are unsaved changes.
        :return: True if the file was successfully closed; False otherwise.
        :rtype: bool
        """

        if prompt_save_changes and self.is_file_modified():
            if not self.save_or_discard_changes_with_prompt():
                return False

        self._build_step_tree_model.beginResetModel()
        try:
            self._blueprint_file = None
            self._build_step_tree_model.set_blueprint(self.blueprint)
        finally:
            self._build_step_tree_model.endResetModel()

        self.fileChanged.emit()
        self.readOnlyChanged.emit(self.is_read_only())

        return True

    def step(self, step_path: str) -> action.BuildStep | None:
        """
        Returns the build step at given path.

        :param str step_path: full build step to get build step instance for.
        :return: build step.
        :rtype: action.BuildStep or None
        """

        return self.blueprint.step_by_path(step_path)

    def rename_step(self, step_path: str, target_name: str) -> str | None:
        """
        Renames step at given path with the new target name.

        :param str step_path: build step full path to rename.
        :param str target_name: new build step name.
        :return: new build step path after renaming it.
        :rtype: str
        """

        if self.is_read_only():
            logger.error('Cannot rename build step because blueprint is in read only mode')
            return None

        step = self.blueprint.step_by_path(step_path)
        if step is None:
            logger.error(f'Cannot rename build step because was not possible to find build step: {step_path}')
            return None

        if step.is_root():
            logger.error('Cannot rename build step because root step cannot be renamed')
            return None

        old_name = step.name
        step.set_name(target_name)

        if step.name != old_name:
            self._emit_step_changed(step)

        return step.full_path()

    def is_interactive_building(self) -> bool:
        """
        Returns whether an interactive build is currently active.

        :return: True if an interactive build is active; False otherwise.
        :rtype: bool
        """

        return self._interactive_builder is not None

    def run_validation(self):
        """
        Runs a Blueprint validator for the current blueprint.
        """

        if not self.is_file_open():
            return

        if not builder.BlueprintBuilder.pre_build_validate(self._blueprint_file):
            return

        validator = builder.BlueprintValidator(self.blueprint_file)
        validator.start()

        self.validated.emit()

    def setting(self, key: str, default: Any = None) -> Any:
        """
        Returns blueprint setting with given key.

        :param str key: setting key.
        :param Any default: default value that should be returned if not setting with given key was found.
        :return: setting value.
        :rtype: Any
        """

        return self.blueprint.setting(key, default=default)

    def set_setting(self, key: str, value: Any):
        """
        Sets a blueprint setting with given key and value.

        :param str key: key of setting to set.
        :param Any value: value of the setting to set.
        """

        if self.is_read_only():
            logger.error('Cannot set blueprint setting because blueprint is in read only mode.')
            return

        old_value = self.blueprint.setting(key)
        if old_value != value:
            self.blueprint.set_setting(key, value)
            self.modify()
            self.settingChanged.emit(key, value)

    def cleanup(self):
        """
        Cleanup blueprint model.
        """

        pass

    def _refresh_rig_exists(self):
        """
        Internal function that refreshes the internal values that indicates whether a built rig exists within scene.
        """

        old_read_only = self.is_read_only()
        self._does_rig_exist = bool(len(all_rigs()))
        self.rigExistsChanged.emit()
        if old_read_only != self.is_read_only():
            self.readOnlyChanged.emit(self.is_read_only())

    def _save_file_with_prompt(self, force_prompt: bool = False) -> bool:
        """
        Internal function that saves blueprint file into disk allowing the user to select where to save it.

        :param bool force_prompt: whether to prompt the user even if the blueprint file is already saved in disk.
        :return: True if file was saved successfully; False otherwise.
        :rtype: bool
        """

        if not self.is_file_open():
            logger.error('Nothing to save.')
            return False

        if self.is_read_only():
            logger.error('Blueprint file cannot be saved because blueprint is in read only mode.')
            return False

        if force_prompt or not self._blueprint_file.has_file_path():
            file_path, _ = qt.QFileDialog.getSaveFileName(None, 'Save Blueprint', filter='Noddle Blueprint (*.yaml)')
            if not file_path:
                return False
            self._blueprint_file.file_path = file_path
            self.fileChanged.emit()

        self.save_file()

        return True

    def _emit_step_changed(self, step: action.BuildStep):
        """
        Internal function that emits signal that indicates that given build step has been modified by the model somehow.

        :param action.BuildStep step: modified build step.
        """

        index = self._build_step_tree_model.index_by_step(step)
        self._build_step_tree_model.dataChanged.emit(index, index, [])
        self.modify()


class BuildStepTreeModel(qt.QAbstractItemModel):
    """
    Custom Qt tree model for viewing and modifying the BuildStep hierarchy of a blueprint.
    """

    def __init__(self, blueprint_model: BlueprintModel | None = None, parent: qt.QObject | None = None):
        super().__init__(parent=parent)

        self._blueprint_model = blueprint_model

    @property
    def blueprint(self) -> bp.Blueprint | None:
        """
        Getter method that returns the blueprint associated to this model.

        :return: blueprint instance.
        :rtype: blueprint.Blueprint
        """

        return self._blueprint_model.blueprint

    @blueprint.setter
    def blueprint(self, value: bp.Blueprint | None):
        """
        Setter method that sets the blueprint associated to this model.

        :param bp.Blueprint value: blueprint instance.
        """

        self._blueprint_model.blueprint = value

    @override
    def columnCount(self, parent: qt.QModelIndex = ...) -> int:
        return 1

    @override
    def rowCount(self, parent: qt.QModelIndex = ...) -> int:
        if not parent.isValid():
            return 1

        step = self.step_for_index(parent)
        return step.num_children() if step else 0

    @override
    def flags(self, index: qt.QModelIndex) -> Union[qt.Qt.ItemFlags, qt.Qt.ItemFlag]:
        if not index.isValid():
            return qt.Qt.NoItemFlags

        flags = qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable
        if self.is_read_only():
            return flags

        step = self.step_for_index(index)
        if not step:
            return flags

        if not step.is_root():
            flags |= qt.Qt.ItemIsDragEnabled | qt.Qt.ItemIsEditable
        if step.can_have_children():
            flags |= qt.Qt.ItemIsDropEnabled

        return flags

    @override
    def index(self, row: int, column: int, parent: qt.QModelIndex = ...) -> qt.QModelIndex:
        if column != 0:
            return qt.QModelIndex()

        if parent.isValid():
            parent_step = self.step_for_index(parent)
            if parent_step is not None and parent_step.can_have_children():
                child_step = parent_step.child_at(row)
                if child_step:
                    return self.createIndex(row, column, child_step)
        elif row == 0:
            return self.createIndex(row, column, self.blueprint.root_step)

        return qt.QModelIndex()

    @override(check_signature=False)
    def parent(self, child: qt.QModelIndex) -> qt.QModelIndex:
        if not child.isValid():
            return qt.QModelIndex()

        child_step = self.step_for_index(child)
        if child_step is None:
            return qt.QModelIndex()

        parent_step = child_step.parent

        return self.index_by_step(parent_step) if parent_step is not None else qt.QModelIndex()

    def data(self, index: qt.QModelIndex, role: qt.Qt.ItemDataRole = ...) -> Any:
        if not index.isValid():
            return

        step = self.step_for_index(index)
        if step is None:
            return

        if role == qt.Qt.DisplayRole:
            return step.display_name()
        elif role == qt.Qt.FontRole:
            font = qt.QFont()
            font.setItalic(self.is_read_only())
            return font
        elif role == qt.Qt.EditRole:
            return step.name
        elif role == qt.Qt.DecorationRole:
            is_disabled = step.is_disabled_in_hierarchy()
            if not step.is_action():
                icon_name = 'step_group'
                if is_disabled:
                    icon_name = 'step_group_disabled'
                elif step.has_warnings():
                    icon_name = 'warning'
            else:
                is_mirrored = step.action_proxy.is_mirrored
                if is_disabled:
                    icon_name = 'step_action_sym_disabled' if is_mirrored else 'step_action_disabled'
                elif step.has_warnings():
                    icon_name = 'warning'
                else:
                    icon_name = 'step_action_sym' if is_mirrored else 'step_action'
            result = resources.icon(icon_name, extension='svg')
            return result
        elif role == qt.Qt.SizeHintRole:
            return qt.QSize(0, 20)
        elif role == qt.Qt.ForegroundRole:
            color = step.color()
            if step.is_disabled_in_hierarchy():
                color *= 0.4
            color.a = 1.0
            return qt.QColor(*color.as_8bit())
        elif role == qt.Qt.BackgroundRole:
            # Highlight active step during interactive build
            if self._blueprint_model.is_interactive_building():
                if self._blueprint_model.interactive_builder.current_build_step_path == step.full_path():
                    return qt.QColor(60, 120, 94, 128)
            # Highlight steps with warnings
            if step.is_action() and step.has_warnings():
                return qt.QColor(255, 255, 110, 25)

    def setData(self, index: qt.QModelIndex, value: Any, role: qt.Qt.ItemDataRole = ...) -> bool:
        if not index.isValid() or self.is_read_only():
            return False

        step = self.step_for_index(index)
        if step is None:
            return False

        if role == qt.Qt.EditRole:
            value = value or ''
            step_path = step.full_path()
            commands.rename_step(step_path, value)
            return True
        elif role == qt.Qt.CheckStateRole:
            if step.is_root():
                return False
            step.is_disabled = True if value else False
            self.dataChanged.emit(index, index, [])
            self._emit_data_changed_on_all_children(index, [])
            return True

        return False

    def is_read_only(self) -> bool:
        """
        Returns whether model can be modified.

        :return: True if model only can be read and not modified; False otherwise.
        :rtype: bool
        """

        return self._blueprint_model.is_read_only() if self._blueprint_model else False

    def step_for_index(self, index: qt.QModelIndex) -> action.BuildStep | None:
        """
        Internal function that returns the build step instance that is pointing given model index.

        :param qt.QModelIndex index: model index.
        :return: build step instance.
        :rtype: action.BuildStep or None
        """

        return index.internalPointer() if index.isValid() else None

    def index_by_step(self, build_step: action.BuildStep) -> qt.QModelIndex:
        """
        Internal function that returns the model index that points to the given build step within the model.

        :param action.BuildStep build_step: build step to get model index for.
        :return: model index pointing to given build step.

        ..note:: this function returns a QModelIndex even if build step is not found within model. In this case,
            `QModelIndex.isValid()` will return False.
        """

        if build_step is None:
            return qt.QModelIndex()

        index_in_parent = build_step.index_in_parent()
        return self.createIndex(index_in_parent, 0, build_step) if index_in_parent >= 0 else qt.QModelIndex()

    def _emit_data_changed_on_all_children(
            self, parent: qt.QModelIndex = qt.QModelIndex(), roles: list[qt.Qt.ItemDataRole] | None = None):
        """
        Internal recursive function that emits dataChanged signal for all children indexes.

        :param qt.QModelIndex parent: parent index whose children indexes we want dataChanged signal to be emitted for.
        :param list[qt.Qt.ItemDataRole] | None or None roles: optional list of item data roles to be notified for.
        """

        if not parent.isValid():
            return
        row_count = self.rowCount(parent)
        if row_count == 0:
            return

        first_child = self.index(0, 0, parent)
        last_child = self.index(row_count - 1, 0, parent)

        # Emit one event for all child indexes of parent.
        self.dataChanged.emit(first_child, last_child, roles)

        # Recursively emit on all children
        for i in range(row_count):
            child_index = self.index(i, 0, parent)
            self._emit_data_changed_on_all_children(child_index, roles)


class BuildStepSelectionModel(qt.QItemSelectionModel):
    pass
