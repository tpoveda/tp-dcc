from __future__ import annotations

import typing
from collections.abc import Generator, Iterator
from typing import Any, cast

from Qt.QtCore import (
    QItemSelectionModel,
    QModelIndex,
    QObject,
    QPoint,
    Qt,
    Signal,
)
from Qt.QtGui import QIcon
from Qt.QtWidgets import QAbstractItemView, QWidget

from tp.preferences.directory import DirectoryPath

from ... import contexts, dpi, icons, utils
from ..layouts import VerticalLayout
from ..viewmodel import roles
from ..viewmodel.data import BaseDataSource
from ..viewmodel.treemodel import TreeModel
from ..viewmodel.treeview import (
    TreeViewWidget,
    TreeViewWidgetSelectionChangedEvent,
)
from ..window import Window

if typing.TYPE_CHECKING:
    from tp.preferences.assets import BrowserPreference


class CategoryFolder(BaseDataSource):
    def __init__(
        self,
        directory_info: dict[str, Any],
        model: FolderTreeModel | None = None,
        parent: BaseDataSource | None = None,
    ):
        super().__init__(header_text=None, model=model, parent=parent)

        self._data = directory_info
        self._icon: QIcon | None = None

    # region === Data === #

    @property
    def internal_data(self) -> dict[str, Any]:
        """The internal data of the folder."""

        return self._data

    def folder_id(self) -> str:
        """The unique identifier of the folder."""

        return self._data.get("id", "")

    def alias(self) -> str:
        """The alias of the folder."""

        return self._data.get("alias", "")

    # endregion

    # region === BaseDataSource Overrides === #

    def column_count(self) -> int:
        """Returns the number of columns for the item.

        Returns:
            The number of columns for the item.
        """

        return 1

    def icon(self, index: int) -> QIcon | None:
        """The icon of the folder item."""

        return self._icon

    def supports_drag(self, index: int) -> bool:
        """Determine whether an item at the specified index supports
        drag-and-drop functionality.

        Args:
            index: The index of the item to check if drag-and-drop
                functionality is supported.

        Returns:
            `True` if the item at the specified index supports drag-and-drop;
            `False` otherwise.
        """

        return True

    def supports_drop(self, index: int) -> bool:
        """Determine whether an item at the specified index supports
        drag-and-drop functionality.

        Args:
            index: The index of the item to check if drag-and-drop
                functionality is supported.

        Returns:
            `True` if the item at the specified index supports drag-and-drop;
            `False` otherwise.
        """

        return True

    def mime_data(self, index: int) -> dict[str, Any]:
        """Returns the mime data for the item at the specified index.

        Args:
            index: The index of the item to get the mime data for.

        Returns:
            A dictionary containing the mime data for the item.
        """

        data = self._data.copy()
        data["children"] = []
        for child in self.children:
            data["children"].append(child.mime_data(0))

        return data

    def drop_mime_data(
        self, items: list[str], action: Qt.DropAction
    ) -> dict[str, Any]:
        """Handles the drop of mime data onto the item.

        Args:
            items: A list of items being dropped.
            action: The drop action being performed.

        Returns:
            A dictionary containing information about the drop operation.
        """

        return {"items": items}

    def custom_roles(self, index: int) -> list[int]:
        """Returns a list of custom roles for the item at the specified index.

        Args:
            index: The index of the item to get the custom roles for.

        Returns:
            A list of custom roles for the item.
        """

        return [roles.UID_ROLE + 1]

    def data_by_role(self, index: int, role: Qt.ItemDataRole) -> Any:
        """Returns the data for the item at the specified index and role.

        Args:
            index: The index of the item to get the data for.
            role: The role to get the data for.

        Returns:
            The data for the item at the specified index and role.
        """

        if role == roles.UID_ROLE + 1:
            return self.folder_id()

        return super().data_by_role(index, role)

    def data(self, index: int) -> str:
        """Returns the data for the item at the specified index.

        Args:
            index: The index of the item to get the data for.

        Returns:
            The data for the item at the specified index.
        """

        if self.is_root():
            return "root"

        return self.alias()

    def set_data(self, index: int, value: Any) -> bool:
        """Sets the data for the item at the specified index.

        Args:
            index: The index of the item to set the data for.
            value: The value to set the data to.
        """

        if not value or value == self.alias():
            return False

        self._data.alias = value

        return True

    # noinspection PyMethodOverriding
    def insert_row_data_source(
        self, index: int, data: dict[str, Any], item_type: str
    ) -> CategoryFolder | None:
        """Inserts a new child data source at the specified index.

        Args:
            index: The index to insert the new data source at.
            data: A dictionary containing the data for the new data source.
            item_type: The type of the new data source. Can be either "path"

        Returns:
            The newly created child data source.
        """

        model = cast(FolderTreeModel, self.model)

        if item_type == "category":
            new_item = model.preferences.create_category(
                name=data["alias"],
                category_id=None,
                parent=self.folder_id(),
                children=data.get("children", []),
            )
            new_item = CategoryFolder(new_item, model=self.model, parent=self)
            self.insert_child(index, new_item)
        else:
            directory_path = DirectoryPath(
                data["path"], alias=data.get("alias")
            )
            new_item = FolderItem(
                directory_path.to_dict(), model=self.model, parent=self
            )
            self.insert_child(index, new_item)

    # noinspection PyMethodOverriding
    def insert_row_data_sources(
        self, index: int, count: int, items: list[dict[str, Any]]
    ) -> bool:
        """Inserts new child data sources at the specified index.

        Args:
            index: The index to insert the new data sources at.
            count: The number of data sources to insert.
            items: A list of dictionaries containing the data for the new
                data sources.

        Returns:
            `True` if the data sources were inserted successfully; `False` otherwise.
        """

        for item in items:
            data: dict[str, Any] = {}
            if item.get("path"):
                item_type = "path"
                data["path"] = item["path"]
                data["alias"] = item["alias"]
            else:
                item_type = "category"
                data["alias"] = item["alias"]

            child_item = self.insert_row_data_source(index, data, item_type)
            children = item.get("children", [])
            if children:
                child_item.insert_row_data_sources(
                    0, len(children), items=children
                )

        model = cast(FolderTreeModel, self.model)
        model.preferences.save_settings()

        return True

    # endregion


