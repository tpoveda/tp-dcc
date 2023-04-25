#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains delegates that can be used to customize how data is renderer in list views
"""

import os

from Qt.QtCore import Qt, QPoint, QPointF, QRect, QRectF, QSize
from Qt.QtWidgets import QStyle, QStyledItemDelegate
from Qt.QtGui import QFontMetrics, QColor, QPalette, QTextOption, QPainter, QPen


class BaseListViewDelegate(QStyledItemDelegate, object):
    """
    Base delegate for list view widgets
    """

    _ICON_MARGIN = 4

    # region Override Functions
    def paint(self, painter, option, index):

        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        model = index.model()
        view = self.parent()

        if view.hasFocus() and option.state & QStyle.State_MouseOver:
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.gray)
            painter.drawRoundedRect(option.rect.adjusted(1, 1, -1, -1), self._ICON_MARGIN, self._ICON_MARGIN)

        pixmap = model.data(index, Qt.DecorationRole).pixmap(view.iconSize())
        pm_rect = QRect(option.rect.topLeft() + QPoint(self._ICON_MARGIN + 1, self._ICON_MARGIN + 1),
                        view.iconSize() - QSize(self._ICON_MARGIN * 2, self._ICON_MARGIN * 2))
        painter.drawPixmap(pm_rect, pixmap)
        if option.state & QStyle.State_Selected:
            painter.setPen(QPen(Qt.red, 1.0, Qt.SolidLine, Qt.SquareCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(option.rect.adjusted(2, 2, -2, -2))

        font = view.font()
        fm = QFontMetrics(font)
        text = os.path.splitext(os.path.basename(model.data(index, Qt.DisplayRole)))[0]
        text = fm.elidedText(text, Qt.ElideRight, view.iconSize().width() - 4)
        text_opt = QTextOption()
        text_opt.setAlignment(Qt.AlignHCenter)
        txt_rect = QRectF(
            QPointF(pm_rect.bottomLeft() + QPoint(0, 1)), QPointF(option.rect.bottomRight() - QPoint(4, 3)))

        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(22, 22, 22, 220))
        painter.drawRoundedRect(txt_rect.adjusted(-2, -2, 2, 2), 2, 2)
        painter.restore()
        painter.setPen(self.parent().palette().color(QPalette.WindowText))
        painter.drawText(txt_rect, text, text_opt)

        font.setPointSize(8)
        fm = QFontMetrics(font)
        item = model.itemFromIndex(index)
        size_text = '%d x %d' % (item.size.width(), item.size.height())
        size_rect = fm.boundingRect(option.rect, Qt.AlignLeft | Qt.AlignTop, size_text)
        size_rect.translate(4, 4)

        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(22, 22, 22, 220))
        painter.drawRoundedRect(size_rect.adjusted(-2, -2, 2, 2), 2, 2)
        painter.restore()
        painter.setFont(font)
        painter.drawText(size_rect, size_text)

    def sizeHint(self, option, index):
        view = self.parent()
        return view.iconSize() + QSize(2, 14)
