from __future__ import annotations

import typing

from Qt.QtCore import Signal, QSize
from Qt.QtWidgets import QWidget

from tp.preferences.interfaces.preferences import theme_interface

from .thumbslist.view import ThumbsListView
from .thumbslist.widgets.infowindow import InfoEmbeddedWindow
from ..buttons import BasePushButton
from ..layouts import VerticalLayout, HorizontalLayout
from ... import uiconsts, dpi

if typing.TYPE_CHECKING:
    from .thumbslist.model import ThumbsListModel


class ThumbBrowser(QWidget):
    _theme_interface = None

    def __init__(
        self,
        columns: int | None = None,
        icon_size: QSize | None = None,
        fixed_width: int | None = None,
        fixed_height: int | None = None,
        uniform_icons: bool = False,
        item_name: str = "",
        apply_text: str = "Apply",
        create_text: str = "New",
        select_directories_active: bool = False,
        parent: QWidget | None = None,
    ):
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

        self._uniform_icons = uniform_icons
        self._item_name = item_name
        self._apply_text = apply_text
        self._create_text = create_text
        self._saved_height: int | None = None

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

    @property
    def thumbs_list_view(self) -> ThumbBrowserListView:
        """The browser lists view widget."""

        return self._thumb_widget

    def setFixedHeight(self, height: int, save: bool = False):
        """Sets a fixed height for an object and optionally saves the height.

        Args:
            height: The fixed height to be applied to the object.
            save: Whether to save the height value. Defaults to False.
        """

        super().setFixedHeight(height)

        if save:
            self._saved_height = height

    def set_model(self, model: ThumbsListModel):
        """Set the model for the thumb list view.

        Args:
            model: The model to be set for the thumb list view.
        """

        self._thumb_widget.setModel(model)

    def set_columns(self, columns: int):
        """Set the number of columns for the thumb list view.

        Args:
            columns: The number of columns to be set.
        """

        # self._thumb_widget.set_columns(columns)

    def set_icon_size(self, icon_size: QSize):
        """Set the icon size for the thumb list view.

        Args:
            icon_size: The size of the icons to be set.
        """

        # self._thumb_widget.set_icon_size(icon_size)

    def _setup_widgets(self):
        """Set up the widgets for this widget."""

        self._thumb_widget = ThumbBrowserListView(
            uniform_icons=self._uniform_icons, parent=self
        )
        self._info_embedded_window = InfoEmbeddedWindow(
            parent=self._thumb_widget, margins=(0, 0, 0, uiconsts.SMALL_PADDING)
        )

    def _setup_layouts(self):
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
        self._folder_popup_button.setStyleSheet("background-color: transparent;")

        top_layout.addWidget(self._folder_popup_button)

        return top_layout

    def _setup_signals(self):
        """Set up the signals for this widget."""

        self._folder_popup_button.leftClicked.connect(
            self._on_folder_popup_button_clicked
        )

    def _on_folder_popup_button_clicked(self):
        """Handle the folder popup button click event."""

        print("Hello World")


class ThumbBrowserListView(ThumbsListView):
    pass


class ThumbSearchWidget(QWidget):
    searchChanged = Signal(object, object)

    def __init__(self, theme_pref, parent: QWidget | None = None):
        """Initialize the ThumbSearchWidget.

        Args:
            parent: The parent widget.
        """

        super().__init__(parent=parent)

        self._setup_widgets()
        self._setup_layouts()

    def _setup_widgets(self):
        """Set up the widgets for the search widget."""

        pass

    def _setup_layouts(self):
        """Set up the layouts for the search widget."""

        main_layout = HorizontalLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(main_layout)
