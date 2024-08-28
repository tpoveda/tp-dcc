from __future__ import annotations

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QWidget, QPushButton

from . import layouts, labels, lineedits


class StringEdit(QWidget):
    """
    Custom widget that creates a label, textbox (QLineEdit) and an optional button
    """

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
        """
        Initializes the StringEdit widget.

        :param label: The text for the label. Defaults to an empty string.
        :param edit_text: The initial text for the text box. Defaults to an empty string.
        :param edit_placeholder: The placeholder text for the text box. Defaults to an empty string.
        :param button_text: The text for the optional button. Defaults to None.
        :param edit_width: The width of the text box. Defaults to None.
        :param label_ratio: The ratio of the label width. Defaults to 1.
        :param button_ratio: The ratio of the button width. Defaults to 1.
        :param edit_ratio: The ratio of the text box width. Defaults to 5.
        :param tooltip: The tooltip text for the widget. Defaults to an empty string.
        :param orientation: The orientation of the widget (horizontal or vertical). Defaults to Qt.Horizontal.
        :param enable_menu: If True, enables a context menu for the text box. Defaults to False.
        :param parent: The parent widget. Defaults to None.
        """

        super().__init__(parent)

        self._label = label
        self._button_text = button_text
        self._enable_menu = enable_menu
        self._button: QPushButton | None = None

        self._layout = (
            layouts.HorizontalLayout
            if orientation == Qt.Horizontal
            else layouts.VerticalLayout
        )(parent=self)

        self._edit = self._setup_edit_line(
            edit_text=edit_text,
            placeholder=edit_placeholder,
            tooltip=tooltip,
            edit_width=edit_width,
        )
        if label:
            self._label = labels.BaseLabel(text=label, tooltip=tooltip, parent=self)
            self._layout.addWidget(self._label, label_ratio)
        self._layout.addWidget(self._edit, edit_ratio)

        if self._button_text:
            self._button = QPushButton(button_text, parent)
            self._layout.addWidget(self._button, button_ratio)

        self._setup_signals()

    @property
    def label(self) -> labels.BaseLabel:
        """
        Gets the label associated with the widget.

        This property returns the label associated with the StringEdit widget.

        :return: The label associated with the widget.
        """

        return self._label

    # noinspection SpellCheckingInspection
    @property
    def edit(self) -> lineedits.BaseLineEdit:
        """
        Gets the text box (QLineEdit) associated with the widget.

        This property returns the text box (QLineEdit) associated with the StringEdit widget.

        :return: The text box (QLineEdit) associated with the widget.
        :rtype: lineedits.BaseLineEdit
        """

        return self._edit

    # noinspection PyPep8Naming
    @property
    def editingFinished(self) -> Signal:
        """
        Gets the editingFinished signal of the text box.

        This property returns the editingFinished signal of the text box associated with the StringEdit widget.

        :return: The editingFinished signal of the text box.
        """

        return self._edit.editingFinished

    # noinspection PyPep8Naming
    @property
    def textChanged(self) -> Signal:
        """
        Gets the textChanged signal of the text box.

        This property returns the textChanged signal of the text box associated with the StringEdit widget.

        :return: The textChanged signal of the text box.
        """

        return self._edit.textChanged

    # noinspection PyPep8Naming
    @property
    def textModified(self) -> Signal:
        """
        Gets the textModified signal of the text box.

        This property returns the textModified signal of the text box associated with the StringEdit widget.

        :return: The textModified signal of the text box.
        """

        return self._edit.textModified

    # noinspection PyPep8Naming
    @property
    def returnPressed(self) -> Signal:
        """
        Gets the returnPressed signal of the text box.

        This property returns the returnPressed signal of the text box associated with the StringEdit widget.

        :return: The returnPressed signal of the text box.
        """

        return self._edit.returnPressed

    # noinspection PyPep8Naming
    @property
    def mousePressed(self) -> Signal:
        """
        Gets the mousePressed signal of the text box.

        This property returns the mousePressed signal of the text box associated with the StringEdit widget.

        :return: The mousePressed signal of the text box.
        """

        return self._edit.mousePressed

    # noinspection PyPep8Naming
    @property
    def mouseMoved(self) -> Signal:
        """
        Gets the mouseMoved signal of the text box.

        This property returns the mouseMoved signal of the text box associated with the StringEdit widget.

        :return: The mouseMoved signal of the text box.
        """

        return self._edit.mouseMoved

    # noinspection PyPep8Naming
    @property
    def mouseReleased(self) -> Signal:
        """
        Gets the mouseMoved signal of the text box.

        This property returns the mouseReleased signal of the text box associated with the StringEdit widget.

        :return: The mouseReleased signal of the text box.
        """

        return self._edit.mouseReleased

    def text(self) -> str:
        """
        Returns text from line edit.

        :return: line edit text.
        """

        return self._edit.text()

    def set_text(self, text: str):
        """
        Sets line edit text.

        :param text: new text.
        """

        self._edit.setText(text)

    def select_all(self):
        """
        Selects all text in the line edit.
        """

        self._edit.selectAll()

    def set_placeholder_text(self, text: str):
        """
        Sets line edit placeholder text.

        :param text: placeholder text.
        """

        self._edit.setPlaceholderText(text)

    # noinspection SpellCheckingInspection
    def _setup_edit_line(
        self, edit_text: str, placeholder: str, tooltip: str, edit_width: int
    ) -> lineedits.BaseLineEdit:
        """
        Sets up the text box (QLineEdit) for the widget.

        This method initializes and configures the text box (QLineEdit) with the specified parameters.

        :param edit_text: The initial text for the text box.
        :param placeholder: The placeholder text for the text box.
        :param tooltip: The tooltip text for the text box.
        :param edit_width: The width of the text box.
        :return: The configured text box (QLineEdit).
        :rtype: lineedits.BaseLineEdit
        """

        return lineedits.BaseLineEdit(
            text=edit_text,
            placeholder=placeholder,
            tooltip=tooltip,
            edit_width=edit_width,
            parent=self,
        )

    def _setup_signals(self):
        """
        Internal function that setup widget signals.
        """

        if self._button:
            self._button.clicked.connect(self.buttonClicked.emit)


