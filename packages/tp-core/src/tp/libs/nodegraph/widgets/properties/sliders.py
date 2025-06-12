from __future__ import annotations

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import (
    QSizePolicy,
    QWidget,
    QSlider,
    QSpinBox,
    QDoubleSpinBox,
    QAbstractSpinBox,
    QHBoxLayout,
)
from Qt.QtGui import QMouseEvent

from .abstract import AbstractPropertyWidget


class SliderPropertyWidget(AbstractPropertyWidget):
    """
    Property widget that represents a slider.
    """

    def __init__(
        self,
        disable_scroll: bool = True,
        realtime_update: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self._block: bool = False
        self._disable_scroll = disable_scroll
        self._realtime_update = realtime_update

        self._slider = QSlider(parent=self)
        self._spinbox = QSpinBox(parent=self)

        self._setup_ui()
        self._setup_signals()

    def get_value(self) -> int:
        """
        Returns the value of the property widget.

        :return: value of the property widget.
        """

        return self._spinbox.value()

    def set_value(self, value: int):
        """
        Sets the value of the property widget.

        :param value: value to set.
        """

        if value == self.get_value():
            return

        self._block = True
        try:
            self._spinbox.setValue(value)
            self.valueChanged.emit(self.name, value)
        finally:
            self._block = False

    def set_min(self, value: int):
        """
        Sets the minimum value of the property widget.

        :param value: minimum value to set.
        """

        self._slider.setMinimum(value)
        self._spinbox.setMinimum(value)

    def set_max(self, value: int):
        """
        Sets the maximum value of the property widget.

        :param value: maximum value to set.
        """

        self._slider.setMaximum(value)
        self._spinbox.setMaximum(value)

    def _setup_ui(self):
        """
        Internal function that sets up the UI of the property widget.
        """

        self._slider.setOrientation(Qt.Horizontal)
        self._slider.setTickPosition(QSlider.TicksBelow)
        self._slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        main_layout.addWidget(self._spinbox)
        main_layout.addWidget(self._slider)

        self._slider_mouse_press_event = self._slider.mousePressEvent
        self._slider.mousePressEvent = self._on_slider_mouse_press
        self._slider.mouseReleaseEvent = self._on_slider_mouse_release

        if self._disable_scroll:
            self._slider.wheelEvent = lambda _: None
            self._spinbox.wheelEvent = lambda _: None

    def _setup_signals(self):
        """
        Internal function that sets up all signals and slots connections.
        """

        self._slider.valueChanged.connect(self._on_slider_value_changed)
        self._spinbox.valueChanged.connect(self._on_spinbox_value_changed)

    def _on_slider_mouse_press(self, event: QMouseEvent):
        """
        Internal callback function that is called when the slider is clicked.

        :param event: mouse event.
        """

        self._block = True
        self._slider_mouse_press_event(event)

    def _on_slider_mouse_release(self, event: QMouseEvent):
        """
        Internal callback function that is called when the slider is released.

        :param event: mouse event.
        """

        if not self._realtime_update:
            self.valueChanged.emit(self.name, self.get_value())
        self._block = False

    def _on_slider_value_changed(self, value: int):
        """
        Internal callback function that is called when the slider value changes.

        :param value: slider value.
        """

        self._spinbox.setValue(value)
        if self._realtime_update:
            self.valueChanged.emit(self.name, self.get_value())

    def _on_spinbox_value_changed(self, value: int):
        """
        Internal callback function that is called when the spinbox value changes.

        :param value: spinbox value.
        """

        if value == self._slider.value():
            return

        self._slider.setValue(value)
        if not self._block:
            self.valueChanged.emit(self.name, self.get_value())


class DoubleSliderPropertyWidget(SliderPropertyWidget):
    """
    Property widget that represents a double slider.
    """

    def __init__(
        self,
        decimals: int = 2,
        disable_scroll: bool = True,
        realtime_update: bool = False,
        parent: QWidget | None = None,
    ):
        # Initialize parent class.
        super(SliderPropertyWidget, self).__init__(parent=parent)

        self._block = False
        self._realtime_update = realtime_update
        self._disable_scroll = disable_scroll
        self._slider = DoubleSlider(decimals=decimals, parent=self)
        self._spinbox = QDoubleSpinBox(parent=self)

        self._setup_ui()
        self._setup_signals()

    def _setup_signals(self):
        """
        Internal function that sets up all signals and slots connections.
        """

        self._slider.doubleValueChanged.connect(self._on_slider_value_changed)
        self._spinbox.valueChanged.connect(self._on_spinbox_value_changed)


class DoubleSlider(QSlider):
    """
    Slider that represents a double.
    """

    doubleValueChanged = Signal(float)

    def __init__(self, decimals: int = 2, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._multiplier: int = 10**decimals

        self.valueChanged.connect(self._on_value_changed)

    def value(self) -> float:
        """
        Returns the value of the slider.

        :return: value of the slider.
        """

        return float(super().value()) / self._multiplier

    def setValue(self, value: float):
        """
        Sets the value of the slider.

        :param value: value to set.
        """

        super().setValue(int(value * self._multiplier))

    def setMinimum(self, value: float):
        """
        Sets the minimum value of the slider.

        :param value: minimum value to set.
        """

        super().setMinimum(int(value * self._multiplier))

    def setMaximum(self, value: float):
        """
        Sets the maximum value of the slider.

        :param value: maximum value to set.
        """

        super().setMaximum(int(value * self._multiplier))

    def singleStep(self) -> float:
        """
        Returns the single step of the slider.

        :return: single step of the slider.
        """

        return float(super().singleStep()) / self._multiplier

    def setSingleStep(self, value: float):
        """
        Sets the single step of the slider.

        :param value: single step to set.
        """

        super().setSingleStep(int(value * self._multiplier))

    def _on_value_changed(self):
        """
        Internal callback function that is called when the value changes.
        """

        value = float(super().value()) / self._multiplier
        self.doubleValueChanged.emit(value)
