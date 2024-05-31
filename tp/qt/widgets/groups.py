from __future__ import annotations

from typing import Sequence

from ...externals.Qt.QtCore import Qt, Signal
from ...externals.Qt.QtWidgets import QWidget, QButtonGroup, QRadioButton
from .. import uiconsts
from . import layouts


class RadioButtonGroup(QWidget):
    """
    Custom widget that creates a horizontal or vertical group of radio buttons.
    """

    toggled = Signal(int)

    def __init__(
            self, radio_names: Sequence[str] | None = None, tooltips: Sequence[str] | None = None,
            default: int | None = 0, vertical: bool = False, margins: tuple[int, int, int, int] =
            (uiconsts.REGULAR_PADDING, uiconsts.REGULAR_PADDING, uiconsts.REGULAR_PADDING, 0),
            spacing: int = uiconsts.SMALL_SPACING, alignment: Qt.AlignmentFlag | None = None,
            parent: QWidget | None = None):
        """
        Constructor.

        :param radio_names: optional list of radio button names.
        :param tooltips: optional list of tooltips for each one of the radio buttons.
        :param default: optional default button to be checked.
        :param vertical: whether to create buttons horizontally or vertically.
        :param margins: optional margins used for buttons layout.
        :param spacing: optional spacing used for buttons layout.
        :param alignment: optional align for buttons layout.
        """

        super().__init__(parent=parent)

        self._radio_buttons: list[QRadioButton] = []
        self._group = QButtonGroup(parent=self)
        if vertical:
            radio_layout = layouts.vertical_layout(margins=margins, spacing=spacing, alignment=alignment)
        else:
            radio_layout = layouts.horizontal_layout(margins=margins, spacing=spacing, alignment=alignment)
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

        self._group.buttonClicked.connect(lambda: self.toggled.emit(self.checked_index()))

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
