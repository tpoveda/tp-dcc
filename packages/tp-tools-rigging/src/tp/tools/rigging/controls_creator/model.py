from __future__ import annotations

import typing

from Qt.QtCore import QObject

from tp.libs.qt import Model, UiProperty
from tp.preferences.interfaces import rigging
from tp.libs.qt.widgets import ThumbsListModel

from . import adapter

if typing.TYPE_CHECKING:
    from tp.preferences.assets import BrowserPreference


class ControlsCreatorModel(Model):
    """Model class for the Controls Creator tool panel."""

    @property
    def browser_model(self) -> ControlCurvesViewerModel:
        """The thumbnail browser model."""

        return self._browser_model

    # noinspection PyAttributeOutsideInit
    def initialize_properties(self) -> list[UiProperty]:
        """Initializes the properties associated with the instance.

        Returns:
            A list of initialized UI properties.
        """

        self._control_prefs = rigging.controls_creator_interface()
        self._thumbs_browser_preferences: BrowserPreference = (
            self._control_prefs.control_assets
        )
        self._browser_model = ControlCurvesViewerModel(
            uniform_icons=self._thumbs_browser_preferences.browser_uniform_icons(),
            preferences=self._thumbs_browser_preferences,
        )

        return [
            UiProperty("directories", [], type=list[str]),
            UiProperty("active_directories", [], type=list[str]),
        ]


class ControlCurvesViewerModel(ThumbsListModel):
    def __init__(
        self,
        directories: list[str] | None = None,
        active_directories: list[str] | None = None,
        chunk_count: int | None = None,
        uniform_icons: bool = False,
        include_sub_directories: bool = False,
        preferences: BrowserPreference | None = None,
        parent: QObject | None = None,
    ) -> None:
        """Initialize the `ThumbsListModel`.

        Args:
            directories: A list of directory paths to load thumbnails from.
            active_directories: A list of active directory paths to filter
            chunk_count: Number of items to load per chunk for lazy loading.
            uniform_icons: Whether to use uniform icons for all items.
            include_sub_directories: Whether to include subdirectories when
                loading thumbnails.
            parent: The parent QObject, if any.
        """

        super().__init__(
            extensions=[adapter.get().get_curve_file_extension()],
            directories=directories,
            active_directories=active_directories,
            chunk_count=chunk_count,
            uniform_icons=uniform_icons,
            include_sub_directories=include_sub_directories,
            preferences=preferences,
            parent=parent,
        )

    def _update_items(self):
        super()._update_items()
