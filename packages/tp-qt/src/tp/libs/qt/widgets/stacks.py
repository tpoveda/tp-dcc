from __future__ import annotations

from Qt.QtCore import Qt, Signal, QObject, QRegularExpression
from Qt.QtWidgets import QWidget, QStackedWidget, QFrame, QLineEdit
from Qt.QtGui import (
    QIcon,
    QValidator,
    QRegularExpressionValidator,
    QFocusEvent,
    QMouseEvent,
)

from .buttons import BaseButton
from .layouts import VerticalLayout, HorizontalLayout
from .. import dpi, icons, contexts
from ..mixins import stacked_animation_mixin


@stacked_animation_mixin
class SlidingOpacityStackedWidget(QStackedWidget):
    """Custom stack widget that activates opacity animation when
    the current stack index changes
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)


class StackWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._setup_widgets()
        self._setup_layouts()

    # region === Setup === #

    def _setup_widgets(self):
        """Set up the widgets for the stack widget."""

        self._stack = SlidingOpacityStackedWidget(parent=self)

    def _setup_layouts(self):
        """Set up the layouts for the stack widget."""

        main_layout = VerticalLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        main_layout.addWidget(self._stack)

    # endregion


class StackTitleFrame(QFrame, dpi.DPIScaling):
    minimized = Signal()
    maximized = Signal()
    toggleExpandRequested = Signal(bool)
    shiftUpPressed = Signal()
    shiftDownPressed = Signal()
    deletePressed = Signal()
    updateRequested = Signal()

    def __init__(
        self,
        title: str = "",
        title_editable: bool = False,
        icon: QIcon | None = None,
        item_icon_size: int = 20,
        icons_size: int = 16,
        collapsed: bool = True,
        shift_arrows_enabled: bool = True,
        delete_button_enabled: bool = True,
        delete_icon: QIcon | None = None,
        upper: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self._title = title
        self._upper = upper
        self._collapsed = collapsed
        self._shift_arrows_enabled = shift_arrows_enabled
        self._delete_button_enabled = delete_button_enabled
        self._title_editable = title_editable
        self._item_icon = icon or icons.icon("dashboard_layout")
        self._item_icon_size = item_icon_size
        self._icons_size = icons_size
        self._collapsed_icon = icons.icon("arrow_forward")
        self._expanded_icon = icons.icon("arrow_expand")
        self._down_icon = icons.icon("sort_down")
        self._up_icon = icons.icon("sort_up")
        self._delete_icon = delete_icon or icons.icon("cancel_circle")
        self._highlight_offset = 40

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

        self.setFixedHeight(self.sizeHint().height() + dpi.dpi_scale(2))
        self.setMinimumSize(
            self.sizeHint().width(), self.sizeHint().height() + dpi.dpi_scale(1)
        )

    # region === Setup === #

    @property
    def main_layout(self) -> HorizontalLayout:
        """The main layout of the stack title frame."""

        return self._main_layout

    @property
    def expand_toggle_button(self) -> BaseButton:
        """The expand/collapse toggle button."""

        return self._expand_toggle_button

    @property
    def line_edit(self) -> LineClickEdit:
        """The line edit for the title."""

        return self._line_edit

    def _setup_widgets(self) -> None:
        """Set up the widgets for the stack title frame."""

        self._line_edit = LineClickEdit(text=self._title, upper=self._upper)
        if not self._title_editable:
            self._line_edit.setReadOnly(True)

        self._item_icon_button = BaseButton(parent=self)
        self._item_icon_button.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._item_icon_button.set_icon(self._item_icon, size=self._item_icon_size)
        self._expand_toggle_button = BaseButton(parent=self)
        self._expand_toggle_button.set_icon(
            self._collapsed_icon if self._collapsed else self._expanded_icon
        )
        self._shift_down_button = BaseButton(parent=self)
        self._shift_down_button.set_icon(self._down_icon, size=self._icons_size)
        self._shift_up_button = BaseButton(parent=self)
        self._shift_up_button.set_icon(self._up_icon, size=self._icons_size)
        self._delete_button = BaseButton(parent=self)
        self._delete_button.set_icon(self._delete_icon, size=self._icons_size)

        if not self._shift_arrows_enabled:
            self._shift_down_button.hide()
            self._shift_up_button.hide()

        if not self._delete_button_enabled:
            self._delete_button.hide()

    def _setup_layouts(self) -> None:
        """Set up the layouts for the stack title frame."""

        self._main_layout = HorizontalLayout()
        self._main_layout.setSpacing(0)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._main_layout)

        extras_layout = HorizontalLayout()
        extras_layout.setSpacing(0)
        extras_layout.setContentsMargins(0, 0, 0, 0)

        line_edit_layout = VerticalLayout()
        line_edit_layout.setSpacing(0)
        line_edit_layout.setContentsMargins(0, 0, 0, 0)
        line_edit_layout.addWidget(self._line_edit)

        self._main_layout.addWidget(self._expand_toggle_button)
        self._main_layout.addWidget(self._item_icon_button)
        self._main_layout.addSpacing(dpi.dpi_scale(10))
        self._main_layout.addLayout(line_edit_layout, stretch=4)
        self._main_layout.addLayout(extras_layout)
        self._main_layout.addWidget(self._shift_up_button)
        self._main_layout.addWidget(self._shift_down_button)
        self._main_layout.addWidget(self._delete_button)

    def _setup_signals(self):
        """Set up the signals for the stack title frame."""

        self._shift_up_button.leftClicked.connect(self.shiftUpPressed.emit)
        self._shift_down_button.leftClicked.connect(self.shiftDownPressed.emit)
        self._delete_button.leftClicked.connect(self.deletePressed.emit)
        self._line_edit.textChanged.connect(self._on_line_edit_text_changed)
        self._line_edit.selectionChanged.connect(self._on_line_edit_selection_changed)

    # endregion

    # region === Overrides === #

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Override the `mouseDoubleClickEvent`to edit the title if
        title editing is enabled.

        Args:
            event: Qt mouse event.
        """

        if not self._title_editable:
            return

        self._line_edit.editEvent(event)

    # endregion

    # region === Callbacks === #

    def _on_line_edit_text_changed(self, text: str) -> None:
        """Callback for when the text in the line edit changes.

        This method replaces spaces with underscores.

        Args:
            text: The new text.
        """

        pos = self._line_edit.cursorPosition()
        text = text.replace(" ", "_")
        with contexts.block_signals(self._line_edit):
            self._line_edit.setText(text)
        self._line_edit.setCursorPosition(pos)

    def _on_line_edit_selection_changed(self) -> None:
        """Callback for when the selection in the line edit changes.

        This method deselects the text if title editing is disabled.
        """

        if not self._title_editable:
            self._line_edit.deselect()

    # endregion

    # region === Expand / Collapse === #

    def expand(self) -> None:
        """Update the expand/collapse button icon to the expanded icon."""

        self._expand_toggle_button.set_icon(self._expanded_icon)

    def collapse(self) -> None:
        """Update the expand/collapse button icon to the collapsed icon."""

        self._expand_toggle_button.set_icon(self._collapsed_icon)

    # endregion

    # region === Visuals === #

    def set_item_icon_color(self, color: tuple[float, float, float]) -> None:
        """Sets the color of the item icon.

        Args:
            color: The color to set as an RGB tuple.
        """

        self._item_icon_button.set_icon_color(color)

    def set_item_icon(self, icon: str | QIcon) -> None:
        """Sets the icon of the item.

        Args:
            icon: The icon to set.
        """

        self._item_icon_button.set_icon(icon, size=self._item_icon_size)

    def set_delete_button_icon(self, icon: str | QIcon) -> None:
        """Sets the icon of the delete button.

        Args:
            icon: The icon to set.
        """

        self._delete_button.set_icon(
            icon, size=self._icons_size, color_offset=self._highlight_offset
        )

    def set_delete_button_icon_color(self, color: tuple[float, float, float]) -> None:
        """Sets the color of the delete button.

        Args:
            color: The color to set as an RGB tuple.
        """

        self._delete_button.set_icon_color(color)

    # endregion


