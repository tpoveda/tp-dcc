from __future__ import annotations

import contextlib

from Qt.QtCore import QObject
from Qt.QtWidgets import QWidget


@contextlib.contextmanager
def block_signals(widget: QObject, children: bool = False):
    """Context manager to temporarily block signals of a widget and its children.

    Args:
        widget: The widget whose signals should be blocked.
        children: Whether to block signals of the widget's children.
    """

    widget.blockSignals(True)
    child_widgets = widget.findChildren(QWidget) if children else []
    for child_widget in child_widgets:
        child_widget.blockSignals(True)
    try:
        yield widget
    finally:
        widget.blockSignals(False)
        for child_widget in child_widgets:
            child_widget.blockSignals(False)
