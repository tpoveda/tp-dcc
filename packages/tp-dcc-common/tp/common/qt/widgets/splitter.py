# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom splitter widgets
"""

from Qt.QtCore import Qt, Signal, QSize
from Qt.QtWidgets import QSplitter, QSplitterHandle
from Qt.QtGui import QColor, QPainter, QBrush

from tp.core.managers import resources
from tp.common.qt.widgets import buttons


class CollapsibleSplitter(QSplitter, object):

    doExpand = Signal()
    doCollapse = Signal()

    def __init__(self, orientation=Qt.Vertical, parent=None):

        self._handle = None
        super(CollapsibleSplitter, self).__init__(parent)

        self.setHandleWidth(16)
        self.setOrientation(orientation)

    def createHandle(self):
        self._handle = CollapsibleSplitterHandle(self.orientation(), self)
        self._handle.buttonClicked.connect(self._on_update_splitter)
        return self._handle

    def _on_update_splitter(self, expand):
        if expand:
            self.setSizes([1, 1])
        else:
            self.setSizes([1, 0])

    def expand(self):
        self._handle.expand()
        self.doExpand.emit()

    def collapse(self):
        self._handle.collapse()
        self.doCollapse.emit()


class CollapsibleSplitterButton(buttons.HoverButton, object):

    clickedButton = Signal()

    def __init__(self, icon=None, hover_icon=None, pressed_icon=None, parent=None):
        super(CollapsibleSplitterButton, self).__init__(
            icon=icon, hover_icon=hover_icon, pressed_icon=pressed_icon, parent=parent
        )

        self._can_emit_signal = True

    def mouseMoveEvent(self, event):
        super(CollapsibleSplitterButton, self).mouseMoveEvent(event)
        self._can_emit_signal = False
        if self._mouse_pressed:
            if self._pressed_icon:
                self.setIcon(self._pressed_icon)
            else:
                self.setIcon(self._idle_icon)

    def mouseReleaseEvent(self, event):
        if self.rect().contains(event.pos()) and self._can_emit_signal:
            self.clickedButton.emit()
        self._can_emit_signal = True
        super(CollapsibleSplitterButton, self).mouseReleaseEvent(event)


class CollapsibleSplitterHandle(QSplitterHandle, object):

    buttonClicked = Signal(bool)

    def __init__(self, orientation, parent):
        super(CollapsibleSplitterHandle, self).__init__(orientation, parent)

        self._is_expanded = True

        expand_icon = resources.icon('back')
        expand_hover_icon = resources.icon('expand_hover')
        expand_pressed_icon = resources.icon('expand_pressed')
        self.expand_btn = CollapsibleSplitterButton(
            icon=expand_icon, hover_icon=expand_hover_icon, pressed_icon=expand_pressed_icon, parent=self
        )
        self.expand_btn.setFixedWidth(16)
        self.expand_btn.setFixedHeight(16)
        self.expand_btn.setIconSize(QSize(16, 16))
        self.expand_btn.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self.expand_btn.setFocusPolicy(Qt.NoFocus)
        self.expand_btn.setVisible(False)

        collapse_icon = resources.icon('next')
        collapse_hover_icon = resources.icon('collapse_hover')
        collapse_pressed_icon = resources.icon('collapse_pressed')
        self.collapse_btn = CollapsibleSplitterButton(
            icon=collapse_icon, hover_icon=collapse_hover_icon, pressed_icon=collapse_pressed_icon, parent=self
        )
        self.collapse_btn.setFixedWidth(16)
        self.collapse_btn.setFixedHeight(16)
        self.collapse_btn.setIconSize(QSize(16, 16))
        self.collapse_btn.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self.collapse_btn.setFocusPolicy(Qt.NoFocus)
        self.collapse_btn.setVisible(False)
        if self.orientation() == Qt.Horizontal:
            self.collapse_btn.setCursor(Qt.SplitHCursor)
        else:
            self.collapse_btn.setCursor(Qt.SplitVCursor)

        self.expand_btn.clickedButton.connect(self.expand)
        self.collapse_btn.clickedButton.connect(self.collapse)

        self.expand()

    def mouseMoveEvent(self, event):
        if self._is_expanded:
            super(CollapsibleSplitterHandle, self).mouseMoveEvent(event)

    def resizeEvent(self, event):
        y = self.rect().height() * 0.5 - self.expand_btn.height() * 0.5
        self.expand_btn.move(0, y)
        self.collapse_btn.move(0, y)

    def paintEvent(self, event):

        painter = QPainter(self)

        if self._is_expanded:
            rect2 = event.rect()
            rect2.setX(15)
            rect2.setWidth(1)
            painter.fillRect(rect2, QBrush(QColor(87, 87, 87)))

    def collapse(self):
        self.expand_btn.setVisible(True)
        self.collapse_btn.setVisible(False)
        self._is_expanded = False
        self.setCursor(Qt.ArrowCursor)
        self.update()
        self.buttonClicked.emit(False)

    def expand(self):
        self.expand_btn.setVisible(False)
        self.collapse_btn.setVisible(True)
        self._is_expanded = True
        if self.orientation() == Qt.Horizontal:
            self.setCursor(Qt.SplitHCursor)
        else:
            self.setCursor(Qt.SplitVCursor)
        self.update()
        self.buttonClicked.emit(True)
