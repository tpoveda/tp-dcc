from __future__ import annotations

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QWidget, QPushButton
from Qt.QtGui import QIntValidator, QDoubleValidator

from .. import uiconsts
from .labels import BaseLabel
from .lineedits import BaseLineEdit, IntLineEdit, FloatLineEdit
from .layouts import HorizontalLayout, VerticalLayout


class StringEdit(QWidget):
    """Custom widget that creates a label, textbox (QLineEdit) and an optional button."""

    buttonClicked = Signal()

    def __init__(
        self,
        label: str = "",
        edit_text: str = "",
        edit_placeholder: str = "",
        button_text: str | None = None,
        edit_width: int | None = None,
        label_ratio: int = 1,
        button_ratio: int = 1,
        edit_ratio: int = 5,
        tooltip: str = "",
        orientation: Qt.Orientation = Qt.Horizontal,
        enable_menu: bool = False,
        parent: QWidget | None = None,
    ):
        """Initializes the StringEdit widget.

        Args:
            label: The text for the label. Defaults to an empty string.
            edit_text: The initial text for the text box. Defaults to an empty
                string.
            edit_placeholder: The placeholder text for the text box. Defaults to
                an empty string.
            button_text: The text for the optional button. Defaults to None.
            edit_width: The width of the text box. Defaults to None.
            label_ratio: The ratio of the label width. Defaults to 1.
            button_ratio: The ratio of the button width. Defaults to 1.
            edit_ratio: The ratio of the text box width. Defaults to 5.
            tooltip: The tooltip text for the widget. Defaults to an empty
                string.
            orientation: The orientation of the widget (horizontal or vertical).
                Defaults to Qt.Horizontal.
            enable_menu: If True, enables a context menu for the text box.
                Defaults to False.
            parent: The parent widget. Defaults to None.
        """

        super().__init__(parent)

        self._enable_menu = enable_menu
        self._button: QPushButton | None = None

        self._layout = (
            HorizontalLayout if orientation == Qt.Horizontal else VerticalLayout
        )()
        self._layout.setSpacing(uiconsts.DEFAULT_SPACING)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        self._edit = self._setup_edit_line(
            edit_text=edit_text,
            placeholder=edit_placeholder,
            tooltip=tooltip,
            edit_width=edit_width,
            enable_menu=enable_menu,
        )

        if label:
            self._label = BaseLabel(text=label, tooltip=tooltip, parent=self)
            self._layout.addWidget(self._label, label_ratio)
        self._layout.addWidget(self._edit, edit_ratio)

        if button_text:
            self._button = QPushButton(button_text, parent)
            self._layout.addWidget(self._button, button_ratio)

        self._setup_signals()

    @property
    def label(self) -> BaseLabel:
        """Gets the label associated with the widget.

        This property returns the label associated with the StringEdit widget.

        Returns:
            The label associated with the widget.
        """

        return self._label

    # noinspection SpellCheckingInspection
    @property
    def edit(self) -> BaseLineEdit:
        """Gets the text box (QLineEdit) associated with the widget.

        This property returns the text box (QLineEdit) associated with the
        StringEdit widget.

        Returns:
            The text box (QLineEdit) associated with the widget.
        """

        return self._edit

    # noinspection PyPep8Naming
    @property
    def editingFinished(self) -> Signal:
        """Gets the editingFinished signal of the text box.

        This property returns the editingFinished signal of the text box
        associated with the StringEdit widget.

        Returns:
            The editingFinished signal of the text box.
        """

        return self._edit.editingFinished

    # noinspection PyPep8Naming
    @property
    def textChanged(self) -> Signal:
        """Gets the textChanged signal of the text box.

        This property returns the textChanged signal of the text box associated
        with the StringEdit widget.

        Returns:
            The textChanged signal of the text box.
        """

        return self._edit.textChanged

    # noinspection PyPep8Naming
    @property
    def textModified(self) -> Signal:
        """Gets the textModified signal of the text box.

        This property returns the textModified signal of the text box associated
        with the StringEdit widget.

        Returns:
            The textModified signal of the text box.
        """

        return self._edit.textModified

    # noinspection PyPep8Naming
    @property
    def returnPressed(self) -> Signal:
        """Gets the returnPressed signal of the text box.

        This property returns the returnPressed signal of the text box associated
        with the StringEdit widget.

        Returns:
            The returnPressed signal of the text box.
        """

        return self._edit.returnPressed

    # noinspection PyPep8Naming
    @property
    def mousePressed(self) -> Signal:
        """Gets the mousePressed signal of the text box.

        This property returns the mousePressed signal of the text box associated
        with the StringEdit widget.

        Returns:
            The mousePressed signal of the text box.
        """

        return self._edit.mousePressed

    # noinspection PyPep8Naming
    @property
    def mouseMoved(self) -> Signal:
        """Gets the mouseMoved signal of the text box.

        This property returns the mouseMoved signal of the text box associated
        with the StringEdit widget.

        Returns:
            The mouseMoved signal of the text box.
        """

        return self._edit.mouseMoved

    # noinspection PyPep8Naming
    @property
    def mouseReleased(self) -> Signal:
        """Gets the mouseMoved signal of the text box.

        This property returns the mouseReleased signal of the text box associated
        with the StringEdit widget.

        Returns:
            The mouseReleased signal of the text box.
        """

        return self._edit.mouseReleased

    def text(self) -> str:
        """Returns text from line edit.

        Returns:
            Line edit text.
        """

        return self._edit.text()

    def set_text(self, text: str):
        """Sets line edit text.

        Args:
            text: New text.
        """

        self._edit.setText(text)

    def select_all(self):
        """Selects all text in the line edit."""

        self._edit.selectAll()

    def set_placeholder_text(self, text: str):
        """Sets line edit placeholder text.

        Args:
            text: Placeholder text.
        """

        self._edit.setPlaceholderText(text)

    # noinspection SpellCheckingInspection
    def _setup_edit_line(
        self,
        edit_text: str,
        placeholder: str,
        tooltip: str,
        edit_width: int,
        enable_menu: bool,
    ) -> BaseLineEdit:
        """Sets up the text box (QLineEdit) for the widget.

        This method initializes and configures the text box (QLineEdit) with the
        specified parameters.

        Args:
            edit_text: The initial text for the text box.
            placeholder: The placeholder text for the text box.
            tooltip: The tooltip text for the text box.
            edit_width: The width of the text box.
            enable_menu: If True, enables a context menu for the text box.

        Returns:
            The configured text box (QLineEdit).
        """

        return BaseLineEdit(
            text=edit_text,
            placeholder=placeholder,
            tooltip=tooltip,
            edit_width=edit_width,
            enable_menu=enable_menu,
            parent=self,
        )

    def _setup_signals(self):
        """Internal function that setup widget signals."""

        if self._button:
            self._button.clicked.connect(self.buttonClicked.emit)


