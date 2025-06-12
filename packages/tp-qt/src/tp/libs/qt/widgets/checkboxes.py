from __future__ import annotations

from typing import Any
from functools import partial

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QWidget, QCheckBox, QLabel, QHBoxLayout
from Qt.QtGui import QMouseEvent

from .. import contexts
from . import layouts, menus


@menus.mixin
class BaseCheckBoxWidget(QWidget):
    """
    Custom widget class that adds the ability for a middle/right/click menu to be added to the QCheckbox.
    """

    leftClicked = Signal()
    middleClicked = Signal()
    rightClicked = Signal()
    toggled = Signal(bool)
    stateChanged = Signal(object)

    def __init__(
        self,
        text: str = "",
        checked: bool = False,
        tooltip: str = "",
        enable_menu: bool = True,
        menu_vertical_offset: int = 20,
        right: bool = False,
        label_ratio: int = 0,
        box_ratio: int = 0,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self._right = right
        self._label_ratio = label_ratio
        self._box_ratio = box_ratio
        self._checkbox = QCheckBox(text or "", parent=self)
        self._label: QLabel | None = None
        self._main_layout: QHBoxLayout | None = None

        if tooltip:
            self.setToolTip(tooltip)

        self._setup_ui()
        self._setup_signals()
        self.setChecked(checked)
        self.set_text(text)

        if enable_menu:
            self._setup_menu_class(menu_vertical_offset=menu_vertical_offset)
            self.leftClicked.connect(partial(self.show_context_menu, Qt.LeftButton))
            self.middleClicked.connect(partial(self.show_context_menu, Qt.MiddleButton))
            self.rightClicked.connect(partial(self.show_context_menu, Qt.RightButton))

    def __getattr__(self, item: str) -> Any:
        if self._checkbox and hasattr(self._checkbox, item):
            return getattr(self._checkbox, item)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        for mouse_button, menu_instance in self._click_menu.items():
            if menu_instance and event.button() == mouse_button:
                if mouse_button == Qt.LeftButton:
                    return self.leftClicked.emit()
                elif mouse_button == Qt.MiddleButton:
                    return self.middleClicked.emit()
                elif mouse_button == Qt.RightButton:
                    return self.rightClicked.emit()

        super().mousePressEvent(event)

    def text(self) -> str:
        """
        Returns checkbox text.

        :return: checkbox text.
        :rtype: str
        """

        return self._label.text() if self._label else self._checkbox.text()

    def set_text(self, value: str):
        """
        Sets checkbox text.

        :param str value: checkbox text to set.
        """

        if self._label:
            self._label.setText(value)

        self._checkbox.setText("" if self._right else value)

    def set_checked_quiet(self, flag: bool):
        """
        Sets the checkbox check status without emitting any signal.

        :param bool flag: whether checkbox is checked.
        """

        with contexts.block_signals(self._checkbox):
            self._checkbox.setChecked(flag)

    def _setup_ui(self):
        """
        Internal function that setup widgets.
        """

        self._main_layout = layouts.HorizontalLayout()
        self.setLayout(self._main_layout)

        if self._right:
            self._label = QLabel(parent=self)
            self._main_layout.addWidget(self._label, self._label_ratio)
        self._main_layout.addWidget(self._checkbox, self._box_ratio)

    def _setup_signals(self):
        """
        Internal function that setup signal connections.
        """

        self._checkbox.stateChanged.connect(self.stateChanged.emit)
        self._checkbox.toggled.connect(self.toggled.emit)
