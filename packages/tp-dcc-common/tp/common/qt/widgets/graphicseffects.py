#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different graphic effects
"""

from Qt.QtCore import QPropertyAnimation, QEasingCurve
from Qt.QtWidgets import QGraphicsEffect, QGraphicsBlurEffect

from tp.common.python import decorators


class OpacityEffect(QGraphicsEffect, object):
    def __init__(self, target, duration, parent=None):
        super(OpacityEffect, self).__init__(parent=parent)

        self._target = target
        self._duration = duration
        self._animation = QPropertyAnimation(self._target, "opacity")
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(0.0)

    def get_duration(self):
        return self._duration

    def set_duration(self, value):
        self._duration = value

    def get_target(self):
        return self._target

    def set_target(self, value):
        self._target = value

    def get_animation(self):
        return self._animation

    duration = property(get_duration, set_duration)
    target = property(get_target, set_target)
    animation = property(get_animation)

    def fade_in_out(self):
        """
        Executes the animation
        """

        self._animation.stop()
        self._animation.setDuration(self._duration)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(0.0)
        self._animation.setKeyValueAt(0.3, 1.0)
        self._animation.setKeyValueAt(0.6, 1.0)
        self._animation.start()

    # region Functions
    def fade_in(self):
        """
        Fade in the opacity property of the effect target
        """

        self._animation.stop()
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._animation.setDuration(self._duration)
        self._animation.setStartValue(0)
        self._animation.setEndValue(1)
        self._animation.start()

    def fade_out(self):
        """
        Fade out the opacity property of the effect target
        """

        self._animation.stop()
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._animation.setDuration(self._duration)
        self._animation.setStartValue(1)
        self._animation.setEndValue(0)
        self._animation.start()


class GraphicsLayeredBlurEffect(QGraphicsBlurEffect, object):
    def __init__(self, inner_radius=0, outer_radius=0, parent=None):
        super(GraphicsLayeredBlurEffect, self).__init__(parent=parent)

        self._inner_radius = inner_radius
        self._outer_radius = outer_radius

    @property
    @decorators.returns(float)
    def inner_radius(self):
        return self._inner_radius

    @inner_radius.setter
    @decorators.accepts(float)
    def inner_radius(self, value):
        self._inner_radius = value

    @property
    @decorators.returns(float)
    def outer_radius(self):
        return self._outer_radius

    @outer_radius.setter
    @decorators.accepts(float)
    def outer_radius(self, value):
        self._outer_radius = value

    def draw(self, painter):
        if self._outer_radius > 0:
            self.setBlurRadius(self._outer_radius)
            super(GraphicsLayeredBlurEffect, self).draw(painter)
        if self._inner_radius > 0:
            self.setBlurRadius(self._inner_radius)
            super(GraphicsLayeredBlurEffect, self).draw(painter)
        super(GraphicsLayeredBlurEffect, self).drawSource(painter)
