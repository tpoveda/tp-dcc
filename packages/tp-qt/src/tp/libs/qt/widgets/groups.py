from __future__ import annotations

from typing import Sequence
from abc import abstractmethod

from Qt.QtCore import Qt, Property, Signal
from Qt.QtWidgets import (
    QSizePolicy,
    QWidget,
    QButtonGroup,
    QBoxLayout,
    QPushButton,
    QRadioButton,
)
from Qt.QtGui import QIcon

from . import layouts, buttons
from .. import uiconsts, dpi
from ...resources.style import theme


class BaseButtonGroup(QWidget):
    """
    Base abstract class used to define group of buttons.
    """

    def __init__(
        self, orientation: Qt.Orientation = Qt.Horizontal, parent: QWidget | None = None
    ):
        super().__init__(parent=parent)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self._main_layout = QBoxLayout(
            QBoxLayout.LeftToRight
            if orientation == Qt.Horizontal
            else QBoxLayout.TopToBottom
        )
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._main_layout)

        self._button_group = QButtonGroup(parent=self)
        self._orientation = "horizontal" if orientation == Qt.Horizontal else "vertical"

    @property
    def button_group(self) -> QButtonGroup:
        """
        Getter method that returns the button group instance.

        :return: button group.
        """

        return self._button_group

    @abstractmethod
    def create_button(self, button_data: dict) -> QPushButton:
        """
        Creates button instance within this group.
        Must be overridden by derived classes.

        :param button_data: button creation keyword arguments.
        :return: newly created button instance.
        """

        raise NotImplementedError()

    def set_spacing(self, spacing: int):
        """
        Sets main buttons group layout spacing between widgets.

        :param spacing: main layout spacing.
        """

        self._main_layout.setSpacing(spacing)

    def add_button(self, data: dict, index: int | None = None) -> QPushButton:
        """
        Adds new button into the group based on given button creation data.

        :param data: dictionary that defines the button to create.
        :param index: optional index of the button within the group.
        :return: newly created button.
        """

        if isinstance(data, str):
            data = {"text": data}
        elif isinstance(data, QIcon):
            data = {"icon": data}
        button = self.create_button(data)
        button.setProperty("combine", self._orientation)
        if data.get("text"):
            button.setProperty("text", data.get("text"))
        if data.get("icon"):
            button.setProperty("icon", data.get("icon"))
        if data.get("data"):
            button.setProperty("data", data.get("data"))
        if data.get("checked"):
            button.setProperty("checked", data.get("checked"))
        if data.get("shortcut"):
            button.setProperty("shortcut", data.get("shortcut"))
        if data.get("tooltip"):
            button.setProperty("toolTip", data.get("tooltip"))
        if data.get("checkable"):
            button.setProperty("checkable", data.get("checkable"))
        if data.get("clicked"):
            # noinspection PyTypeChecker
            button.clicked.connect(data["clicked"])
        if data.get("toggled"):
            # noinspection PyTypeChecker
            button.toggled.connect(data["toggled"])
        if index is None:
            self._button_group.addButton(button)
        else:
            self._button_group.addButton(button, index)
        self._main_layout.insertWidget(self._main_layout.count(), button)

        return button

    def set_buttons(self, buttons_data: list[dict]):
        """
        Removes all current group buttons and creates new ones based on the list of button creation data.

        :param buttons_data: list of dictionaries defining the buttons to create.
        """

        for button in self._button_group.buttons():
            self._button_group.removeButton(button)
            self._main_layout.removeWidget(button)
            button.setVisible(False)

        for index, data_dict in enumerate(buttons_data):
            button = self.add_button(data_dict, index)
            if index == 0:
                button.setProperty("position", "left")
            elif index == len(buttons_data) - 1:
                button.setProperty("position", "right")
            else:
                button.setProperty("position", "center")


class PushButtonGroup(BaseButtonGroup):
    """Class that allows to create group of push buttons."""

    def __init__(
        self, orientation: Qt.Orientation = Qt.Horizontal, parent: QWidget | None = None
    ):
        super().__init__(orientation=orientation, parent=parent)

        self._type = buttons.BaseButton.Type.Primary.value
        self._size = theme.instance().sizes.default

        self._button_group.setExclusive(False)
        self.set_spacing(1)

    def create_button(self, button_data: dict) -> QPushButton:
        button = buttons.BaseButton()
        button.type = button_data.get("type", self._type)
        button.set_size(button_data.get("size", self._size))

        return button


