from __future__ import annotations

import os
import typing
from pathlib import Path

from Qt.QtCore import Qt, Signal, QObject, QModelIndex
from Qt.QtWidgets import QWidget
from Qt.QtGui import QColor, QIcon

from tp.libs import qt
from tp.libs.qt.widgets import TreeModel, TreeViewWidget, BaseDataSource, IconMenuButton

from .abstract_editor import EditorPlugin

if typing.TYPE_CHECKING:
    from tp.libs.modrig.maya.api import ModuleUiData, ModulesManager, RegisteredModule


class ModulesLibraryEditor(EditorPlugin):
    id = "modules_library"
    name = "Modules"
    description = "Modules Library Editor"
    version = "0.1.0"

    def get_allowed_areas(self) -> Qt.DockWidgetArea | Qt.DockWidgetAreas:
        """Get the allowed dock areas for this plugin."""

        return Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea

    def get_default_area(self) -> Qt.DockWidgetArea:
        """Get the default dock area for this plugin."""

        return Qt.LeftDockWidgetArea


class ModulesLibraryWidget(TreeViewWidget):
    moduleItemDoubleClicked = Signal(str)

    def __init__(
        self,
        modules_manager: ModulesManager,
        title="Modules",
        expand: bool = True,
        sorting: bool = True,
        parent: QWidget | None = None,
    ):
        super().__init__(title=title, expand=expand, sorting=sorting, parent=parent)

        self.tree_view.setHeaderHidden(True)
        self.tree_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tree_view.setIndentation(qt.dpi_scale(20))

        self._root_source = ModuleFolderDataSource(folder_path="")
        self._modules_tree_model = ModulesTreeModel(
            modules_manager, self._root_source, parent=self
        )
        self.set_model(self._modules_tree_model)

        self.refresh()
        self.expand_all()

    def refresh(self):
        self._root_source.set_user_objects([])
        self.set_sorting_enabled(False)
        try:
            self._modules_tree_model.reload_modules()
            self._modules_tree_model.reload()
        finally:
            self.set_sorting_enabled(True)

        super().refresh()

    def _setup_widgets(self):
        """Set up the widgets for the widget."""

        super()._setup_widgets()

        self._menu_button = IconMenuButton(parent=self)
        self._menu_button.setFixedWidth(qt.dpi_scale(22))
        self._menu_button.setIcon(qt.icon("menu_dots"))
        self._menu_button.addAction(
            name="Expand All", connect=self.expand_all, action_icon=qt.icon("sort_down")
        )
        self._menu_button.addAction(
            name="Collapse All",
            connect=self.collapse_all,
            action_icon=qt.icon("sort_right"),
        )

    def _setup_layouts(self):
        """Set up the layouts for the widget."""

        super()._setup_layouts()

        self.toolbar_layout.setContentsMargins(*qt.margins_dpi_scale(*(10, 6, 2, 0)))
        self.toolbar_layout.addWidget(self._menu_button)

    def _setup_signals(self):
        """Set up the signals for the widget."""

        super()._setup_signals()

        self.tree_view.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _on_item_double_clicked(self, index: QModelIndex) -> None:
        """Handles the event when an item in the tree view is double-clicked.

        Args:
            index: The QModelIndex of the item that was double-clicked.
        """

        item = self._modules_tree_model.item_from_index(index)
        if not isinstance(item, ModuleDataSource):
            return

        self.moduleItemDoubleClicked.emit(item.module_info["module_class"].id)


class ModulesTreeModel(TreeModel):
    def __init__(
        self,
        modules_manager: ModulesManager,
        root: ModuleFolderDataSource,
        parent: QObject | None = None,
    ):
        super().__init__(root=root, parent=parent)

        self._modules_manager = modules_manager

    def reload_modules(self) -> None:
        """Reload the modules from the modules manager and populates the
        tree model with the corresponding data sources.
        """

        folder_items: dict[str, ModuleFolderDataSource] = {}

        for directory in self._modules_manager.manager.paths:
            if not os.path.isdir(directory):
                continue
            for root, dirs, files in os.walk(directory):
                if "__pycache" in root:
                    continue

                parent_item = folder_items.get(os.path.basename(root), self.root())
                for direct in dirs:
                    if "__pycache" in direct:
                        continue
                    if os.path.basename(direct) in folder_items:
                        continue

                    full_path = (Path(root) / direct).as_posix()
                    source = ModuleFolderDataSource(
                        folder_path=full_path, model=self, parent=parent_item
                    )
                    folder_items[os.path.basename(full_path)] = source
                    parent_item.add_child(source)

                for f in files:
                    if not f.endswith(".py") or f == "__init__.py":
                        continue

                    full_path = (Path(root) / f).as_posix()
                    module_name, module_info = (
                        self._modules_manager.module_data_by_path(full_path)
                    )
                    if not module_info:
                        continue
                    ui_data: ModuleUiData = module_info["module_class"].ui_data
                    if not ui_data.display_name:
                        ui_data.display_name = module_name.replace("module", "")
                    source = ModuleDataSource(
                        name=module_name,
                        module_info=module_info,
                        ui_data=ui_data,
                        model=self,
                        parent=parent_item,
                    )
                    parent_item.add_child(source)


