#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains lightbox widets
"""

from Qt.QtCore import Signal, QEvent
from Qt.QtWidgets import QWidget, QFrame

from tpDcc.libs.qt.core import animation
from tpDcc.libs.qt.widgets import layouts


class Lightbox(QFrame, object):

    closed = Signal()
    DEFAULT_DURATION = 400

    def __init__(self, parent, widget=None, duration=DEFAULT_DURATION):
        super(Lightbox, self).__init__(parent)

        self.setObjectName('Lightbox')

        self._widget = None
        self._accepted = False
        self._rejected = False
        self._animation = None
        self._duration = duration

        self.setStyleSheet('background-color: rgba(255, 0, 0, 50);')

        layout = layouts.GridLayout(parent=self)
        self.setLayout(layout)

        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 5)
        layout.setRowStretch(2, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 5)
        layout.setColumnStretch(2, 1)

        layout.addWidget(QWidget(), 0, 0)
        layout.addWidget(QWidget(), 0, 1)
        layout.addWidget(QWidget(), 0, 2)
        layout.addWidget(QWidget(), 1, 0)
        layout.addWidget(QWidget(), 1, 2)
        layout.addWidget(QWidget(), 2, 0)
        layout.addWidget(QWidget(), 2, 1)
        layout.addWidget(QWidget(), 2, 2)

        if widget:
            self.setWidget(widget)

        parent = self.parent()
        parent.installEventFilter(self)

    def widget(self):
        """
        Returns the current widget for the light box
        :return: QWidget
        """

        return self._widget

    def mousePressEvent(self, event):
        """
        Overrides base QFrame mousePressEvent function
        Hides the light box if the user clicks in it
        :param event: QEvent
        """

        widget = self.widget()
        if not widget or not widget.underMouse():
            self.reject()

    def eventFilter(self, object, event):
        """
        Overrides base QFrame eventFilter function
        Updates the geometry when the parent widget changes size
        :param object: QWidget
        :param event: QEvent
        :return: bool
        """

        try:
            if event.type() == QEvent.Resize:
                self.updateGeometry()

            return super(Lightbox, self).eventFilter(object, event)
        except Exception:
            return True

    def updateGeometry(self):
        """
        Overrides base QFrame updateGeometry function
        Updates the geometry to be in the center of its parent
        """

        self.setGeometry(self.parent().geometry())
        self.move(0, 0)
        geometry = self.geometry()
        center_point = self.geometry().center()
        geometry.moveCenter(center_point)
        geometry.setY(geometry.y())
        self.move(geometry.topLeft())

    def showEvent(self, event):
        """
        Overrides base QFrame showEvent
        :param event: QEvent
        """

        self.updateGeometry()
        self.fade_in(self._duration)

    def set_widget(self, widget):
        """
        Set the widget for the light box
        :param widget: QWidget
        """

        if self._widget:
            self.layout().removeWidget(self._widget)

        widget.setParent(self)
        widget.accept = self.accept
        widget.reject = self.reject

        self.layout().addWidget(widget, 1, 1)
        self._widget = widget

    def fade_in(self, duration=200):
        """
        Fade in the dialog using the opacity effect
        :param duration: int
        :return: QPropertyAnimation
        """

        self._animation = animation.fade_in_widget(self, duration=duration)
        return self._animation

    def fade_out(self, duration=200):
        """
        Fade out the dialog using the opacity effect
        :param duration: int
        :return: QPrropertyAnimation
        """

        self._animation = animation.fade_out_widget(self, duration=duration)
        return self._animation

    def accept(self):
        """
        Triggered when the DialogButton has been accepted
        """

        if not self._accepted:
            self._accepted = True
            animation = self.fade_out(self._duration)
            if animation:
                animation.finished.connect(self._on_accept_animation_finished)
            else:
                self._accept_animation_finished()

    def reject(self):
        """
        Triggered when the DialogButtonBox has been rejected
        """

        if not self._rejected:
            self._rejected = True
            animation = self.fade_out(self._duration)
            if animation:
                animation.finished.connect(self._on_reject_animation_finished)
            else:
                self._reject_animation_finished()

    def _on_accept_animation_finished(self):
        """
        Internal function triggered when the animation has finished on accepted
        """

        if hasattr(self.widget().__class__, 'accept'):
            self.widget().__class__.accept(self.widget())

        self.close()
        self.closed.emit()

    def _on_reject_animation_finished(self):
        """
        Internal function triggered when the animation has finished on rejected
        """

        if hasattr(self.widget().__class__, 'reject'):
            self.widget().__class__.reject(self.widget())

        self.close()
        self.closed.emit()