class FolderItem(CategoryFolder):
    """A filesystem folder within the tree."""

    def __init__(
        self,
        directory_info: dict[str, Any],
        model: FolderTreeModel | None = None,
        parent: BaseDataSource | None = None,
    ):
        super().__init__(
            directory_info=directory_info, model=model, parent=parent
        )

        self._icon = icons.icon("folder")

    # region === BaseDataSource Overrides === #

    def tooltip(self, index: int) -> str:
        """The tooltip of the folder item."""

        return self._data.get("path", "")

    def supports_drop(self, index: int) -> bool:
        """Determine whether an item at the specified index supports
        drag-and-drop functionality.

        Args:
            index: The index of the item to check if drag-and-drop
                functionality is supported.

        Returns:
            `True` if the item at the specified index supports drag-and-drop;
            `False` otherwise.
        """

        return False

    def data(self, index: int) -> str:
        """Returns the data for the item at the specified index.

        Args:
            index: The index of the item to get the data for.

        Returns:
            The data for the item at the specified index.
        """

        return self.alias()

    # endregion


class FolderTreeModel(TreeModel):
    def __init__(
        self,
        preferences: BrowserPreference,
        root: BaseDataSource | None,
        parent: QObject | None = None,
    ):
        super().__init__(root=root, parent=parent)

        self._preferences = preferences

    @property
    def preferences(self) -> BrowserPreference:
        """The browser preferences instance."""

        return self._preferences

    @preferences.setter
    def preferences(self, prefs: BrowserPreference) -> None:
        """Sets the browser preferences instance."""

        self._preferences = prefs

    def reload(self):
        categories = self._preferences.categories()
        directories = self._preferences.browser_folder_paths()

        root_category = CategoryFolder(directory_info={}, model=self)
        tree: dict[str, CategoryFolder | FolderItem] = {
            d.id: FolderItem(d.to_dict(), model=self) for d in directories
        }

        for category in categories:
            tree[category["id"]] = CategoryFolder(category, model=self)

        for category in categories:
            category_item = tree[category["id"]]
            parent = tree.get(category["parent"])
            children = category.get("children", [])
            if parent is not None:
                category_item.set_parent_source(parent)
            for child in children:
                existing_child = tree.get(child)
                if existing_child is None:
                    continue
                existing_child.set_parent_source(category_item)

        for item in tree.values():
            if item.parent_source() is None:
                item.set_parent_source(root_category)

        self.set_root(root_category, refresh=False)

        super().reload()