class ModuleFolderDataSource(BaseDataSource):
    _ICON: QIcon | None = None

    def __init__(
        self,
        folder_path: str,
        header_text: str | None = None,
        model: ModulesTreeModel | None = None,
        parent: BaseDataSource | None = None,
    ):
        super().__init__(header_text=header_text, model=model, parent=parent)

        self._folder_path = folder_path
        self._name = os.path.basename(folder_path)

        if ModuleFolderDataSource._ICON is None:
            ModuleFolderDataSource._ICON = qt.colorize_icon(
                qt.icon("folder"),
                size=qt.dpi_scale(16),
                color=QColor(236, 236, 236),
            )

    def data(self, index: int) -> str:
        """Retrieve data associated with the provided index.

        Args:
            index: An integer representing the position of the desired data
            element in the collection.

        Returns:
            The data associated with the specified index.
        """

        return self._name

    def icon(self, index: int) -> QIcon | None:
        """Retrieve the icon associated with the given index in a data
        structure.

        Args:
            index: The index for which the corresponding icon is to be
                retrieved.

        Returns:
            QIcon | None: The icon associated with the given index; `None` if
                no icon is found.
        """

        return ModuleFolderDataSource._ICON

    def is_editable(self, index: int) -> bool:
        """Determine whether the specified index is editable.

        Args:
            index: An integer representing the index to check.

        Returns:
            `True` if the index is editable; `False` otherwise.
        """

        return False

    # noinspection PyMethodMayBeStatic
    def is_folder(self) -> bool:
        """Determine whether this data source represents a folder.

        Returns:
            `True` if this data source is a folder; `False` otherwise.
        """

        return False


class ModuleDataSource(BaseDataSource):
    def __init__(
        self,
        name: str,
        module_info: RegisteredModule,
        ui_data: ModuleUiData,
        header_text: str | None = None,
        model: ModulesTreeModel | None = None,
        parent: BaseDataSource | None = None,
    ):
        super().__init__(header_text=header_text, model=model, parent=parent)

        self._name = name
        self._module_info = module_info
        self._ui_data = ui_data
        self._label = ui_data.display_name
        if self._module_info["module_class"].beta_version:
            self._label += " (Beta)"
        self._icon = qt.colorize_layered_icon(
            icons=[qt.icon("rounded_square_filled"), qt.icon(self._ui_data.icon)],
            size=qt.dpi_scale(16),
            colors=[QColor(self._ui_data.icon_color)],
            scaling=[1, 0.8],
        )

    @property
    def module_info(self) -> RegisteredModule:
        """The registered module information dictionary."""

        return self._module_info

    def data(self, index: int) -> str:
        """Retrieve data associated with the provided index.

        Args:
            index: An integer representing the position of the desired data
            element in the collection.

        Returns:
            The data associated with the specified index.
        """

        return self._label

    def icon(self, index: int) -> QIcon | None:
        """Retrieve the icon associated with the given index in a data
        structure.

        Args:
            index: The index for which the corresponding icon is to be
                retrieved.

        Returns:
            QIcon | None: The icon associated with the given index; `None` if
                no icon is found.
        """

        return self._icon

    def is_editable(self, index: int) -> bool:
        """Determine whether the specified index is editable.

        Args:
            index: An integer representing the index to check.

        Returns:
            `True` if the index is editable; `False` otherwise.
        """

        return False

    # noinspection PyMethodMayBeStatic
    def is_folder(self) -> bool:
        """Determine whether this data source represents a folder.

        Returns:
            `True` if this data source is a folder; `False` otherwise.
        """

        return False
