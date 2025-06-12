from __future__ import annotations

import typing

from Qt.QtWidgets import QWidget

from .base import (
    LabelPropertyWidget,
    LineEditPropertyWidget,
    TextEditPropertyWidget,
    ComboBoxPropertyWidget,
    CheckBoxPropertyWidget,
    SpinBoxPropertyWidget,
    DoubleSpinBoxPropertyWidget,
)
from .sliders import SliderPropertyWidget, DoubleSliderPropertyWidget
from .paths import FilePathPropertyWidget, FileSavePathPropertyWidget
from .colorpicker import ColorPickRGBPropertyWidget, ColorPickRGBAPropertyWidget
from .valuelineedit import IntLineEditPropertyWidget, FloatLineEditPropertyWidget
from .vectors import Vector2PropertyWidget, Vector3PropertyWidget, Vector4PropertyWidget
from ...views import uiconsts

if typing.TYPE_CHECKING:
    from .abstract import AbstractPropertyWidget


class NodePropertyWidgetFactory:
    """
    Factory class that allows to create node property widgets.
    """

    def __init__(self):
        super().__init__()

        self._widget_mapping: [int, QWidget | None] = {
            uiconsts.PropertyWidget.Hidden.value: None,
            uiconsts.PropertyWidget.Label.value: LabelPropertyWidget,
            uiconsts.PropertyWidget.LineEdit.value: LineEditPropertyWidget,
            uiconsts.PropertyWidget.TextEdit.value: TextEditPropertyWidget,
            uiconsts.PropertyWidget.ComboBox.value: ComboBoxPropertyWidget,
            uiconsts.PropertyWidget.CheckBox.value: CheckBoxPropertyWidget,
            uiconsts.PropertyWidget.SpinBox.value: SpinBoxPropertyWidget,
            uiconsts.PropertyWidget.DoubleSpinBox.value: DoubleSpinBoxPropertyWidget,
            uiconsts.PropertyWidget.ColorPicker.value: ColorPickRGBPropertyWidget,
            uiconsts.PropertyWidget.Color4Picker.value: ColorPickRGBAPropertyWidget,
            uiconsts.PropertyWidget.Slider.value: SliderPropertyWidget,
            uiconsts.PropertyWidget.DoubleSlider.value: DoubleSliderPropertyWidget,
            uiconsts.PropertyWidget.FileOpen.value: FilePathPropertyWidget,
            uiconsts.PropertyWidget.FileSave.value: FileSavePathPropertyWidget,
            uiconsts.PropertyWidget.Int.value: IntLineEditPropertyWidget,
            uiconsts.PropertyWidget.Float.value: FloatLineEditPropertyWidget,
            uiconsts.PropertyWidget.Vector2: Vector2PropertyWidget,
            uiconsts.PropertyWidget.Vector3: Vector3PropertyWidget,
            uiconsts.PropertyWidget.Vector4: Vector4PropertyWidget,
        }

    def widget(
        self, widget_type: int
    ) -> (
        QWidget
        | AbstractPropertyWidget
        | LabelPropertyWidget
        | LineEditPropertyWidget
        | TextEditPropertyWidget
        | ComboBoxPropertyWidget
        | CheckBoxPropertyWidget
        | SpinBoxPropertyWidget
        | DoubleSpinBoxPropertyWidget
        | ColorPickRGBPropertyWidget
        | ColorPickRGBAPropertyWidget
        | SliderPropertyWidget
        | DoubleSliderPropertyWidget
        | FilePathPropertyWidget
        | FileSavePathPropertyWidget
        | IntLineEditPropertyWidget
        | FloatLineEditPropertyWidget
        | Vector2PropertyWidget
        | Vector3PropertyWidget
        | Vector4PropertyWidget
        | None
    ):
        """
        Returns the widget for the given widget type.

        :param widget_type: int
        :return: QWidget | None
        """

        if widget_type not in self._widget_mapping:
            return

        return self._widget_mapping[widget_type]()
