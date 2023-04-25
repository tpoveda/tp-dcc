#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to create different kind of joystick widgets
"""

from Qt.QtCore import Qt, Signal, QPoint, QPointF, QRectF, QSize
from Qt.QtCore import QPropertyAnimation, QParallelAnimationGroup, QEasingCurve
from Qt.QtWidgets import QWidget
from Qt.QtGui import QPainter, QPen, QBrush, QRadialGradient


class JoyPad(QWidget, object):

    xChanged = Signal(float)
    yChanged = Signal(float)

    def __init__(self, parent=None):
        super(JoyPad, self).__init__(parent=parent)

        self._x = 0
        self._y = 0
        self._bounds = QRectF()
        self._knop_bounds = QRectF()
        self._last_pos = QPoint()
        self._knop_pressed = False

        self._return_animation = QParallelAnimationGroup(self)
        self._x_anim = QPropertyAnimation(self, 'x')
        self._y_anim = QPropertyAnimation(self, 'y')
        self._alignment = Qt.AlignTop | Qt.AlignLeft

        self._x_anim.setEndValue(0.0)
        self._x_anim.setDuration(400)
        self._x_anim.setEasingCurve(QEasingCurve.OutSine)

        self._y_anim.setEndValue(0.0)
        self._y_anim.setDuration(400)
        self._y_anim.setEasingCurve(QEasingCurve.OutSine)

        self._return_animation.addAnimation(self._x_anim)
        self._return_animation.addAnimation(self._y_anim)

    # region Static Functions
    @staticmethod
    def constraint(value, min_value, max_value):
        return min_value if value < min_value else max_value if value > max_value else value
    # endregion

    # region Properties
    def get_x(self):
        return self._x

    def set_x(self, x):
        self._x = self.constraint(x, -1.0, 1.0)
        radius = (self._bounds.width() - self._knop_bounds.width()) * 0.5
        self._knop_bounds.moveCenter(
            QPointF(self._bounds.center().x() + self._x * radius, self._knop_bounds.center().y()))
        self.update()
        self.xChanged.emit(self._x)

    def get_y(self):
        return self._y

    def set_y(self, y):
        self._y = self.constraint(y, -1.0, 1.0)
        radius = (self._bounds.width() - self._knop_bounds.width()) * 0.5
        self._knop_bounds.moveCenter(
            QPointF(self._knop_bounds.center().x(), self._bounds.center().y() - self._y * radius))
        self.update()
        self.yChanged.emit(self._x)

    def get_alignment(self):
        return self._alignment

    def set_alignment(self, alignment):
        self._alignment = alignment

    x = property(get_x, set_x)
    y = property(get_y, set_y)
    alignment = property(get_alignment, set_alignment)
    # endregion

    # region Override Functions
    def resizeEvent(self, event):
        a = min(self.width(), self.height())
        top_left = QPointF()
        if self._alignment & Qt.AlignTop:
            top_left.setY(0)
        elif self._alignment & Qt.AlignVCenter:
            top_left.setY((self.height() - a) * 0.5)
        elif self._alignment & Qt.AlignBottom:
            top_left.setY(self.height() - a)

        if self._alignment & Qt.AlignLeft:
            top_left.setX(0)
        elif self._alignment & Qt.AlignHCenter:
            top_left.setX((self.width() - a) * 0.5)
        elif self._alignment & Qt.AlignRight:
            top_left.setX(self.width() - a)

        self._bounds = QRectF(top_left, QSize(a, a))
        self._knop_bounds.setWidth(a * 0.3)
        self._knop_bounds.setHeight(a * 0.3)

        radius = (self._bounds.width() - self._knop_bounds.height()) * 0.5
        self._knop_bounds.moveCenter(
            QPointF(self._bounds.center().x() + self._x * radius, self._bounds.center().y() - self._y * radius))

    def mousePressEvent(self, event):
        if self._knop_bounds.contains(event.pos()):
            # self._return_animation.stop()
            self._last_pos = event.pos()
            self._knop_pressed = True

    def mouseReleaseEvent(self, event):
        self._knop_pressed = False
        self.x = 0.0
        self.y = 0.0
        # self._return_animation.start()

    def mouseMoveEvent(self, event):
        if not self._knop_pressed:
            return

        delta_pos = QPointF(event.pos() - self._last_pos)
        delta_pos += 0.5 * (QPointF(event.pos()) - self._knop_bounds.center())

        from_center_to_knop = self._knop_bounds.center() + delta_pos - self._bounds.center()
        radius = (self._bounds.width() - self._knop_bounds.width()) * 0.5
        from_center_to_knop.setX(self.constraint(from_center_to_knop.x(), -radius, radius))
        from_center_to_knop.setY(self.constraint(from_center_to_knop.y(), -radius, radius))
        self._knop_bounds.moveCenter(from_center_to_knop + self._bounds.center())
        self._last_pos = event.pos()

        self.update()

        if radius == 0:
            return
        x = (self._knop_bounds.center().x() - self._bounds.center().x()) / radius
        y = (-self._knop_bounds.center().y() + self._bounds.center().y()) / radius

        if self._x != x:
            self._x = x
            self.xChanged.emit(self._x)

        if self._y != y:
            self._y = y
            self.yChanged.emit(self._y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)

        gradient = QRadialGradient(self._bounds.center(), self._bounds.width() * 0.5, self._bounds.center())
        gradient.setFocalRadius(self._bounds.width() * 0.3)
        gradient.setCenterRadius(self._bounds.width() * 0.7)
        gradient.setColorAt(0, Qt.white)
        gradient.setColorAt(1, Qt.lightGray)

        painter.setPen(QPen(QBrush(Qt.gray), self._bounds.width() * 0.005))
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(self._bounds)

        painter.setPen(QPen(QBrush(Qt.gray), self._bounds.width() * 0.005))
        painter.drawLine(
            QPointF(self._bounds.left(), self._bounds.center().y()),
            QPointF(self._bounds.center().x() - self._bounds.width() * 0.35, self._bounds.center().y())
        )
        painter.drawLine(
            QPointF(self._bounds.center().x() + self._bounds.width() * 0.35, self._bounds.center().y()),
            QPointF(self._bounds.right(), self._bounds.center().y())
        )
        painter.drawLine(
            QPointF(self._bounds.center().x(), self._bounds.top()),
            QPointF(self._bounds.center().x(), self._bounds.center().y() - self._bounds.width() * 0.35)
        )
        painter.drawLine(
            QPointF(self._bounds.center().x(), self._bounds.center().y() + self._bounds.width() * 0.35),
            QPointF(self._bounds.center().x(), self._bounds.bottom())
        )

        if not self.isEnabled():
            return

        gradient = QRadialGradient(
            self._knop_bounds.center(), self._knop_bounds.width() * 0.5, self._knop_bounds.center())
        gradient.setFocalRadius(self._knop_bounds.width() * 0.2)
        gradient.setCenterRadius(self._knop_bounds.width() * 0.5)
        gradient.setColorAt(0, Qt.gray)
        gradient.setColorAt(1, Qt.darkGray)

        painter.setPen(QPen(QBrush(Qt.darkGray), self._bounds.width() * 0.005))
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(self._knop_bounds)

        # endregion

    # region Public Functions
    def add_x_animation(self):
        # Abort if the animation is already added
        if self._x_anim.parent() == self._return_animation:
            return

        self._return_animation.addAnimation(self._x_anim)

    def remove_x_animation(self):
        # Abort if the animation is already removed
        if self._x_anim.parent() != self._return_animation:
            return

        self._return_animation.removeAnimation(self._x_anim)

        # Take ownership of the animation (parent is 0 after removeAnimation())
        self._x_anim.setParent(self)

    def add_y_animation(self):
        # Abort if the animation is already added
        if self._y_anim.parent() == self._return_animation:
            return

        self._return_animation.addAnimation(self._y_anim)

    def remove_y_animation(self):
        # Abort if the animation is already removed
        if self._y_anim.parent() != self._return_animation:
            return

        self._return_animation.removeAnimation(self._y_anim)

        # Take ownership of the animation (parent is 0 after removeAnimation())
        self._y_anim.setParent(self)
    # endregion
