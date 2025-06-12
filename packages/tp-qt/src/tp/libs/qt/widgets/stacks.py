from __future__ import annotations

from Qt.QtWidgets import QWidget, QStackedWidget

from ..mixins import stacked_animation_mixin


@stacked_animation_mixin
class SlidingOpacityStackedWidget(QStackedWidget):
    """Custom stack widget that activates opacity animation when
    the current stack index changes
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
