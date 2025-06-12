from __future__ import annotations

import numbers
from typing import Type, Any
from dataclasses import dataclass

from Qt.QtGui import QColor

from ..views.uiconsts import PropertyWidget


@dataclass
class DataType:
    """
    Class that defines all data types.
    """

    name: str
    type_class: Type
    color: QColor
    label: str
    default: Any
    is_runtime: bool = False
    property_type: PropertyWidget | None = None


Exec = DataType("Exec", type(None), QColor("#FFFFFF"), "", None)
Any = DataType("Any", type(Any), QColor("#171717"), "Any", None, is_runtime=True)
String = DataType(
    "String", str, QColor("#A203F2"), "Name", "", property_type=PropertyWidget.LineEdit
)
Numeric = DataType(
    "Numeric",
    numbers.Complex,
    QColor("#DEC017"),
    "Number",
    0.0,
    property_type=PropertyWidget.DoubleSpinBox,
)
Boolean = DataType(
    "Boolean",
    bool,
    QColor("#C40000"),
    "Condition",
    False,
    property_type=PropertyWidget.CheckBox,
)
List = DataType(
    "List",
    list,
    QColor("#0BC8F1"),
    "List",
    [],
    is_runtime=True,
)
Dict = DataType("Dict", dict, QColor("#0BC8F1"), "Dict", {})
