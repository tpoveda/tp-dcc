from __future__ import annotations

from Qt.QtCore import QPoint, QPropertyAnimation, QEasingCurve
from Qt.QtWidgets import QWidget, QGraphicsOpacityEffect


def _stackable(widget):
    """Used for stacked_animation_mixin to only add mixin for widget who can be stacked."""

    # We use widget() to get currentWidget, use currentChanged to play the animation.
    # For now just QTabWidget and QStackedWidget can use this decorator.
    return (
        issubclass(widget, QWidget)
        and hasattr(widget, "widget")
        and hasattr(widget, "currentChanged")
    )


def stacked_animation_mixin(cls):
    """
    Decorator for stacked widget.
    When Stacked widget currentChanged, show opacity and position animation for current widget.
    """
    if not _stackable(cls):  # If widget can't stack, return the original widget class
        return cls
    old_init = cls.__init__

    def _new_init(self, *args, **kwargs):
        old_init(self, *args, **kwargs)
        self._previous_index = 0
        self._to_show_pos_ani = QPropertyAnimation()
        self._to_show_pos_ani.setDuration(400)
        self._to_show_pos_ani.setPropertyName(b"pos")
        self._to_show_pos_ani.setEndValue(QPoint(0, 0))
        self._to_show_pos_ani.setEasingCurve(QEasingCurve.OutCubic)

        self._to_hide_pos_ani = QPropertyAnimation()
        self._to_hide_pos_ani.setDuration(400)
        self._to_hide_pos_ani.setPropertyName(b"pos")
        self._to_hide_pos_ani.setEndValue(QPoint(0, 0))
        self._to_hide_pos_ani.setEasingCurve(QEasingCurve.OutCubic)

        self._opacity_eff = QGraphicsOpacityEffect()
        self._opacity_ani = QPropertyAnimation()
        self._opacity_ani.setDuration(400)
        self._opacity_ani.setEasingCurve(QEasingCurve.InCubic)
        self._opacity_ani.setPropertyName(b"opacity")
        self._opacity_ani.setStartValue(0.0)
        self._opacity_ani.setEndValue(1.0)
        self._opacity_ani.setTargetObject(self._opacity_eff)
        self._opacity_ani.finished.connect(self._disable_opacity)
        self.currentChanged.connect(self._play_anim)

    def _on_play_anim(self, index: int):
        """Internal callback function that is called when an animated is played.

        Args:
            index: new stack index.
        """

        current_widget = self.widget(index)
        if self._previous_index < index:
            self._to_show_pos_ani.setStartValue(QPoint(self.width(), 0))
            self._to_show_pos_ani.setTargetObject(current_widget)
            self._to_show_pos_ani.start()
        else:
            self._to_hide_pos_ani.setStartValue(QPoint(-self.width(), 0))
            self._to_hide_pos_ani.setTargetObject(current_widget)
            self._to_hide_pos_ani.start()
        if current_widget:
            current_widget.setGraphicsEffect(self._opacity_eff)
            current_widget.graphicsEffect().setEnabled(True)
        self._opacity_ani.start()
        self._previous_index = index

    def _on_disable_opacity(self):
        """Internal callback function that is called when opacity animation finishes"""

        if self.currentWidget():
            self.currentWidget().graphicsEffect().setEnabled(False)

    setattr(cls, "__init__", _new_init)
    setattr(cls, "_play_anim", _on_play_anim)
    setattr(cls, "_disable_opacity", _on_disable_opacity)

    return cls
