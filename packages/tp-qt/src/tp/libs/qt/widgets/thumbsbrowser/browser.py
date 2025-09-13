from __future__ import annotations

import os
import enum
import typing
from dataclasses import dataclass
from typing import Iterable, Callable, Any

from loguru import logger
from Qt.QtCore import Qt, Signal, QSize
from Qt.QtWidgets import QWidget, QAction, QStyledItemDelegate
from Qt.QtGui import QIcon

from tp.libs.python import osplatform
from tp.preferences.interfaces.preferences import theme_interface

from .directorypopup import DirectoryPopup
from .thumbslist.view import ThumbsListView
from .thumbslist.widgets.infowindow import InfoEmbeddedWindow
from ..buttons import BasePushButton, IconMenuButton
from ..search import SearchLineEdit
from ..layouts import VerticalLayout, HorizontalLayout
from ..mouseslider import SliderSettings
from ... import uiconsts, dpi, icons

if typing.TYPE_CHECKING:
    from .thumbslist.model import ThumbsListModel, ItemData


class ThumbBrowser(QWidget):
    _theme_interface = None

    def __init__(
        self,
        delegate_class: type[QStyledItemDelegate] | None = None,
        columns: int | None = None,
        icon_size: QSize | None = None,
        fixed_width: int | None = None,
        fixed_height: int | None = None,
        uniform_icons: bool = False,
        item_name: str = "",
        apply_text: str = "Apply",
        apply_icon: QIcon | None = None,
        create_text: str = "New",
        new_active: bool = True,
        snapshot_active: bool = False,
        snapshot_new_active: bool = False,
        clipboard_active: bool = False,
        create_thumbnail_active: bool = False,
        select_directories_active: bool = False,
        mouse_slider: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the ThumbBrowser widget.

        Args:
            columns: The number of square image columns.
            icon_size: The size of the icons (in pixels).
            fixed_width: The fixed width of the widget (in pixels).
            fixed_height: The fixed height of the widget (in pixels).
            uniform_icons: Whether to use uniform icons. If True, icons will
                be clipped to keep icons square.
            parent: The parent widget.
        """

        super().__init__(parent=parent)

        if ThumbBrowser._theme_interface is None:
            ThumbBrowser._theme_interface = theme_interface()

        self._delegate_class = delegate_class
        self._uniform_icons = uniform_icons
        self._item_name = item_name
        self._apply_text = apply_text
        self._apply_icon = apply_icon or icons.icon("checkmark")
        self._create_text = create_text
        self._saved_height: int | None = None
        self._mouse_slider = mouse_slider
        self._mouse_slider_settings: SliderSettings = {}
        self._select_directories_active = select_directories_active

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

        if columns is not None:
            self.set_columns(columns)
        if fixed_height:
            self.setFixedHeight(dpi.dpi_scale(fixed_height), save=True)
        if fixed_width:
            self.setFixedWidth(dpi.dpi_scale(fixed_width))
        if icon_size is not None:
            self.set_icon_size(icon_size)

        self._dots_menu.set_create_visible(new_active)
        self._dots_menu.set_snapshot_visible(snapshot_active)
        self._dots_menu.set_from_clipboard_visible(clipboard_active)
        self._dots_menu.set_from_snapshot_visible(snapshot_new_active)
        self._dots_menu.set_create_thumbnail_visible(create_thumbnail_active)

    # region === Setup === #

    @property
    def thumbs_list_view(self) -> ThumbsListView:
        """The browser lists view widget."""

        return self._thumb_widget

    def _setup_widgets(self) -> None:
        """Set up the widgets for this widget."""

        self._directory_popup = DirectoryPopup(parent=self)
        self._thumb_widget = ThumbsListView(
            delegate_class=self._delegate_class,
            uniform_icons=self._uniform_icons,
            mouse_slider=self._mouse_slider,
            slider_settings=self._mouse_slider_settings,
            parent=self,
        )
        self._info_embedded_window = InfoEmbeddedWindow(
            parent=self._thumb_widget, margins=(0, 0, 0, uiconsts.SMALL_PADDING)
        )

    def _setup_layouts(self) -> None:
        """Set up the layouts for this widget."""

        main_layout = VerticalLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        main_layout.addLayout(self._setup_top_bar())
        main_layout.addWidget(self._info_embedded_window)
        main_layout.addWidget(self._thumb_widget, 1)

    def _setup_top_bar(self) -> HorizontalLayout:
        """Set up the top bar layout for the thumb browser."""

        top_layout = HorizontalLayout()
        top_layout.setSpacing(uiconsts.SMALL_SPACING)
        top_layout.setContentsMargins(0, 0, 0, uiconsts.SPACING)

        self._folder_popup_button = BasePushButton(parent=self)
        self._folder_popup_button.setToolTip("Folder")
        self._folder_popup_button.set_icon("folder")
        self._folder_popup_button.setVisible(self._select_directories_active)

        self._search_widget = ThumbSearchWidget(parent=self)

        self._info_button = BasePushButton(parent=self)
        self._info_button.setToolTip("Thumbnail information and add metadata")
        self._info_button.set_icon("info_circle")

        self._dots_menu = ThumbBrowserDotsMenu(
            uniform_icons=self._uniform_icons,
            item_name=self._item_name,
            apply_text=self._apply_text,
            apply_icon=self._apply_icon,
            create_text=self._create_text,
            parent=self,
        )

        top_layout.addWidget(self._folder_popup_button)
        top_layout.addWidget(self._search_widget)
        top_layout.addWidget(self._info_button)
        top_layout.addWidget(self._dots_menu)

        return top_layout

    def _setup_signals(self) -> None:
        """Set up the signals for this widget."""

        self._folder_popup_button.leftClicked.connect(
            self._on_folder_popup_button_clicked
        )
        self._search_widget.searchChanged.connect(self._on_search_changed)
        self._info_button.leftClicked.connect(self._on_info_button_clicked)
        self._dots_menu.uniformIconActionTriggered.connect(
            self._on_menu_uniform_icons_action_toggled
        )
        self._dots_menu.browseActionTriggered.connect(
            self._on_menu_browse_action_triggered
        )

    # endregion

    # region === Visuals === #

    def set_columns(self, columns: int) -> None:
        """Set the number of columns for the thumb list view.

        Args:
            columns: The number of columns to be set.
        """

        self._thumb_widget.set_columns(columns)

    def icon_size(self) -> QSize:
        """Get the icon size for the thumb list view.

        Returns:
            The size of the icons.
        """

        return self._thumb_widget.iconSize()

    def set_icon_size(self, icon_size: QSize):
        """Set the icon size for the thumb list view.

        Args:
            icon_size: The size of the icons to be set.
        """

        self._thumb_widget.setIconSize(icon_size)

    def close_directory_popup(self) -> None:
        """Close the directory popup if it's open."""

        self._directory_popup.close()

    def _update_uniform_icons(self):
        pass

    # region === Filtering === #

    def _select_directories(self) -> None:
        pass

    def set_persistent_filter(self, text: str, tags: Iterable[str]) -> None:
        """Set a persistent filter for the items in the thumb list view.

        Args:
            text: The text to filter the items by.
            tags: The tags to filter the items by.
        """

        self._thumb_widget.set_persistent_filter(text, tags)

    def filter(self, text, tags: Iterable[str] | None = None) -> None:
        """Filter the items in the thumb list view.

        Args:
            text: The text to filter the items by.
            tags: The tags to filter the items by.
        """

        self._thumb_widget.filter(text, tags)

    # endregion

    # region === Info Window === #

    def _toggle_info_visibility(self):
        print("Toggling info visibility")

    # endregion

    # region === Browsing === #

    def model(self) -> ThumbsListModel | None:
        """Get the current model of the thumb list view.

        Returns:
            The current model of the thumb list view.
        """

        return self._thumb_widget.root_model()

    def set_model(self, model: ThumbsListModel) -> None:
        """Set the model for the thumb list view.

        Args:
            model: The model to be set for the thumb list view.
        """

        self._thumb_widget.setModel(model)
        self._info_embedded_window.set_model(model)

        model.refresh_asset_folders()
        model.refresh()

        # noinspection PyBroadException
        try:
            self._directory_popup.selectionChanged.disconnect(
                self._on_directory_popup_selection_changed
            )
        except Exception:
            pass
        self._directory_popup.selectionChanged.connect(
            self._on_directory_popup_selection_changed
        )
        model.itemSelectionChanged.connect(self._on_model_item_selection_changed)

    def current_item_data(self) -> ItemData | None:
        """Get the data of the currently selected item in the thumb list view.

        Returns:
            The data of the currently selected item, or `None` if no item is
                selected.
        """

        return self.model().current_item_data

    def _browse_directory(self) -> None:
        """Open a file browser pointing to the current directory."""

        current_item = self.current_item_data()
        directory = current_item.directory if current_item else None
        if directory is None:
            active_directories = self.model().active_directories()
            directory = active_directories[0].path if active_directories else None

        if not directory:
            logger.warning("No directory to browse to")
            return

        os.startfile(directory)

    def _toggle_directory_popup_visibility(self) -> None:
        """Toggle the visibility of the directory popup."""

        if self._directory_popup.isVisible():
            self._directory_popup.close()
            return

        self._update_directory_popup()
        self._directory_popup.show()

    def _update_directory_popup(self) -> None:
        """Update the directory popup with the current directories from the
        model.
        """

        model = self.model()

        model.update_from_prefs()
        self._directory_popup.set_anchor_widget(self)
        self._directory_popup.preferences = model.preferences
        self._directory_popup.reset()
        self._directory_popup.set_active_items(model.active_directories(), model.preferences.active_categories())

    # endregion

    # region === Saving/Restoring State === #

    def setFixedHeight(self, height: int, save: bool = False) -> None:
        """Sets a fixed height for an object and optionally saves the height.

        Args:
            height: The fixed height to be applied to the object.
            save: Whether to save the height value. Defaults to False.
        """

        super().setFixedHeight(height)

        if save:
            self._saved_height = height

    # endregion

    # region === Callbacks === #

    def _on_folder_popup_button_clicked(self) -> None:
        """Handle the folder popup button click event."""

        self._toggle_directory_popup_visibility()

    def _on_search_changed(self, text: str, filter_data: Any) -> None:
        """Handle the search changed event.

        Args:
            text: The new search text.
            filter_data: The filter data.
        """

    def _on_info_button_clicked(self) -> None:
        """Handle the info button click event."""

    def _on_menu_uniform_icons_action_toggled(self) -> None:
        """Handle the uniform icons action toggled event."""

    def _on_menu_browse_action_triggered(self) -> None:
        """Handle the browse action triggered event."""

        self._browse_directory()

    def _on_directory_popup_selection_changed(self):
        """Handle the directory popup selection changed event."""

    def _on_model_item_selection_changed(self):
        """Handle the model item selection changed event."""

        pass

    # endregion


class ThumbSearchWidget(QWidget):
    searchChanged = Signal(object, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the `ThumbSearchWidget`.

        Args:
            parent: The parent widget.
        """

        super().__init__(parent=parent)

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

        # self.setFixedHeight(dpi.dpi_scale(24))

    # region === Setup === #

    def _setup_widgets(self):
        """Set up the widgets for the search widget."""

        self._filter_menu = IconMenuButton(switch_icon_on_click=True, parent=self)
        self._filter_menu.setToolTip("Search filter by meta data")
        self._filter_menu.addAction(
            "Name And Tags",
            action_icon=icons.icon("filter"),
            icon_text="filter",
            data=["filename", "tags"],
        )
        self._filter_menu.addAction(
            "File Name",
            action_icon=icons.icon("file"),
            icon_text="file",
            data="filename",
        )
        self._filter_menu.addAction(
            "Description",
            action_icon=icons.icon("info_popup"),
            icon_text="info_popup",
            data="description",
        )
        self._filter_menu.addAction(
            "Tags",
            action_icon=icons.icon("tag"),
            icon_text="tag",
            data="tags",
        )
        self._filter_menu.addAction(
            "Creators",
            action_icon=icons.icon("user"),
            icon_text="user",
            data="creators",
        )
        self._filter_menu.addAction(
            "Websites",
            action_icon=icons.icon("web"),
            icon_text="web",
            data="websites",
        )
        self._filter_menu.addAction(
            "All",
            action_icon=icons.icon("check_all"),
            icon_text="check_all",
            data=["filename", "description", "tags", "creators", "websites"],
        )
        self._filter_menu.set_menu_name("Name And Tags")
        self._filter_menu.menu_align = Qt.AlignLeft

        self._search_line_edit = SearchLineEdit(parent=self)
        self._search_line_edit.setPlaceholderText("Search...")

    def _setup_layouts(self):
        """Set up the layouts for the search widget."""

        main_layout = HorizontalLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(main_layout)

        main_layout.addWidget(self._filter_menu)
        main_layout.addWidget(self._search_line_edit)

    def _setup_signals(self):
        """Set up the signals for the search widget."""

        self._search_line_edit.textChanged.connect(self._on_search_text_changed)
        self._filter_menu.actionTriggered.connect(self._on_filter_menu_action_triggered)

    # endregion

    # region === Callbacks === #

    def _on_search_text_changed(self, text: str) -> None:
        """Handle the search text changed event.

        Args:
            text: The new search text.
        """

        filter_data = self._filter_menu.current_action().data()
        self.searchChanged.emit(text, filter_data)

    # noinspection PyUnusedLocal
    def _on_filter_menu_action_triggered(
        self, action: QAction, mouse_menu: Qt.MouseButton
    ) -> None:
        """Handle the filter menu action triggered event.

        Args:
            action: The action that was triggered.
            mouse_menu: The mouse button that triggered the action.
        """

        filter_data = action.data()
        text = self._search_line_edit.text()
        self.searchChanged.emit(text, filter_data)

    # endregion


class ThumbBrowserMenuActionType(enum.IntEnum):
    """Enum for the different types of actions in the thumb browser menu."""

    Apply = 0
    Create = 1
    Rename = 2
    Delete = 3
    Browse = 4
    SetDirection = 5
    SelectDirectories = 6
    Refresh = 7
    UniformIcons = 8
    Snapshot = 9
    SnapshotNew = 10
    CreateThumbnail = 11
    NewThumbnailFromClipboard = 12


@dataclass
class ThumbBrowserMenuActionData:
    """Data class for the thumb browser menu action data."""

    id: ThumbBrowserMenuActionType
    text: str
    callback: Callable
    icon: QIcon
    checkable: bool = False
    enabled: bool = True


class ThumbBrowserDotsMenu(IconMenuButton):
    applyActionTriggered = Signal()
    createActionTriggered = Signal()
    renameActionTriggered = Signal()
    deleteActionTriggered = Signal()
    browseActionTriggered = Signal()
    setDirectoryActionTriggered = Signal()
    selectDirectoriesActionTriggered = Signal()
    refreshActionTriggered = Signal()
    uniformIconActionTriggered = Signal(object)
    snapshotActionTriggered = Signal()
    snapshotNewActionTriggered = Signal()
    createThumbnailActionTriggered = Signal()
    newFromClipboardTriggered = Signal()

    def __init__(
        self,
        uniform_icons: bool,
        item_name: str,
        apply_text: str,
        apply_icon: QIcon,
        create_text: str,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the `ThumbBrowserDotsMenu`.

        Args:
            uniform_icons: Whether to use uniform icons. If True, icons will
                be clipped to keep icons square.
            parent: The parent widget.
        """

        self._uniform_icons = uniform_icons
        self._item_name = item_name
        self._apply_text = apply_text
        self._create_text = create_text
        self._apply_icon = apply_icon
        self._menu_actions: dict[ThumbBrowserMenuActionType, QAction] = {}

        super().__init__(parent=parent)

    # region === Setup === #

    def setup_ui(self):
        super().setup_ui()

        self.set_icon(icons.icon("menu_dots"), size=16)
        self.setToolTip(f"File menu. Manage {self._item_name}")
        self.menu_align = Qt.AlignRight

        new_actions = [
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.Apply,
                text=f"{self._apply_text} (Double Click)",
                callback=self.applyActionTriggered,
                icon=self._apply_icon,
                checkable=False,
                enabled=True,
            ),
            None,
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.Create,
                text=f"{self._create_text} {self._item_name}",
                callback=self.createActionTriggered,
                icon=icons.icon("save"),
                checkable=False,
                enabled=True,
            ),
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.Rename,
                text="Rename",
                callback=self.renameActionTriggered,
                icon=icons.icon("crayon"),
                checkable=False,
                enabled=True,
            ),
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.Delete,
                text="Delete",
                callback=self.deleteActionTriggered,
                icon=icons.icon("trash"),
                checkable=False,
                enabled=True,
            ),
            None,
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.SetDirection,
                text=f"Set {self._item_name} Directory...",
                callback=self.setDirectoryActionTriggered,
                icon=icons.icon("add_folder"),
                checkable=False,
                enabled=True,
            ),
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.SelectDirectories,
                text="Select Directories...",
                callback=self.selectDirectoriesActionTriggered,
                icon=icons.icon("add_folder"),
                checkable=False,
                enabled=False,
            ),
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.Browse,
                text=f"Open in {'Explorer' if osplatform.is_windows() else 'Finder'}",
                callback=self.browseActionTriggered,
                icon=icons.icon("opened_folder"),
                checkable=False,
                enabled=True,
            ),
            None,
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.Refresh,
                text="Refresh Thumbnails",
                callback=self.refreshActionTriggered,
                icon=icons.icon("reload"),
                checkable=False,
                enabled=True,
            ),
            None,
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.UniformIcons,
                text="Square Icons",
                callback=self.uniformIconActionTriggered.emit,
                icon=icons.icon("square"),
                checkable=True,
                enabled=False,
            ),
            None,
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.Snapshot,
                text="Take New Snapshot",
                callback=self._on_new_snapshot_toggled,
                icon=icons.icon("camera"),
                checkable=False,
                enabled=True,
            ),
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.SnapshotNew,
                text="Replace Image",
                callback=self._on_replace_image_toggled,
                icon=icons.icon("camera"),
                checkable=False,
                enabled=False,
            ),
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.NewThumbnailFromClipboard,
                text="Paste Thumbnail from Clipboard",
                callback=self.newFromClipboardTriggered,
                icon=icons.icon("clipboard"),
                checkable=False,
                enabled=True,
            ),
            ThumbBrowserMenuActionData(
                id=ThumbBrowserMenuActionType.CreateThumbnail,
                text="New Thumbnail",
                callback=self.createThumbnailActionTriggered,
                icon=self._apply_icon,
                checkable=False,
                enabled=True,
            ),
        ]

        for action_data in new_actions:
            if action_data is None:
                self.add_separator()
            else:
                self._menu_actions[action_data.id] = self.addAction(
                    action_data.text,
                    connect=action_data.callback,
                    action_icon=action_data.icon,
                    checkable=action_data.checkable,
                )
                self._menu_actions[action_data.id].setEnabled(action_data.enabled)

    @property
    def apply_action(self) -> QAction:
        """The apply action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.Apply]

    @property
    def create_action(self) -> QAction:
        """The create action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.Create]

    @property
    def rename_action(self) -> QAction:
        """The rename action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.Rename]

    @property
    def delete_action(self) -> QAction:
        """The delete action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.Delete]

    @property
    def browse_action(self) -> QAction:
        """The browse action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.Browse]

    @property
    def set_directory_action(self) -> QAction:
        """The set directory action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.SetDirection]

    @property
    def refresh_action(self) -> QAction:
        """The refresh action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.Refresh]

    @property
    def uniform_icon_action(self) -> QAction:
        """The uniform icon action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.UniformIcons]

    @property
    def snapshot_action(self) -> QAction:
        """The snapshot action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.Snapshot]

    @property
    def snapshot_new_action(self) -> QAction:
        """The snapshot new action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.SnapshotNew]

    @property
    def create_thumbnail_action(self) -> QAction:
        """The create thumbnail action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.CreateThumbnail]

    @property
    def new_from_clipboard_action(self) -> QAction:
        """The new from clipboard action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.NewThumbnailFromClipboard]

    @property
    def select_directories_action(self) -> QAction:
        """The select directories action from the menu."""

        return self._menu_actions[ThumbBrowserMenuActionType.SelectDirectories]

    # endregion

    # region === State === #

    def set_create_visible(self, active: bool) -> None:
        """Set whether the create action is active.

        Args:
            active: Whether the create action is active.
        """

        self._set_action_visible(ThumbBrowserMenuActionType.Create, active)

    def set_rename_visible(self, active: bool) -> None:
        """Set whether the rename action is active.

        Args:
            active: Whether the rename action is active.
        """

        self._set_action_visible(ThumbBrowserMenuActionType.Rename, active)

    def set_snapshot_visible(self, active: bool) -> None:
        """Set whether the snapshot action is active.

        Args:
            active: Whether the snapshot action is active.
        """

        self._set_action_visible(ThumbBrowserMenuActionType.Snapshot, active)

    def set_delete_visible(self, active: bool) -> None:
        """Set whether the delete action is active.

        Args:
            active: Whether the delete action is active.
        """

        self._set_action_visible(ThumbBrowserMenuActionType.Delete, active)

    def set_from_clipboard_visible(self, active: bool) -> None:
        """Set whether the 'from clipboard' action is active.

        Args:
            active: Whether the 'from clipboard' action is active.
        """

        self._set_action_visible(
            ThumbBrowserMenuActionType.NewThumbnailFromClipboard, active
        )

    def set_from_snapshot_visible(self, active: bool) -> None:
        """Set whether the 'from snapshot' action is active.

        Args:
            active: Whether the 'from snapshot' action is active.
        """

        self._set_action_visible(ThumbBrowserMenuActionType.SnapshotNew, active)

    def set_create_thumbnail_visible(self, active: bool) -> None:
        """Set whether the 'create thumbnail' action is active.

        Args:
            active: Whether the 'create thumbnail' action is active.
        """

        self._set_action_visible(ThumbBrowserMenuActionType.CreateThumbnail, active)

    def set_directory_visible(self, active: bool) -> None:
        """Set whether the set directory action is active.

        Args:
            active: Whether the set directory action is active.
        """

        self._set_action_visible(ThumbBrowserMenuActionType.SetDirection, active)

    def _set_action_visible(
        self, action_id: ThumbBrowserMenuActionType, active: bool
    ) -> None:
        """Set whether a specific action is active (visible) in the menu.

        Args:
            action_id: The ID of the action to set.
            active: Whether the action should be active (visible).
        """

        action = self._menu_actions.get(action_id)
        if not action:
            logger.warning(f"Action {action_id} not found in menu")
            return

        action.setVisible(active)

    # endregion

    # === Callbacks === #

    def _on_new_snapshot_toggled(self):
        pass

    def _on_replace_image_toggled(self):
        pass

    # endregion
