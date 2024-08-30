from __future__ import annotations

import numbers
from typing import Type, Any
from dataclasses import dataclass

from Qt.QtGui import QColor


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


Exec = DataType("Exec", type(None), QColor("#FFFFFF"), "", None)
String = DataType("String", str, QColor("#A203F2"), "Name", "")
Numeric = DataType("Numeric", numbers.Complex, QColor("#DEC017"), "Number", 0.0)
Boolean = DataType("Boolean", bool, QColor("#C40000"), "Condition", False)
List = DataType("List", list, QColor("#0BC8F1"), "List", [], is_runtime=True)
Dict = DataType("Dict", dict, QColor("#0BC8F1"), "Dict", {})
