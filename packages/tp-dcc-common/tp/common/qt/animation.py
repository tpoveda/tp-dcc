#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class with classes and function to work with GUI animations
"""

from Qt.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from Qt.QtWidgets import QGraphicsOpacityEffect
from Qt.QtGui import QFont, QColor, QPen, QBrush

from tp.core import dcc


class BaseAnimObject(object):
    _glow_pens = {}
    for index in range(1, 11):
        _glow_pens[index] = [QPen(QColor(0, 255, 0, 12 * index), 1, Qt.SolidLine),
                             QPen(QColor(0, 255, 0, 5 * index), 3, Qt.SolidLine),
                             QPen(QColor(0, 255, 0, 2 * index), 5, Qt.SolidLine),
                             QPen(QColor(0, 255, 0, 25.5 * index), 1, Qt.SolidLine)]

    _pens_text = QPen(QColor(202, 207, 210), 1, Qt.SolidLine)
    _pens_shadow = QPen(QColor(9, 10, 12), 1, Qt.SolidLine)
    _pens_border = QPen(QColor(9, 10, 12), 2, Qt.SolidLine)
    _pens_clear = QPen(QColor(0, 0, 0, 0), 1, Qt.SolidLine)

    _pens_text_disabled = QPen(QColor(102, 107, 110), 1, Qt.SolidLine)
    _pens_shadow_disabled = QPen(QColor(0, 0, 0), 1, Qt.SolidLine)

    _brush_clear = QBrush(QColor(0, 0, 0, 0))
    _brush_border = QBrush(QColor(9, 10, 12))

    def __init__(self):
        font = QFont()
        font.setPointSize(8)
        font.setFamily("Calibri")
        self.setFont(font)

        self._hover = False
        self._glow_index = 0
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._animate_glow)

    def enterEvent(self, event):
        super(self.__class__, self).enterEvent(event)

        if not self.isEnabled():
            return

        self._hover = True
        self._start_anim()

    def leaveEvent(self, event):
        super(self.__class__, self).leaveEvent(event)

        if not self.isEnabled():
            return

        self._hover = False
        self._start_anim()

    def _animate_glow(self):
        if self._hover:
            if self._glow_index >= 10:
                self._glow_index = 10
                self._anim_timer.stop()
            else:
                self._glow_index += 1

        else:
            if self._glow_index <= 0:
                self._glow_index = 0
                self._anim_timer.stop()
            else:
                self._glow_index -= 1

        dcc.execute_deferred(self.update)

    def _start_anim(self):
        if self._anim_timer.isActive():
            return

        self._anim_timer.start(20)


def property_animation(start=[0, 0], end=[30, 0], duration=300, object=None, property='iconSize', on_finished=None):
    """
    Functions that returns a ready to use QPropertyAnimation
    :param start: int, animation start value
    :param end: int, animation end value
    :param duration: int, duration of the effect
    :param object: variant, QDialog || QMainWindow
    :param property: str, object property to animate
    :param on_finished: variant, function to call when the animation is finished
    :return: QPropertyAnimation
    """

    animation = QPropertyAnimation(object, property, object)
    anim_curve = QEasingCurve()
    anim_curve.setType(QEasingCurve.InOutQuint)
    animation.setEasingCurve(anim_curve)
    animation.setDuration(duration)
    animation.setStartValue(start)
    animation.setEndValue(end)
    animation.start()

    return animation


def fade_in_widget(widget, duration=200, on_finished=None):
    """
    Fade in animation effect for widgets
    :param widget: QWidget, widget to apply effect
    :param duration: int, duration of the effect
    :param on_finished: variant, function to call when the animation is finished
    :return: QPropertyAnimation
    """

    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b'opacity')
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.InOutCubic)
    animation.start()

    if on_finished:
        animation.finished.connect(on_finished)

    widget._fade_in_ = animation

    return animation


def fade_out_widget(widget, duration=200, on_finished=None):
    """
    Fade out animation effect for widgets
    :param widget: QWidget, widget to apply effect
    :param duration: int, duration of the effect
    :param on_finished: variant, function to call when the animation is finished
    :return: QPropertyAnimation
    """

    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b'opacity')
    animation.setDuration(duration)
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)
    animation.setEasingCurve(QEasingCurve.InOutCubic)
    animation.start()

    if on_finished:
        animation.finished.connect(on_finished)

    widget._fade_out_ = animation

    return animation


def fade_window(start=0, end=1, duration=300, object=None, on_finished=None):
    """
    Fade animation for windows
    :param start: int, animation start value
    :param end: int, animation end value
    :param duration: int, duration of the effect
    :param object: variant, QDialog || QMainWindow
    :param on_finished: variant, function to call when the animation is finished
    :return: QPropertyAnimation
    """

    anim_curve = QEasingCurve()
    anim_curve.setType(QEasingCurve.OutQuint)
    animation = QPropertyAnimation(object, b'windowOpacity', object)
    animation.setEasingCurve(anim_curve)
    animation.setDuration(duration)
    animation.setStartValue(start)
    animation.setEndValue(end)
    animation.start()

    if on_finished:
        animation.finished.connect(on_finished)

    return animation


def slide_window(start=-100, end=0, duration=300, object=None, on_finished=None):
    """
    Slide animation for windows
    :param start: int, animation start value
    :param end: int, animation end value
    :param duration: int, duration of the effect
    :param object: variant, QDialog || QMainWindow
    :param on_finished: variant, function to call when the animation is finished
    :return: QPropertyAnimation
    """

    pos = object.pos()
    animation = QPropertyAnimation(object, b'pos', object)
    animation.setDuration(duration)
    anim_curve = QEasingCurve()
    if start >= end:
        anim_curve.setType(QEasingCurve.OutExpo)
    else:
        anim_curve.setType(QEasingCurve.InOutExpo)
    animation.setEasingCurve(anim_curve)
    animation.setStartValue(QPoint(pos.x(), pos.y() + start))
    animation.setEndValue(QPoint(pos.x(), pos.y() + end))
    animation.start()

    if on_finished:
        animation.finished.connect(on_finished)

    return animation


def fade_animation(start=0, end=1, duration=300, object=None, on_finished=None):
    """
    Fade animation for widgets
     :param start: int, animation start value
    :param end: int, animation end value
    :param duration: int, duration of the effect
    :param object: variant, QDialog || QMainWindow
    :param on_finished: variant, function to call when the animation is finished
    :return: QPropertyAnimation
    """

    anim_curve = QEasingCurve()
    anim_curve.setType(QEasingCurve.OutQuint)

    if start == 'current':
        start = object.opacity()
    if end == 'current':
        end = object.opacity()

    animation = QPropertyAnimation(object, b'opacity', object)
    animation.setEasingCurve(anim_curve)
    animation.setDuration(duration)
    animation.setStartValue(start)
    animation.setEndValue(end)
    animation.start()

    if on_finished:
        animation.finished.connect(on_finished)