class IntEdit(StringEdit):
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
        """
        Initializes the StringEdit widget.

        :param label: The text for the label. Defaults to an empty string.
        :param edit_text: The initial text for the text box. Defaults to an empty string.
        :param edit_placeholder: The placeholder text for the text box. Defaults to an empty string.
        :param button_text: The text for the optional button. Defaults to None.
        :param edit_width: The width of the text box. Defaults to None.
        :param label_ratio: The ratio of the label width. Defaults to 1.
        :param button_ratio: The ratio of the button width. Defaults to 1.
        :param edit_ratio: The ratio of the text box width. Defaults to 5.
        :param tooltip: The tooltip text for the widget. Defaults to an empty string.
        :param orientation: The orientation of the widget (horizontal or vertical). Defaults to Qt.Horizontal.
        :param enable_menu: If True, enables a context menu for the text box. Defaults to False.
        :param parent: The parent widget. Defaults to None.
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
        line_edit: lineedits.IntLineEdit = self._edit

    # noinspection SpellCheckingInspection
    def _setup_edit_line(
        self, edit_text: str, placeholder: str, tooltip: str, edit_width: int
    ) -> lineedits.IntLineEdit:
        """
        Sets up the text box (QLineEdit) for the widget.

        This method initializes and configures the text box (QLineEdit) with the specified parameters.

        :param edit_text: The initial text for the text box.
        :param placeholder: The placeholder text for the text box.
        :param tooltip: The tooltip text for the text box.
        :param edit_width: The width of the text box.
        :return: The configured text box (QLineEdit).
        :rtype: lineedits.IntLineEdit
        """

        return lineedits.IntLineEdit(
            text=edit_text,
            placeholder=placeholder,
            tooltip=tooltip,
            edit_width=edit_width,
            parent=self,
        )
