from __future__ import annotations

import typing

from Qt.QtWidgets import QWidget, QVBoxLayout

from tp.libs.qt import factory
from tp.preferences.interfaces import asset
from tp.libs.qt.widgets.window import Window
from tp.libs.qt.widgets.thumbsbrowser.browser import ThumbBrowser
from tp.libs.qt.widgets.thumbsbrowser.mixin import ThumbBrowserMixin

from ..core.model import AssetSceneModel

if typing.TYPE_CHECKING:
    from tp.preferences.assets import BrowserPreference


class AssetsView(QWidget, ThumbBrowserMixin):
    """Assets view widget."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        preferences: BrowserPreference = (
            asset.model_assets_interface().model_assets_preference
        )
        self.set_asset_preferences(preferences)

        self._setup_widgets()
        self._setup_layouts()

    def _setup_widgets(self):
        """Set up all view widgets."""

        uniform_icons = self.browser_preference.browser_uniform_icons()

        self._thumbs_browser = ThumbBrowser(
            uniform_icons=uniform_icons,
            columns=3,
            # fixed_height=382,
            item_name="Asset",
            apply_text="Import",
            select_directories_active=True,
            parent=self,
        )
        self._thumbs_model = AssetSceneModel(
            self._thumbs_browser.thumbs_list_view,
            directories=self.browser_preference.browser_folder_paths(),
        )
        self._thumbs_browser.set_model(self._thumbs_model)

    def _setup_layouts(self):
        """Set up the layouts and add all widgets to them."""

        main_layout = factory.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        main_layout.addWidget(self._thumbs_browser)


class AssetsWindow(Window):
    """Assets window."""

    def __init__(self, title="Assets Browser", width=1000, height=600, **kwargs):
        super().__init__(title=title, width=width, height=height, **kwargs)

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        """Set up all the widgets."""

        super().setup_widgets()

        self._assets_widget = AssetsView(parent=self)

    def setup_layouts(self, main_layout: QVBoxLayout):
        """Set up the layouts for the window."""

        super().setup_layouts(main_layout)

        main_layout.addWidget(self._assets_widget)
