from __future__ import annotations

import contextlib

from ..externals.Qt.QtCore import QObject
from ..externals.Qt.QtWidgets import QWidget


@contextlib.contextmanager
def block_signals(widget: QObject, children: bool = False):
    """
    Context manager to temporarily block signals of a widget and its children.

    :param widget: The widget whose signals should be blocked.
    :param children: Whether to block signals of the widget's children. Defaults to False.

    Usage:
    with block_signals(widget):
        # Code block where signals are blocked
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
