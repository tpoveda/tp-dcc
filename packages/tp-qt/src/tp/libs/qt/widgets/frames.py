from __future__ import annotations

from typing import Any

from Qt.QtCore import Signal, QSize
from Qt.QtWidgets import (
    QApplication,
    QSizePolicy,
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QCheckBox,
)
from Qt.QtGui import QFont, QIcon, QMouseEvent

from tp.libs.python import paths

from .labels import BaseLabel
from .dividers import LabelDivider
from .layouts import HorizontalLayout, VerticalLayout
from .. import uiconsts, dpi, utils as qtutils


class BaseFrame(QFrame):
    mouseReleased = Signal(QMouseEvent)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.mouseReleased.emit(event)
        return super().mouseReleaseEvent(event)


class CollapsibleFrame(QWidget):
    """Widget for collapsible frame."""

    _COLLAPSED_ICON: QIcon | None = None
    _EXPAND_ICON: QIcon | None = None

    openRequested = Signal()
    closeRequested = Signal()
    toggled = Signal()

    def __init__(
        self,
        title: str,
        tooltip: str | None = None,
        collapsed: bool = False,
        collapsable: bool = True,
        checkable: bool = False,
        checked: bool = True,
        content_margins: tuple[int, int, int, int] = uiconsts.MARGINS,
        content_spacing: int = uiconsts.SPACING,
        parent: QWidget | None = None,
    ):
        """Initializes CollapsibleFrame

        :param title: The title of the frame.
        :param tooltip: The tooltip of the frame.
        :param collapsed: Whether the frame is initially collapsed.
        :param collapsable: Whether the frame is collapsible.
        :param checkable: Whether the frame is checkable.
        :param checked: Whether the frame is checked.
        :param content_margins: The content margins.
        :param content_spacing: The content spacing.
        :param parent: The parent widget.
        """

        super().__init__(parent=parent)

        self._title = title
        self._tooltip = tooltip
        self._collapsed = collapsed if collapsable else False
        self._collapsable = collapsable
        self._checkable = checkable
        self._checked = checked
        self._content_margins = content_margins
        self._content_spacing = content_spacing

        self._title_frame: BaseFrame | None = None
        self._horizontal_layout: QHBoxLayout | None = None
        self._icon_button: QPushButton | None = None
        self._title_label: QLabel | None = None
        self._spacer_item: QSpacerItem | None = None
        self._hider_widget: QFrame | None = None
        self._hider_layout: QVBoxLayout | None = None
        self._checkbox: QCheckBox | None = None

        if CollapsibleFrame._COLLAPSED_ICON is None:
            CollapsibleFrame._COLLAPSED_ICON = QIcon(
                paths.canonical_path("../../resources/icons/arrow_forward_64.png")
            )
        if CollapsibleFrame._EXPAND_ICON is None:
            CollapsibleFrame._EXPAND_ICON = QIcon(
                paths.canonical_path("../../resources/icons/arrow_expand_64.png")
            )

        self._main_layout = QVBoxLayout()
        self._main_layout.setSpacing(0)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._main_layout)

        self._setup_ui()
        self._setup_signals()

    @property
    def hider_layout(self) -> QVBoxLayout:
        """Getter method that returns hider layout instance.

        :returns: hider layout.
        """

        return self._hider_layout

    def add_widget(self, widget: QWidget):
        """Adds given widget into the content layout.

        :param widget: widget to add.
        """

        self._hider_layout.addWidget(widget)

    def add_layout(self, layout: QVBoxLayout | QHBoxLayout | QGridLayout):
        """Adds given widget into the content layout.

        :param layout: layout to add.
        """

        self._hider_layout.addLayout(layout)

    def expand(self):
        """Expands/Shows contents."""

        self.setUpdatesEnabled(False)
        self._hider_widget.show()
        self._icon_button.setIcon(self._EXPAND_ICON)
        self.setUpdatesEnabled(True)
        self.openRequested.emit()
        self._collapsed = False

    def collapse(self):
        """Collapses/Hides contents."""

        self.setUpdatesEnabled(False)
        self._hider_widget.hide()
        self._icon_button.setIcon(self._COLLAPSED_ICON)
        QApplication.processEvents()
        self.setUpdatesEnabled(True)
        QApplication.processEvents()
        self.closeRequested.emit()
        self._collapsed = True

    def _setup_ui(self):
        """Internal function that setup widgets."""

        self._build_title_frame()
        self._build_hider_widget()
        self._main_layout.addWidget(self._title_frame)
        self._main_layout.addWidget(self._hider_widget)

        qtutils.set_stylesheet_object_name(self._title_frame, "collapsed")

    def _setup_signals(self):
        """Internal function that setup signal connections."""

        self.openRequested.connect(self.toggled.emit)
        self.closeRequested.connect(self.toggled.emit)
        self._checkbox.toggled.connect(self._on_checkbox_toggled)
        self._icon_button.clicked.connect(self._on_icon_button_clicked)
        self._title_frame.mouseReleased.connect(self._on_title_frame_mouse_released)

    def _build_title_frame(self):
        """Internal function that builds the title part of the layout with a QFrame widget."""

        self._title_frame = BaseFrame(parent=self)
        self._title_frame.setContentsMargins(0, 0, 0, 0)
        self._horizontal_layout = QHBoxLayout()
        self._horizontal_layout.setSpacing(2)
        self._horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self._title_frame.setLayout(self._horizontal_layout)
        self._checkbox = QCheckBox(parent=self)
        self._checkbox.setChecked(self._checked)
        self._checkbox.setVisible(self._checkable)
        self._checkbox.setFixedSize(dpi.size_by_dpi(QSize(18, 18)))
        self._icon_button = QPushButton(parent=self)
        self._icon_button.setFixedSize(dpi.size_by_dpi(QSize(15, 15)))
        self._icon_button.setFlat(True)
        self._icon_button.setContentsMargins(0, 0, 0, 0)
        self._icon_button.setIcon(
            self._COLLAPSED_ICON if self._collapsed else self._EXPAND_ICON
        )
        self._title_label = QLabel(self._title, parent=self)
        font: QFont = self._title_label.font()
        font.setBold(True)
        self._title_label.setFont(font)
        self._title_label.setContentsMargins(0, 0, 0, 0)
        if self._tooltip:
            self._title_label.setToolTip(self._tooltip)
        self._spacer_item = QSpacerItem(
            10, 0, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        self._horizontal_layout.addSpacing(5)
        self._horizontal_layout.addWidget(self._checkbox)
        self._horizontal_layout.addWidget(self._icon_button)
        self._horizontal_layout.addWidget(self._title_label)
        self._horizontal_layout.addItem(self._spacer_item)

    def _build_hider_widget(self):
        """Internal function that builds the collapsable widget."""

        self._hider_widget = QFrame(parent=self)
        self._hider_widget.setContentsMargins(0, 0, 0, 0)
        self._hider_layout = QVBoxLayout()
        self._hider_layout.setSpacing(self._content_spacing)
        self._hider_layout.setContentsMargins(*self._content_margins)
        self._hider_widget.setLayout(self._hider_layout)
        self._hider_widget.setHidden(self._collapsed)
        self._hider_widget.setEnabled(True if not self._checkable else self._checked)

    def _show_hide_widget(self):
        """Internal function that shows/hides the hider widget which contains the contents specified by the user."""

        if not self._collapsable:
            return

        if self._collapsed:
            self.expand()
            return

        self.collapse()

    def _on_checkbox_toggled(self, flag: bool):
        """Internal callback function that is called each time checkbox is toggled by the user.

        :param flag: whether checkbox was checked or unchecked.
        """

        self._hider_widget.setEnabled(flag)

    # noinspection PyUnusedLocal
    def _on_icon_button_clicked(self, *args):
        """Internal callback function that is called each time icon button is clicked by the user."""

        self._show_hide_widget()

    # noinspection PyUnusedLocal
    def _on_title_frame_mouse_released(self, *args):
        """Internal callback function that is called each time mouse is released over title frame."""

        self._show_hide_widget()


class CollapsibleFrameThin(CollapsibleFrame):
    def _build_title_frame(self):
        super()._build_title_frame()

        title_divider = LabelDivider(parent=self)
        self._spacer_item.changeSize(dpi.dpi_scale(3), 0)
        title_divider.setToolTip(self.toolTip())
        self._horizontal_layout.addWidget(title_divider, 1)


class EmbeddedWindow(QFrame):
    """An embedded window that appears like a window inside another UI.

    This is not a real window but a `QFrame` widget styled to look like one.
    It provides a simple interface with an optional title and close button,
    and can be easily shown or hidden.

    The content area is managed through a `QVBoxLayout` that can be accessed
    via the ` get_layout () ` method.

    Attributes:
        visibilityChanged: Signal emitted when visibility changes.
    """

    visibilityChanged = Signal(bool)

    def __init__(
        self,
        title: str = "",
        default_visibility: bool = False,
        uppercase: bool = False,
        close_button: QPushButton | None = None,
        margins: tuple[int, int, int, int] = (0, 0, 0, 0),
        parent: QWidget | None = None,
    ):
        """Initialize the EmbeddedWindow.

        Args:
            parent: The parent widget to parent this widget to.
            title: The title of the window can be changed later.
            default_visibility: Whether the embedded window is initially
                visible.
            uppercase: Whether to display the title in uppercase.
            margins: Margins for the outer layout as (left, top, right, bottom).
        """

        super().__init__(parent=parent)

        self._title = title
        self._margins = margins
        self._parent_widget = parent
        self._uppercase = uppercase
        self._hide_properties_button = close_button

        self._target_saved_height: int | None = None
        self._inner_frame: QFrame | None = None
        self._outer_layout: HorizontalLayout | None = None
        self._properties_layout: VerticalLayout | None = None
        self._property_title_layout: HorizontalLayout | None = None
        self._properties_label: BaseLabel | None = None

        self.set_visible(default_visibility)

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def sizeHint(self) -> QSize:
        """Return the size hint for the widget.

        The size hint represents the recommended size for the widget, and
        this method ensures that the widget's minimum height is adjusted
        according to the computed size hint, forcing the contents to never
        get squashed.

        Returns:
            The suggested size for the widget.
        """

        size_hint = super().sizeHint()
        self.setMinimumHeight(size_hint.height())

        return size_hint

    def get_layout(self) -> VerticalLayout:
        """Get the layout of the embedded window.

        Notes:
            It allows adding widgets or layouts to this window.

        Returns:
            The vertical layout of the embedded window.
        """

        return self._properties_layout

    def get_title_label(self) -> BaseLabel:
        """Get the title label of the embedded window.

        Returns:
            The title label of the embedded window.
        """

        return self._properties_label

    def get_hide_button(self) -> QPushButton | None:
        """Get the hide button of the embedded window.

        Returns:
            The hide button of the embedded window, or None if not set.
        """

        return self._hide_properties_button

    def set_visible(self, visible: bool):
        """Set the visibility of the embedded window.

        Args:
            visible: Whether to show or hide the embedded window.
        """

        self.setHidden(not visible)
        self.visibilityChanged.emit(visible)

    def show_window(self):
        """Show the embedded window."""

        self.set_visible(True)

    def hide_window(self):
        """Hide the embedded window."""

        self.set_visible(False)

    def set_title(self, title: str):
        """Set the title for the property label and adjusts the layout's
        stretch.

        Args:
            title: The title to set for the property label. If an empty
                string or `None` is provided, the label will be hidden and the
                stretch factor will be reset.
        """
        if title:
            self._property_title_layout.setStretch(
                self._properties_layout.indexOf(self._properties_label), 0
            )
        else:
            self._property_title_layout.setStretch(0, 0)

        self._properties_label.setVisible(bool(title))
        self._properties_label.setText(title)

    def get_state(self) -> dict[str, Any]:
        """Retrieve the state of a specific object.

        Returns:
            A dictionary containing the current state of the object, including:
                - "visible": Boolean indicating the visibility status.
                - "savedSize": The saved height or size of the target object.
        """
        return {
            "visible": self.isVisible(),
            "savedSize": self._target_saved_height,
        }

    def set_state(self, state: dict[str, Any]):
        """Set the state of the object using the provided state dictionary. T

        Args:
            state: A dictionary containing the state information.
                The keys in the dictionary should include:
                - "savedSize": The saved size of the target.
                - "visible": A boolean representing the visibility state.
        """

        self._target_saved_height = state.get("savedSize", None)
        self.set_visible(state.get("visible", False))

    def _setup_widgets(self):
        """Set up the widgets for the embedded window."""

        self._inner_frame = QFrame(parent=self)
        self._inner_frame.setObjectName("embeddedWindowBackground")
        self._inner_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        self._properties_label = BaseLabel(
            self._title, upper=self._uppercase, parent=self, bold=True
        )
        if not self._title:
            self._properties_label.setVisible(False)

    def _setup_layouts(self):
        """Set up the layouts for the embedded window."""

        self._outer_layout = HorizontalLayout()
        self._outer_layout.setContentsMargins(*self._margins)
        self.setLayout(self._outer_layout)
        self._outer_layout.addWidget(self._inner_frame)

        self._properties_layout = VerticalLayout()
        self._properties_layout.setSpacing(uiconsts.SPACING)
        self._properties_layout.setContentsMargins(
            uiconsts.WINDOW_SIDE_PADDING,
            4,
            uiconsts.WINDOW_SIDE_PADDING,
            uiconsts.WINDOW_BOTTOM_PADDING,
        )
        self._inner_frame.setLayout(self._properties_layout)

        self._property_title_layout = HorizontalLayout()
        self._property_title_layout.setSpacing(uiconsts.SMALL_SPACING)
        self._property_title_layout.setContentsMargins(0, 0, 3, 0)
        self._property_title_layout.addWidget(self._properties_label, 10)
        if self._hide_properties_button:
            self._property_title_layout.addWidget(self._hide_properties_button, 10)
        self._properties_layout.addLayout(self._property_title_layout)

    def _setup_signals(self):
        """Set up the signals for the embedded window."""

        if self._hide_properties_button:
            self._hide_properties_button.clicked.connect(self.hide_window)
