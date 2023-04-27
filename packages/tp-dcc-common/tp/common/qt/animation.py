#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Qt animations
"""

from Qt.QtCore import QPoint, QSize, QPropertyAnimation, QEasingCurve
from Qt.QtWidgets import QGraphicsOpacityEffect

from tp.core import log

logger = log.tpLogger


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


def animate_widget_size(
        element, start=(300, 100), end=(300, 150), expanding=False, attribute_list=('minimumSize', 'maximumSize')):
    """
    Animates given widget size.

    :param QWidget element: widget to animate.
    :param tuple(int, int) start: start size.
    :param tuple(int, int) end: end size.
    :param bool expanding: whether to expand the widget.
    :param list(str) attribute_list: list of size attributes to animate.
    """

    duration = min(abs(start[1] - end[1]) * 5, 500)
    for attribute in attribute_list:
        if attribute == 'minimumSize':
            element.setMinimumHeight(end[1])
        elif attribute == 'maximumSize':
            element.setMaximumHeight(0)

        animation = QPropertyAnimation(element, attribute.encode('utf-8'), element)
        if attribute == 'maximumSize':
            animation.setStartValue(QSize(6000, start[1]))
            animation.setEndValue(QSize(6000, end[1]))
        else:
            animation.setStartValue(QSize(0, start[1]))
            animation.setEndValue(QSize(0, end[1]))

        style = QEasingCurve()
        if start[1] <= end[1]:
            style.setType(QEasingCurve.OutBounce)
            style.setAmplitude(0.2)
        else:
            style.setType(QEasingCurve.InOutQuart)
        animation.setEasingCurve(style)

        if expanding:
            if start[1] <= end[1]:
                if attribute == 'maximumSize':
                    [animation.finished.connect(x) for x in [
                        lambda: element.setMaximumHeight(1699999), lambda: element.setMinimumHeight(0)]]

        animation.setDuration(duration)
        animation.start(QPropertyAnimation.DeleteWhenStopped)


def fade_opacity_effect(start=0, end=1, duration=300, target_object=None, on_finished=None):
    """
    Fades with opacity graphics effect.

    :param float or str start: animation start value.
    :param float or str end: animation end value.
    :param int duration: duration of the effect.
    :param QGraphicsOpacityEffect target_object: target graphics effect we want to apply animation to.
    :param callable or None on_finished: function to call when the animation is finished.
    """

    style = QEasingCurve()
    style.setType(QEasingCurve.OutQuint)

    if start == 'current':
        try:
            start = target_object.opacity()
        except:
            start = 1
    if end == 'current':
        end = target_object.opacity()

    try:
        opacity_animation = QPropertyAnimation(target_object, "opacity".encode("utf-8"), target_object)
        opacity_animation.setEasingCurve(style)
        opacity_animation.setDuration(duration)
        opacity_animation.setStartValue(start)
        opacity_animation.setEndValue(end)
        opacity_animation.start()
        if on_finished is not None:
            opacity_animation.finished.connect(on_finished)
    except Exception:
        pass


def fade_window(start=0, end=1, duration=300, target_object=None, on_finished=None):
    """
    Fade animation for windows/dialogs.

    :param int start: animation start value.
    :param int end: animation end value.
    :param int duration: duration of the effect.
    :param QDialog or QMainWindow target_object: target object we want to apply animation to.
    :param callable or None on_finished: function to call when the animation is finished.
    :return: animated Qt property.
    :rtype: QPropertyAnimation
    """

    anim_curve = QEasingCurve()
    anim_curve.setType(QEasingCurve.OutQuint)
    animation = QPropertyAnimation(target_object, b'windowOpacity', target_object)
    animation.setEasingCurve(anim_curve)
    animation.setDuration(duration)
    animation.setStartValue(start)
    animation.setEndValue(end)
    animation.start()

    if on_finished:
        animation.finished.connect(on_finished)

    return animation


def slide_window(start=-100, end=0, duration=300, target_object=None, animation_style=None, on_finished=None):
    """
    Slide animation for windows/dialogs.

    :param int start: animation start value (pos).
    :param int end: animation end value (pos).
    :param int duration: duration of the effect.
    :param QDialog or QMainWindow target_object: target object we want to apply animation to.
    :param animation_style:
    :param callable or None on_finished: function to call when the animation is finished.
    """

    pos = target_object.pos()

    slide_animation = QPropertyAnimation(target_object, b'pos', target_object)
    slide_animation.setDuration(duration)
    style = QEasingCurve()

    # change curve if the value is end or beginning
    style.setType(QEasingCurve.OutExpo if start >= end else QEasingCurve.InOutExpo)

    if animation_style is not None:
        style.setType(animation_style)

    if on_finished is not None:
        slide_animation.finished.connect(on_finished)

    slide_animation.setEasingCurve(style)
    slide_animation.setStartValue(QPoint(pos.x(), pos.y() + start))
    slide_animation.setEndValue(QPoint(pos.x(), pos.y() + end))
    slide_animation.start()


def slide_window(start=-100, end=0, duration=300, target_object=None, animation_style=None, on_finished=None):
    """
    Slide animation for windows/dialogs.

    :param int start: animation start value (pos).
    :param int end: animation end value (pos).
    :param int duration: duration of the effect.
    :param QDialog or QMainWindow target_object: target object we want to apply animation to.
    :param animation_style:
    :param callable or None on_finished: function to call when the animation is finished.
    """

    pos = target_object.pos()

    slide_animation = QPropertyAnimation(target_object, b'pos', target_object)
    slide_animation.setDuration(duration)
    style = QEasingCurve()

    # change curve if the value is end or beginning
    style.setType(QEasingCurve.OutExpo if start >= end else QEasingCurve.InOutExpo)

    if animation_style is not None:
        style.setType(animation_style)

    if on_finished is not None:
        slide_animation.finished.connect(on_finished)

    slide_animation.setEasingCurve(style)
    slide_animation.setStartValue(QPoint(pos.x(), pos.y() + start))
    slide_animation.setEndValue(QPoint(pos.x(), pos.y() + end))
    slide_animation.start()


def resize_window_animation(
        start=(0, 0), end=(0, 0), duration=300, target_object=None, attribute='maximumHeight', on_finished=None):
    """
    Resize animation for windows/dialogs.

    :param tuple(int, int) start: animation start value.
    :param tuple(int, int) end: animation end value.
    :param int duration: duration of the effect.
    :param QDialog or QMainWindow target_object: target object we want to apply animation to.
    :param str attribute: size attribute to animate.
    :param callable or None on_finished: function to call when the animation is finished.
    """

    style = QEasingCurve()
    style.setType(QEasingCurve.OutQuint)

    if start[0] == "current":
        start[0] = target_object.size().height()
    if start[1] == "current":
        start[1] = target_object.size().width()

    positon_animation = QPropertyAnimation(target_object, attribute.encode("utf-8"), target_object)
    positon_animation.setEasingCurve(style)
    positon_animation.setDuration(duration)
    positon_animation.setStartValue(QSize(start[0], start[1]))
    positon_animation.setEndValue(QSize(end[0], end[1]))
    positon_animation.start()

    if on_finished is not None:
        positon_animation.finished.connect(on_finished)


def property_animation(start=None, end=None, duration=300, object=None, property='iconSize', mode='InOutQuint'):
    """
    Animates given property.

    :param any start: start property animation value.
    :param any end: end property animation value.
    :param int duration: animation duration.
    :param object:
    :param str property: property name to animate.
    :param str mode: animation mode.
    """

    animation = QPropertyAnimation(object, property.encode('utf-8'), object)

    style = QEasingCurve()
    if mode == 'Linear':
        style.setType(QEasingCurve.Linear)
    elif mode == 'InQuad':
        style.setType(QEasingCurve.InQuad)
    elif mode == 'OutQuad':
        style.setType(QEasingCurve.OutQuad)
    if mode == 'InOutQuad':
        style.setType(QEasingCurve.InOutQuad)
    elif mode == 'OutInQuad':
        style.setType(QEasingCurve.OutInQuad)
    elif mode == 'InCubic':
        style.setType(QEasingCurve.InCubic)
    if mode == 'OutCubic':
        style.setType(QEasingCurve.OutCubic)
    elif mode == 'InOutCubic':
        style.setType(QEasingCurve.InOutCubic)
    elif mode == 'OutInCubic':
        style.setType(QEasingCurve.OutInCubic)
    if mode == 'InQuart':
        style.setType(QEasingCurve.InQuart)
    elif mode == 'OutQuart':
        style.setType(QEasingCurve.OutQuart)
    elif mode == 'InOutQuart':
        style.setType(QEasingCurve.InOutQuart)
    if mode == 'OutInQuart':
        style.setType(QEasingCurve.OutInQuart)
    elif mode == 'InQuint':
        style.setType(QEasingCurve.InQuint)
    elif mode == 'InBounce':
        style.setType(QEasingCurve.InBounce)
    elif mode == 'OutExpo':
        style.setType(QEasingCurve.OutExpo)
    elif mode == 'InExpo':
        style.setType(QEasingCurve.InExpo)
    elif mode == 'InOutQuint':
        style.setType(QEasingCurve.InOutQuint)
    elif mode == 'OutBounce':
        style.setType(QEasingCurve.OutBounce)
        style.setAmplitude(0.5)
    else:
        logger.wraning("Property Animation Mode not supported:", mode)
        style.setType(QEasingCurve.InOutQuint)

    animation.setEasingCurve(style)
    animation.setDuration(duration)

    # TODO: here we should be able to support any property not only iconSize
    if start[0] == 'current':
        start_value_x = object.iconSize().height()
    else:
        start_value_x = start[0]
    if start[1] == 'current':
        start_value_y = object.iconSize().width()
    else:
        start_value_y = start[1]
    animation.setStartValue(QSize(start_value_x, start_value_y))
    animation.setEndValue(QSize(end[0], end[0]))

    animation.start()


def fade_animation(start=0, end=1, duration=300, object=None, on_finished=None, window_animation=True):
    """
    Fade animation for widgets.

    :param start: int, animation start value
    :param end: int, animation end value
    :param duration: int, duration of the effect
    :param object: variant, QDialog || QMainWindow
    :param on_finished: variant, function to call when the animation is finished
    :return: QPropertyAnimation
    """

    if window_animation is True:
        style = QEasingCurve()
        style.setType(QEasingCurve.OutQuint)
        if start == 'current':
            try:
                start = object.opacity()
            except Exception:
                start = 1
        if end == 'current':
            end = object.opacity()

        try:
            opacity_animation = QPropertyAnimation(object, 'opacity'.encode('utf-8'), object)
            opacity_animation.setEasingCurve(style)
            opacity_animation.setDuration(duration)
            opacity_animation.setStartValue(start)
            opacity_animation.setEndValue(end)
            opacity_animation.start()
            if on_finished:
                opacity_animation.finished.connect(on_finished)
        except Exception:
            pass
    else:
        object.setOpacity(end)