class IntEdit(StringEdit):
    """Custom widget that creates a label, textbox (QLineEdit) and an optional button."""

    def __init__(
        self,
        label: str = "",
        edit_text: str = "",
        edit_placeholder: str = "",
        button_text: str | None = None,
        edit_width: int | None = None,
        label_ratio: int = 1,
        button_ratio: int = 1,
        edit_ratio: int = 1,
        tooltip: str = "",
        orientation: Qt.Orientation = Qt.Horizontal,
        enable_menu: bool = True,
        slide_distance: float = 0.05,
        small_slide_distance: float = 0.01,
        large_slide_distance: float = 1.0,
        scroll_distance: float = 1.0,
        update_on_slide_tick: bool = True,
        parent: QWidget | None = None,
    ):
        """Initializes the IntEdit widget.

        Args:
            label: The text for the label. Defaults to an empty string.
            edit_text: The initial text for the text box. Defaults to an empty
                string.
            edit_placeholder: The placeholder text for the text box. Defaults to
                an empty string.
            button_text: The text for the optional button. Defaults to None.
            edit_width: The width of the text box. Defaults to None.
            label_ratio: The ratio of the label width. Defaults to 1.
            button_ratio: The ratio of the button width. Defaults to 1.
            edit_ratio: The ratio of the text box width. Defaults to 1.
            tooltip: The tooltip text for the widget. Defaults to an empty
                string.
            orientation: The orientation of the widget (horizontal or vertical).
                Defaults to Qt.Horizontal.
            enable_menu: If True, enables a context menu for the text box.
                Defaults to True.
            slide_distance: The distance to slide when using the arrow keys.
                Defaults to 0.05.
            small_slide_distance: The distance to slide when using the arrow
                keys with the Shift key. Defaults to 0.01.
            large_slide_distance: The distance to slide when using the arrow
                keys with the Ctrl key. Defaults to 1.0.
            scroll_distance: The distance to slide when using the mouse wheel.
                Defaults to 1.0.
            update_on_slide_tick: If True, updates the value on each slide tick.
                Defaults to True.
            parent: The parent widget. Defaults to None.
        """

        super().__init__(
            label=label,
            edit_text=edit_text,
            edit_placeholder=edit_placeholder,
            button_text=button_text,
            edit_width=edit_width,
            label_ratio=label_ratio,
            button_ratio=button_ratio,
            edit_ratio=edit_ratio,
            tooltip=tooltip,
            orientation=orientation,
            enable_menu=enable_menu,
            parent=parent,
        )

        # noinspection PyTypeChecker
        line_edit: IntLineEdit = self._edit

        mouse_slider = line_edit.mouse_slider
        mouse_slider.slide_distance = slide_distance
        mouse_slider.small_slide_distance = small_slide_distance
        mouse_slider.large_slide_distance = large_slide_distance
        mouse_slider.scroll_distance = scroll_distance
        mouse_slider.update_on_tick = update_on_slide_tick

    @property
    def sliderStarted(self) -> Signal:
        """Gets the sliderStarted signal of the text box.

        This property returns the sliderStarted signal of the text box associated
        with the IntEdit widget.

        Returns:
            The sliderStarted signal of the text box.
        """

        # noinspection PyTypeChecker
        line_edit: IntLineEdit = self._edit

        return line_edit.mouse_slider.sliderStarted

    @property
    def sliderChanged(self) -> Signal:
        """Gets the sliderChanged signal of the text box.

        This property returns the sliderChanged signal of the text box associated
        with the IntEdit widget.

        Returns:
            The sliderChanged signal of the text box.
        """

        # noinspection PyTypeChecker
        line_edit: IntLineEdit = self._edit

        return line_edit.mouse_slider.sliderChanged

    @property
    def sliderFinished(self) -> Signal:
        """Gets the sliderFinished signal of the text box.

        This property returns the sliderFinished signal of the text box associated
        with the IntEdit widget.

        Returns:
            The sliderFinished signal of the text box.
        """

        # noinspection PyTypeChecker
        line_edit: IntLineEdit = self._edit

        return line_edit.mouse_slider.sliderFinished

    # noinspection SpellCheckingInspection
    def _setup_edit_line(
        self,
        edit_text: str,
        placeholder: str,
        tooltip: str,
        edit_width: int,
        enable_menu: bool,
    ) -> IntLineEdit:
        """Sets up the text box (QLineEdit) for the widget.

        This method initializes and configures the text box (QLineEdit) with the
        specified parameters.

        Args:
            edit_text: The initial text for the text box.
            placeholder: The placeholder text for the text box.
            tooltip: The tooltip text for the text box.
            edit_width: The width of the text box.
            enable_menu: If True, enables a context menu for the text box.

        Returns:
            The configured text box (QLineEdit).
        """

        return IntLineEdit(
            text=edit_text,
            placeholder=placeholder,
            tooltip=tooltip,
            edit_width=edit_width,
            enable_menu=enable_menu,
            parent=self,
        )

    def set_minimum_value(self, value: int):
        """Sets the minimum value for the IntEdit widget.

        Args:
            value: The minimum value to set.
        """

        # noinspection PyTypeChecker
        validator: QDoubleValidator = self._edit.validator()
        validator.setBottom(value)

    def set_maximum_value(self, value: int):
        """Sets the maximum value for the IntEdit widget.

        Args:
            value: The maximum value to set.
        """

        # noinspection PyTypeChecker
        validator: QDoubleValidator = self._edit.validator()
        validator.setTop(value)