class BaseRadioButtonGroup(BaseButtonGroup):
    """Class that allows to create group of radio buttons."""

    checkedChanged = Signal(int)

    def __init__(
        self, orientation: Qt.Orientation = Qt.Horizontal, parent: QWidget | None = None
    ):
        super().__init__(orientation=orientation, parent=parent)

        scale_x, _ = dpi.scale_factor()
        self.set_spacing(int(15 * scale_x))
        self._button_group.setExclusive(True)
        self._button_group.buttonClicked.connect(self.checkedChanged.emit)

    def create_button(self, data_dict: dict) -> QRadioButton:
        """Overrides `create_button` to create a radio button instance within this group.

        Args:
            data_dict: button creation keyword arguments.

        Returns:
            newly created button instance.
        """

        return QRadioButton(parent=self)

    def _set_checked(self, value: int):
        """Internal function that sets the checked button index.

        Args:
            value: checked button index.
        """

        if value == self._get_checked():
            return
        button = self._button_group.button(value)
        if button:
            button.setChecked(True)
            self.checkedChanged.emit(value)

    def _get_checked(self) -> int:
        """Internal function that returns the checked button index.

        Returns:
            int: checked button index.
        """

        return self._button_group.checkedId()

    checked = Property(int, _get_checked, _set_checked, notify=checkedChanged)


class RadioButtonGroup(QWidget):
    """
    Custom widget that creates a horizontal or vertical group of radio buttons.
    """

    toggled = Signal(int)

    def __init__(
        self,
        radio_names: Sequence[str] | None = None,
        tooltips: Sequence[str] | None = None,
        default: int | None = 0,
        vertical: bool = False,
        margins: tuple[int, int, int, int] = (
            uiconsts.REGULAR_PADDING,
            uiconsts.REGULAR_PADDING,
            uiconsts.REGULAR_PADDING,
            0,
        ),
        spacing: int = uiconsts.SMALL_SPACING,
        alignment: Qt.AlignmentFlag | None = None,
        parent: QWidget | None = None,
    ):
        """
        Constructor.

        :param radio_names: optional list of radio button names.
        :param tooltips: optional list of tooltips for each one of the radio buttons.
        :param default: optional default button to be checked.
        :param vertical: whether to create buttons horizontally or vertically.
        :param margins: optional margins used for buttons layout.
        :param spacing: optional spacing used for buttons layout.
        :param alignment: optional align for buttons layout.
        :param parent: optional parent widget.
        """

        super().__init__(parent=parent)

        self._radio_buttons: list[QRadioButton] = []
        self._group = QButtonGroup(parent=self)
        if vertical:
            radio_layout = layouts.VerticalLayout()
        else:
            radio_layout = layouts.HorizontalLayout()

        radio_layout.setContentsMargins(*margins)
        radio_layout.setSpacing(spacing)
        if alignment is not None:
            radio_layout.setAlignment(alignment)
        self.setLayout(radio_layout)

        radio_names = radio_names or []
        tooltips = tooltips or []
        for i, radio_name in enumerate(radio_names):
            new_radio_button = QRadioButton(radio_name, parent=self)
            try:
                new_radio_button.setToolTip(tooltips[i])
            except IndexError:
                pass
            self._group.addButton(new_radio_button)
            radio_layout.addWidget(new_radio_button)
            self._radio_buttons.append(new_radio_button)

        if default is not None and default < len(self._radio_buttons):
            self._radio_buttons[default].setChecked(True)

        if alignment is not None:
            for button in self._radio_buttons:
                radio_layout.setAlignment(button, alignment)

        self._group.buttonClicked.connect(
            lambda: self.toggled.emit(self.checked_index())
        )

    def checked(self) -> QRadioButton | None:
        """
        Returns the radio button that is currently checked.

        :return: checked radio button.
        """

        checked_radio_button: QRadioButton | None = None
        for radio_button in self._radio_buttons:
            if not radio_button.isChecked():
                continue
            checked_radio_button = radio_button
            break

        return checked_radio_button

    def checked_index(self) -> int | None:
        """
        Returns the index of the radio button that is currently checked.

        :return: checked radio button index.
        """

        checked_radio_button_index: int | None = None
        for i, radio_button in enumerate(self._radio_buttons):
            if not radio_button.isChecked():
                continue
            checked_radio_button_index = i
            break

        return checked_radio_button_index

    def set_checked(self, index: int):
        """
        Checks the radio button of give index.

        :param index: index of the radio button to check.
        """

        self._radio_buttons[index].setChecked(True)