class StackItem(QFrame):
    minimized = Signal()
    maximized = Signal()
    toggleExpandRequested = Signal(bool)
    shiftUpPressed = Signal()
    shiftDownPressed = Signal()
    deletePressed = Signal()
    updateRequested = Signal()

    def __init__(
        self,
        title: str,
        collapsed: bool = False,
        collapsable: bool = True,
        icon: QIcon | None = None,
        shift_arrows_enabled: bool = True,
        delete_button_enabled: bool = True,
        title_editable: bool = True,
        item_icon_size: int = 12,
        title_upper: bool = False,
        title_frame: StackTitleFrame | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self._title = title
        self._collapsed = collapsed
        self._collapsable = collapsable
        self._icon = icon
        self._shift_arrows_enabled = shift_arrows_enabled
        self._delete_button_enabled = delete_button_enabled
        self._title_editable = title_editable
        self._item_icon_size = item_icon_size
        self._title_upper = title_upper
        # self._border_width = dpi.dpi_scale(1)
        self._border_width = 0
        self._title_frame = title_frame

        self.hide()

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

        if not collapsable:
            self._collapsed = False
            self.expand()

        self.collapse() if self._collapsed else self.expand()

    # region === Setup === #

    @property
    def contents_layout(self) -> VerticalLayout:
        """The layout that contains the contents of the stack item."""

        return self._contents_layout

    def _setup_widgets(self) -> None:
        """Set up the widgets for the stack item."""

        self._title_frame = self._title_frame or StackTitleFrame(
            title=self._title,
            icon=self._icon,
            title_editable=self._title_editable,
            item_icon_size=self._item_icon_size,
            collapsed=self._collapsed,
            shift_arrows_enabled=self._shift_arrows_enabled,
            delete_button_enabled=self._delete_button_enabled,
            upper=self._title_upper,
            parent=self,
        )

        self._widget_hider = StackHiderWidget(parent=self)
        self._widget_hider.setContentsMargins(0, 0, 0, 0)
        self._widget_hider.setHidden(self._collapsed)

    def _setup_layouts(self) -> None:
        """Set up the layouts for the stack item."""

        main_layout = VerticalLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(
            self._border_width,
            self._border_width,
            self._border_width,
            self._border_width,
        )
        self.setLayout(main_layout)

        self._contents_layout = VerticalLayout()
        self._contents_layout.setSpacing(0)
        self._contents_layout.setContentsMargins(0, 0, 0, 0)
        self._widget_hider.setLayout(self._contents_layout)

        main_layout.addWidget(self._title_frame)
        main_layout.addWidget(self._widget_hider)

    # noinspection PyUnresolvedReferences
    def _setup_signals(self):
        """Set up the signals for the stack item."""

        self._title_frame.toggleExpandRequested.connect(self.toggleExpandRequested)
        self._title_frame.shiftUpPressed.connect(self.shiftUpPressed)
        self._title_frame.shiftDownPressed.connect(self.shiftDownPressed)
        self._title_frame.deletePressed.connect(self.deletePressed)
        self._title_frame.updateRequested.connect(self.updateRequested)
        self._title_frame.expand_toggle_button.leftClicked.connect(self.toggle_contents)

    # endregion

    # region === Visibility === #

    def expand(self, emit: bool = True) -> None:
        """Expands the stack item to show its contents.

        Args:
            emit: Whether to emit the maximized signal.
        """

        self._widget_hider.setHidden(False)
        self._title_frame.expand()

        if emit:
            self.maximized.emit()

        self._collapsed = False

    def collapse(self, emit: bool = True) -> None:
        """Collapses the stack item to hide its contents.

        Args:
            emit: Whether to emit the minimized signal.
        """

        self._widget_hider.setHidden(True)
        self._title_frame.collapse()

        if emit:
            self.minimized.emit()

        self._collapsed = True

    def toggle_contents(self, emit: bool = True) -> bool:
        """Toggles the visibility of the stack item's contents.

        Args:
            emit: Whether to emit the `toggleExpandRequested` signal.

        Returns:
            The new collapsed state of the stack item.
        """

        if not self._collapsable:
            return False

        self.toggleExpandRequested.emit(not self._collapsed)

        if self._collapsed:
            self.expand(emit=emit)
            self.update_size()
            return not self._collapsed

        self.collapse(emit=emit)
        self.update_size()
        return self._collapsed

    # endregion

    # region === Visuals === #

    def set_item_icon_color(self, color: tuple[float, float, float]) -> None:
        """Sets the color of the item icon.

        Args:
            color: The color to set as an RGB tuple.
        """

        self._title_frame.set_item_icon_color(color)

    def set_delete_button_color(self, color: tuple[float, float, float]) -> None:
        """Sets the color of the delete button.

        Args:
            color: The color to set as an RGB tuple.
        """

        self._title_frame.set_delete_button_icon_color(color)

    def show_expand_indicator(self, flag: bool) -> None:
        """Shows or hides the expand/collapse indicator.

        Args:
            flag: Whether to show the indicator.
        """

        self._title_frame.expand_toggle_button.setVisible(flag)

    def set_title_text_mouse_transparent(self, flag: bool) -> None:
        """Sets whether the title text is mouse transparent.

        Args:
            flag: Whether to set the title text as mouse transparent.
        """

        self._title_frame.line_edit.setAttribute(Qt.WA_TransparentForMouseEvents, flag)

    def update_size(self) -> None:
        """Updates the size of the stack item."""

        self.updateRequested.emit()

    # endregion


class StackHiderWidget(QFrame):
    """Widget that hides/shows a stack item."""

    # Only used for stylesheet.
    pass


class LineClickEdit(QLineEdit):
    """A QLineEdit that can be edited on single or double click and
    optionally converts text to upper case.
    """

    def __init__(
        self,
        text: str,
        single: bool = False,
        double: bool = True,
        pass_through_clicks: bool = True,
        upper: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the `LineClickEdit`.

        Args:
            text: The text to set.
            single: Whether to enable single click to edit.
            double: Whether to enable double click to edit.
            pass_through_clicks: Whether to pass through clicks when not
                editing.
            upper: Whether to convert text to upper case.
            parent: The parent widget.
        """

        self._upper = upper

        super().__init__(text, parent=parent)

        self._validator = UpperCaseValidator()
        self._editing_style = self.styleSheet()
        self._default_style = "QLineEdit { border: none; }"

        if upper:
            self.setValidator(self._validator)
            self.setText(text)

        self.setReadOnly(True)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.setStyleSheet(self._default_style)
        self.setProperty("clearFocus", True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        if single:
            self.mousePressEvent = self.editEvent
        else:
            if pass_through_clicks:
                self.mousePressEvent = self.passThroughEvent

        if double:
            self.mouseDoubleClickEvent = self.editEvent
        else:
            if pass_through_clicks:
                self.mouseDoubleClickEvent = self.passThroughEvent

    # region === Overrides === #

    def setText(self, text: str) -> None:
        """Override the `setText` method to optionally convert text to uppercase.

        Args:
            text: The text to set.
        """

        if self._upper:
            text = text.upper()

        super().setText(text)

    # endregion

    # region === Events === #

    # noinspection PyPep8Naming
    def editEvent(self, event: QMouseEvent) -> None:
        """Event handler for mouse press and double-click events to enable
        editing.

        Args:
            event: The mouse event.
        """

        self.setStyleSheet(self._editing_style)
        self.selectAll()
        self.setReadOnly(False)
        self.setFocus()
        event.accept()

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def passThroughEvent(self, event: QMouseEvent) -> None:
        """Event handler for mouse press and double-click events to pass
        through the event to the parent widget.

        Args:
            event: The mouse event.
        """

        event.ignore()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Event handler for mouse press events to pass through the event
        to the parent widget.

        Args:
            event: The mouse event.
        """

        event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Event handler for mouse release events to pass through the event
        to the parent widget.

        Args:
            event: The mouse event.
        """

        event.ignore()

    def focusOutEvent(self, event: QFocusEvent) -> None:
        """Override the `focusOutEvent` to set the line edit to read-only
        when it loses focus.

        Args:
            event: The focus event.
        """

        super().focusOutEvent(event)
        self._edit_finished()

    def _edit_finished(self) -> None:
        """Handle the end of editing by setting the line edit to read-only
        and applying the appropriate style.
        """

        self.setReadOnly(True)
        self.setStyleSheet(self._default_style)
        self.deselect()

    # endregion


class UpperCaseValidator(QValidator):
    """Validator that keeps the text upper case"""

    def validate(self, string: str, pos: int) -> tuple[QValidator.State, str, int]:
        """Validate the given string and position.

        Args:
            string: The string to validate.
            pos: The position in the string.

        Returns:
            A tuple containing the validation state, the (possibly modified)
            string, and the position.
        """

        return QValidator.Acceptable, string.upper(), pos

    @staticmethod
    def create_regex_validator(
        str_value: str, parent: QObject | None = None
    ) -> QRegularExpressionValidator:
        """Create a regex validator that matches the given string.

        Args:
            str_value: The string to match.
            parent: The parent widget.

        Returns:
            A `QRegularExpressionValidator` that matches the given string.
        """

        return QRegularExpressionValidator(QRegularExpression(str_value), parent=parent)
