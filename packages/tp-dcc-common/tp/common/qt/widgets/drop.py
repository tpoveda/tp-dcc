#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Qt drop behaviour
"""

from Qt.QtCore import Qt, QPoint, QRect, QRectF, QLineF, QSizeF
from Qt.QtWidgets import QBoxLayout, QWidget, QFrame, QLabel
from Qt.QtGui import QCursor, QPixmap, QColor, QPalette, QPainter, QBrush, QLinearGradient

from tpDcc.libs.qt.core import qtutils
from tpDcc.libs.qt.widgets import layouts


class DropArea(object):
    InvalidDropArea = 0
    TopDropArea = 1
    RightDropArea = 2
    BottomDropArea = 3
    LeftDropArea = 4
    CenterDropArea = 5

    AllAreas = [TopDropArea, RightDropArea, BottomDropArea, LeftDropArea, CenterDropArea]


class DropOverlay(QFrame, object):
    """
    Paints a translucent rectangle over another widget. The geometry of the rectangle
    is based on the mouse location
    """
    def __init__(self, parent=None):
        super(DropOverlay, self).__init__(parent=parent)

        self._allowed_areas = [DropArea.InvalidDropArea]
        self._cross = DropOverlayCross(overlay=self)
        self._full_area_drop = False
        self._last_location = DropArea.InvalidDropArea
        self._target = None
        self._target_rect = QRect()

        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setWindowOpacity(0.2)
        self.setWindowTitle('DropOverlay')

        top_bottom_layout = QBoxLayout(QBoxLayout.TopToBottom)
        top_bottom_layout.setContentsMargins(0, 0, 0, 0)
        top_bottom_layout.setSpacing(0)
        self.setLayout(top_bottom_layout)

        area_widgets = dict()
        area_widgets[DropArea.TopDropArea] = self.create_drop_indicator_widget(DropArea.TopDropArea)
        area_widgets[DropArea.RightDropArea] = self.create_drop_indicator_widget(DropArea.RightDropArea)
        area_widgets[DropArea.BottomDropArea] = self.create_drop_indicator_widget(DropArea.BottomDropArea)
        area_widgets[DropArea.LeftDropArea] = self.create_drop_indicator_widget(DropArea.LeftDropArea)
        area_widgets[DropArea.CenterDropArea] = self.create_drop_indicator_widget(DropArea.CenterDropArea)
        self._cross.set_area_widgets(area_widgets)
        self._cross.setVisible(False)
        self.setVisible(False)

    # region Static Functions
    @staticmethod
    def create_drop_indicator_pixmap(palette, size, drop_area):
        border_color = palette.color(QPalette.Active, QPalette.Highlight)
        background_color = palette.color(QPalette.Active, QPalette.Base)
        area_background_color = palette.color(QPalette.Active, QPalette.Highlight).lighter(150)

        pm = QPixmap(size.width(), size.height())
        pm.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pm)
        pen = painter.pen()
        base_rect = QRectF(pm.rect())

        painter.fillRect(base_rect, background_color)

        painter.save()
        area_rect = QRectF()
        area_line = QLineF()
        gradient = QLinearGradient()
        if drop_area == DropArea.TopDropArea:
            area_rect = QRectF(base_rect.x(), base_rect.y(), base_rect.width(), base_rect.height() * 0.5)
            area_line = QLineF(area_rect.bottomLeft(), area_rect.bottomRight())
            gradient.setStart(area_rect.topLeft())
            gradient.setFinalStop(area_rect.bottomLeft())
            gradient.setColorAt(0, area_background_color)
            gradient.setColorAt(1, area_background_color.lighter(120))
        elif drop_area == DropArea.RightDropArea:
            area_rect = QRectF(base_rect.width() * 0.5, base_rect.y(), base_rect.width() * 0.5, base_rect.height())
            area_line = QLineF(area_rect.topLeft(), area_rect.bottomLeft())
            gradient.setStart(area_rect.topLeft())
            gradient.setFinalStop(area_rect.topRight())
            gradient.setColorAt(0, area_background_color.lighter(120))
            gradient.setColorAt(1, area_background_color)
        elif drop_area == DropArea.BottomDropArea:
            area_rect = QRectF(base_rect.x(), base_rect.height() * 0.5, base_rect.width(), base_rect.height() * 0.5)
            area_line = QLineF(area_rect.topLeft(), area_rect.topRight())
            gradient.setStart(area_rect.topLeft())
            gradient.setFinalStop(area_rect.bottomLeft())
            gradient.setColorAt(0, area_background_color.lighter(120))
            gradient.setColorAt(1, area_background_color)
        elif drop_area == DropArea.LeftDropArea:
            area_rect = QRectF(base_rect.x(), base_rect.y(), base_rect.width() * 0.5, base_rect.height())
            area_line = QLineF(area_rect.topRight(), area_rect.bottomRight())
            gradient.setStart(area_rect.topLeft())
            gradient.setFinalStop(area_rect.topRight())
            gradient.setColorAt(0, area_background_color)
            gradient.setColorAt(1, area_background_color.lighter(120))

        if area_rect.isValid():
            painter.fillRect(area_rect, gradient)
            pen = painter.pen()
            pen.setColor(border_color)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(area_line)

        painter.restore()

        painter.save()
        pen = painter.pen()
        pen.setColor(border_color)
        pen.setWidth(1)

        painter.setPen(pen)
        painter.drawRect(base_rect.adjusted(0, 0, -pen.width(), -pen.width()))
        painter.restore()

        return pm

    @staticmethod
    def create_drop_indicator_widget(drop_area):
        layout = QLabel()
        layout.setObjectName('DropAreaLabel')
        metric = (layout.fontMetrics().height()) * 2.0
        size = QSizeF(metric, metric)
        layout.setPixmap(
            DropOverlay.create_drop_indicator_pixmap(palette=layout.palette(), size=size, drop_area=drop_area))

        return layout
    # endregion

    # region Override Functions
    def paintEvent(self, event):
        painter = QPainter(self)
        area_color = self.palette().color(QPalette.Active, QPalette.Highlight)

        if self._full_area_drop:
            r = self.rect()
            painter.fillRect(r, QBrush(area_color, Qt.Dense4Pattern))
            painter.setBrush(QBrush(area_color))
            painter.drawRect(r)
            return

        r = self.rect()
        drop_area = self.cursor_location()
        if drop_area == DropArea.TopDropArea:
            r.setHeight(r.height() * 0.5)
        elif drop_area == DropArea.RightDropArea:
            r.setX(r.width() * 0.5)
        elif drop_area == DropArea.BottomDropArea:
            r.setY(r.height() * 0.5)
        elif drop_area == DropArea.LeftDropArea:
            r.setWidth(r.width() * 0.5)
        elif drop_area == DropArea.CenterDropArea:
            r = self.rect()

        if not r.isNull():
            painter.fillRect(r, QBrush(area_color, Qt.Dense4Pattern))
            painter.setBrush(QBrush(area_color))
            painter.drawRect(r)

        # Draw rect over the entire size + border
        # r = self.rect()
        # r.setWidth(r.width() - 1)
        # r.setHeight(r.height() - 1)
        # painter.fillRect(r, QBrush(QColor(0, 100, 255), Qt.Dense4Pattern))
        # painter.setBrush(QColor(0, 100, 255))
        # painter.drawRect(r)

    def showEvent(self, event):
        self._cross.show()

    def hideEvent(self, event):
        self._cross.hide()

    def resizeEvent(self, event):
        self._cross.resize(event.size())

    def moveEvent(self, event):
        self._cross.move(event.pos())
        self._cross.move(event.pos())
    # endregion

    # region Public Functions
    def set_allowed_areas(self, areas):
        if areas == self._allowed_areas:
            return
        self._allowed_areas = areas
        self._cross.reset()

    def allowed_areas(self):
        return self._allowed_areas

    def set_area_widgets(self, widgets):
        self._cross.set_area_widgets(widgets=widgets)

    def cursor_location(self):
        return self._cross.cursor_location()

    def show_drop_overlay(self, target, target_area_rect=None):

        if target_area_rect is None:
            if self._target == target:
                drop_area = self.cursor_location()
                if drop_area != self._last_location:
                    self.repaint()
                    self._last_location = drop_area
                return drop_area

            self.hide_drop_overlay()
            self._full_area_drop = False
            self._target = target
            self._target_rect = QRect()
            self._last_location = DropArea.InvalidDropArea

            self.resize(target.size())
            self.move(target.mapToGlobal(target.rect().topLeft()))

            self.show()

            return self.cursor_location()
        else:
            if self._target == target and self._target_rect == target_area_rect:
                return

            self.hide_drop_overlay()
            self._full_area_drop = True
            self._target = target
            self._target_rect = target_area_rect
            self._last_location = DropArea.InvalidDropArea

            self.resize(target_area_rect.size())
            self.move(target.mapToGlobal(QPoint(target_area_rect.x(), target_area_rect.y())))

            self.show()

            return

    def hide_drop_overlay(self):
        self.hide()
        self._full_area_drop = False

        # Check if Qt Version > 5.0.0 -> If True:
        # self._target.clear
        # else
        # self._target = 0

        self._target = 0
        self._target_rect = QRect()
        self._last_location = DropArea.InvalidDropArea
    # endregion


class DropOverlayCross(QWidget, object):
    """
    Shows a cross with 5 different drop area possibilities
    """
    def __init__(self, overlay):
        super(DropOverlayCross, self).__init__(overlay.parentWidget())

        self._overlay = overlay
        self._widgets = None

        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setWindowTitle('DropOverlayCross')
        # self.setAttribute(Qt.WA_TranslucentBackground)

        self._grid = layouts.GridLayout(spacing=0, margins=(0, 0, 0, 0))

        bl1 = QBoxLayout(QBoxLayout.TopToBottom)
        bl1.setContentsMargins(0, 0, 0, 0)
        bl1.setSpacing(0)
        self.setLayout(bl1)

        bl2 = QBoxLayout(QBoxLayout.LeftToRight)
        bl2.setContentsMargins(0, 0, 0, 0)
        bl2.setSpacing(0)

        bl1.addStretch(1)
        bl1.addLayout(bl2)
        bl2.addStretch(1)
        bl2.addLayout(self._grid, 0)
        bl2.addStretch(1)
        bl1.addStretch(1)

    # region Static Functions
    @staticmethod
    def grid_pos_for_area(drop_area):
        """
        Given a drop area return the position in which the cross widget should be located
        :param drop_area: DropArea
        :return: tuple(QPoint, int)
        """

        if drop_area == DropArea.TopDropArea:
            return QPoint(0, 1), (Qt.AlignHCenter | Qt.AlignBottom)
        elif drop_area == DropArea.RightDropArea:
            return QPoint(1, 2), (Qt.AlignLeft | Qt.AlignVCenter)
        elif drop_area == DropArea.BottomDropArea:
            return QPoint(2, 1), (Qt.AlignHCenter | Qt.AlignTop)
        elif drop_area == DropArea.LeftDropArea:
            return QPoint(1, 0), (Qt.AlignRight | Qt.AlignVCenter)
        elif drop_area == DropArea.CenterDropArea:
            return QPoint(1, 1), Qt.AlignCenter
        else:
            return QPoint(), int()
    # endregion

    # region Override Functions
    def showEvent(self, event):
        self.resize(self._overlay.size())
        self.move(self._overlay.pos())
    # endregion

    # region Public Functions
    def set_area_widgets(self, widgets):
        qtutils.clear_layout(self._grid)
        self._widgets = widgets
        for drop_area, widget in self._widgets.items():
            opts = self.grid_pos_for_area(drop_area=drop_area)
            self._grid.addWidget(widget, opts[0].x(), opts[0].y(), opts[1])
        self.reset()

    def cursor_location(self):
        pos = self.mapFromGlobal(QCursor.pos())
        for drop_area, widget in self._widgets.items():
            if drop_area in self._overlay.allowed_areas():
                if widget:
                    if widget.isVisible() and widget.geometry().contains(pos):
                        return drop_area

        return DropArea.InvalidDropArea

    def reset(self):
        all_areas = [DropArea.TopDropArea, DropArea.RightDropArea, DropArea.BottomDropArea,
                     DropArea.LeftDropArea, DropArea.CenterDropArea]
        allowed_areas = self._overlay.allowed_areas()

        for i in range(len(all_areas)):
            opts = self.grid_pos_for_area(i)
            item = self._grid.itemAtPosition(opts[0].x(), opts[0].y())
            if item:
                w = item.widget()
                if w:
                    try:
                        w.setVisible(set(allowed_areas).issubset(set(all_areas)))
                    except Exception:
                        print('ALLOWED AREAS: ', allowed_areas)
                        print('ALL AREAS: ', all_areas)
    # endregion