class DirectoryPopup(Window):
    selectionChanged = Signal(object)

    def __init__(
        self,
        auto_hide: bool = False,
        attach_to_parent: bool = True,
        preferences: BrowserPreference | None = None,
        parent: QWidget | None = None,
    ):
        self._auto_hide = auto_hide
        self._attach_to_parent = attach_to_parent
        self._preferences = preferences

        self._attached: bool = True
        self._anchor_widget: QWidget | None = None

        super().__init__(parent=parent)

    # region === Setup === #

    @property
    def preferences(self) -> BrowserPreference | None:
        """The browser preferences instance."""

        return self._preferences

    @preferences.setter
    def preferences(self, prefs: BrowserPreference) -> None:
        """Sets the browser preferences instance."""

        self._preferences = prefs
        self._tree_model.preferences = prefs

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        """Setup widgets for the directory popup."""

        self._tree_model = FolderTreeModel(
            preferences=self._preferences, root=None, parent=self
        )
        self._tree_view_widget = TreeViewWidget(parent=self)
        self._tree_view_widget.set_searchable(False)
        self._tree_view_widget.set_show_title_label(False)
        self._tree_view_widget.set_header_hidden(True)
        self._tree_view_widget.set_indentation(dpi.dpi_scale(10))
        self._tree_view_widget.set_drag_drop_mode(
            QAbstractItemView.InternalMove
        )
        self._tree_view_widget.tree_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._tree_view_widget.set_model(self._tree_model)

    def setup_layouts(self, main_layout: VerticalLayout):
        """Setup layouts for the directory popup."""

        main_layout.addWidget(self._tree_view_widget)

    def setup_signals(self) -> None:
        """Setup signals for the directory popup."""

        self._tree_view_widget.selectionChanged.connect(
            self._on_tree_view_selection_changed
        )

    # endregion

    # region === Visibility === #

    def show(self, reattach: bool = True) -> None:
        """Overrides `show` method of `Window` class to move the
        popup to be anchored to the specified widget when the popup is shown.

        Args:
            reattach: Whether to reattach the popup to the parent window.
        """

        if reattach:
            self._attached = True

        new_position = self._move_to_anchor()

        super().show(move=new_position)

    def _move_to_anchor(
        self,
        window_pos: QPoint | None = None,
        offset: tuple[int, int] = (0, 0),
    ) -> QPoint | None:
        """Moves the popup to be anchored to the specified widget.

        Args:
            window_pos: The global position of the parent window.
            offset: Tuple of (x, y) offsets to apply to the position.

        Returns:
            The new position of the popup.
        """

        if self._anchor_widget is None:
            return None

        window_pos = window_pos or self._anchor_widget.mapToGlobal(
            QPoint(0, 0)
        )
        pos = QPoint(
            self._anchor_widget.mapToGlobal(
                QPoint(0, dpi.dpi_scale(offset[1]))
            )
        )
        pos.setX(window_pos.x() - self.width())
        new_pos = utils.contain_widget_in_screen(self, pos)
        self.move(new_pos)

        return new_pos

    # endregion

    # region === Anchoring === #

    def set_anchor_widget(self, widget: QWidget) -> None:
        """Sets the anchor widget for the popup.

        Args:
            widget: The widget to anchor the popup to.
        """

        self._anchor_widget = widget

    # endregion

    # region === Items === #

    def set_active_items(
        self, directories: list[DirectoryPath], categories: list[str]
    ) -> None:
        """Sets the active items in the tree view.

        Args:
            directories: List of directory paths to set as active.
            categories: List of category IDs to set as active.
        """

        def _iterate_proxy_parent_index(
            _model_index: QModelIndex,
        ) -> Generator[QModelIndex, None, None]:
            """Recursively yields parent indexes of the given model index.

            Args:
                _model_index: The model index to start from.

            Yields:
                The parent model indexes up to the root.
            """

            if not _model_index.isValid():
                return
            _parent_index = _model_index.parent()
            yield _parent_index
            for i in _iterate_proxy_parent_index(_parent_index):
                if i is None:
                    return
                yield i

        model = self._tree_view_widget.model

        with contexts.block_signals(self._tree_view_widget):
            proxy_model = self._tree_view_widget.proxy_model

            # Clear current selection.
            selection_model = self._tree_view_widget.selection_model()
            selection_model.clear()

            # Find and select the items.
            selected_indexes: list[QModelIndex] = []
            for item in categories:
                matched_items = cast(
                    list[QModelIndex],
                    proxy_model.match(
                        model.index(0, 0),
                        roles.UID_ROLE + 1,
                        item,
                        hits=1,
                        flags=Qt.MatchRecursive,
                    ),
                )
                selected_indexes.extend(matched_items)
            for item in directories:
                matched_items = cast(
                    list[QModelIndex],
                    proxy_model.match(
                        model.index(0, 0),
                        roles.UID_ROLE + 1,
                        item.id,
                        hits=1,
                        flags=Qt.MatchRecursive,
                    ),
                )
                selected_indexes.extend(matched_items)

            # Select only the top-level items to avoid selecting both parent
            # and child.
            for selected in selected_indexes:
                for parent in _iterate_proxy_parent_index(selected):
                    if parent in selected_indexes:
                        break
                else:
                    selection_model.select(
                        selected, QItemSelectionModel.Select
                    )

    def reset(self) -> None:
        """Resets the directory popup, reloading the tree model and expanding
        all items.
        """

        self._tree_model.reload()
        self._tree_view_widget.expand_all()

    # endregion

    # region === Callbacks === #

    # noinspection PyUnusedLocal
    def _on_tree_view_selection_changed(
        self, event: TreeViewWidgetSelectionChangedEvent
    ) -> None:
        """Callback function that is called when the selection in the tree
        view changes.

        Args:
            event: The selection changed event.
        """

        directories: list[dict[str, Any]] = []
        categories: list[str] = []

        current_selection = cast(
            list[CategoryFolder | FolderItem],
            self._tree_view_widget.selected_items(),
        )
        for data_source in current_selection:
            if type(data_source) == CategoryFolder:
                categories.append(data_source.folder_id())
                for child in cast(
                    Iterator[CategoryFolder | FolderItem],
                    data_source.iterate_children(),
                ):
                    if type(child) == FolderItem:
                        directories.append(child.internal_data)
            else:
                directories.append(data_source.internal_data)

        output_ids = [d["id"] for d in directories]

        self._preferences.set_active_directories(
            [DirectoryPath(**d) for d in directories]
        )
        self._preferences.set_active_categories(categories)
        self.selectionChanged.emit(output_ids)

    # endregion