class FloatEdit(StringEdit):
    """Custom widget that creates a label, textbox (QLineEdit) and an optional button."""

    def __init__(
        self,
        label: str = "",
        edit_text: str = "",
        edit_placeholder: str = "",
        button_text: str | None = None,
        edit_width: int | None = None,
        label_ratio: int = 1,
        button_ratio: int = 1,
        edit_ratio: int = 1,
        tooltip: str = "",
        orientation: Qt.Orientation = Qt.Horizontal,
        enable_menu: bool = True,
        rounding: int = 3,
        slide_distance: float = 0.01,
        small_slide_distance: float = 0.001,
        large_slide_distance: float = 0.1,
        scroll_distance: float = 1.0,
        update_on_slide_tick: bool = True,
        parent: QWidget | None = None,
    ):
        """Initializes the FloatEdit widget.

        Args:
            label: The text for the label. Defaults to an empty string.
            edit_text: The initial text for the text box. Defaults to an empty
                string.
            edit_placeholder: The placeholder text for the text box. Defaults to
                an empty string.
            button_text: The text for the optional button. Defaults to None.
            edit_width: The width of the text box. Defaults to None.
            label_ratio: The ratio of the label width. Defaults to 1.
            button_ratio: The ratio of the button width. Defaults to 1.
            edit_ratio: The ratio of the text box width. Defaults to 1.
            tooltip: The tooltip text for the widget. Defaults to an empty
                string.
            orientation: The orientation of the widget (horizontal or vertical).
                Defaults to Qt.Horizontal.
            enable_menu: If True, enables a context menu for the text box.
                Defaults to True.
            rounding: The number of decimal places to round the float value.
                Defaults to 3.
            slide_distance: The distance to slide when using the arrow keys.
                Defaults to 0.01.
            small_slide_distance: The distance to slide when using the arrow
                keys with the Shift key. Defaults to 0.001.
            large_slide_distance: The distance to slide when using the arrow
                keys with the Ctrl key. Defaults to 0.1.
            scroll_distance: The distance to slide when using the mouse wheel.
                Defaults to 1.0.
            update_on_slide_tick: If True, updates the value on each slide tick.
                Defaults to True.
            parent: The parent widget. Defaults to None.
        """

        self._rounding = rounding

        super().__init__(
            label=label,
            edit_text=edit_text,
            edit_placeholder=edit_placeholder,
            button_text=button_text,
            edit_width=edit_width,
            label_ratio=label_ratio,
            button_ratio=button_ratio,
            edit_ratio=edit_ratio,
            tooltip=tooltip,
            orientation=orientation,
            enable_menu=enable_menu,
            parent=parent,
        )

        # noinspection PyTypeChecker
        line_edit: IntLineEdit = self._edit

        mouse_slider = line_edit.mouse_slider
        mouse_slider.slide_distance = slide_distance
        mouse_slider.small_slide_distance = small_slide_distance
        mouse_slider.large_slide_distance = large_slide_distance
        mouse_slider.scroll_distance = scroll_distance
        mouse_slider.update_on_tick = update_on_slide_tick

    @property
    def sliderStarted(self) -> Signal:
        """Gets the sliderStarted signal of the text box.

        This property returns the sliderStarted signal of the text box associated
        with the IntEdit widget.

        Returns:
            The sliderStarted signal of the text box.
        """

        # noinspection PyTypeChecker
        line_edit: IntLineEdit = self._edit

        return line_edit.mouse_slider.sliderStarted

    @property
    def sliderChanged(self) -> Signal:
        """Gets the sliderChanged signal of the text box.

        This property returns the sliderChanged signal of the text box associated
        with the IntEdit widget.

        Returns:
            The sliderChanged signal of the text box.
        """

        # noinspection PyTypeChecker
        line_edit: IntLineEdit = self._edit

        return line_edit.mouse_slider.sliderChanged

    @property
    def sliderFinished(self) -> Signal:
        """Gets the sliderFinished signal of the text box.

        This property returns the sliderFinished signal of the text box associated
        with the IntEdit widget.

        Returns:
            The sliderFinished signal of the text box.
        """

        # noinspection PyTypeChecker
        line_edit: IntLineEdit = self._edit

        return line_edit.mouse_slider.sliderFinished

    # noinspection SpellCheckingInspection
    def _setup_edit_line(
        self,
        edit_text: str,
        placeholder: str,
        tooltip: str,
        edit_width: int,
        enable_menu: bool,
    ) -> FloatLineEdit:
        """Sets up the text box (QLineEdit) for the widget.

        This method initializes and configures the text box (QLineEdit) with the
        specified parameters.

        Args:
            edit_text: The initial text for the text box.
            placeholder: The placeholder text for the text box.
            tooltip: The tooltip text for the text box.
            edit_width: The width of the text box.
            enable_menu: If True, enables a context menu for the text box.

        Returns:
            The configured text box (QLineEdit).
        """

        return FloatLineEdit(
            text=edit_text,
            placeholder=placeholder,
            tooltip=tooltip,
            edit_width=edit_width,
            enable_menu=enable_menu,
            rounding=self._rounding,
            parent=self,
        )

    def set_minimum_value(self, value: int):
        """Sets the minimum value for the IntEdit widget.

        Args:
            value: The minimum value to set.
        """

        # noinspection PyTypeChecker
        validator: QIntValidator = self._edit.validator()
        validator.setBottom(value)

    def set_maximum_value(self, value: int):
        """Sets the maximum value for the IntEdit widget.

        Args:
            value: The maximum value to set.
        """

        # noinspection PyTypeChecker
        validator: QIntValidator = self._edit.validator()
        validator.setTop(value)
