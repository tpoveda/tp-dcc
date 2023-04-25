#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets with expandable behaviour
"""

from Qt.QtCore import Qt, Signal, QPoint, QPointF, QRect, QSize, QMimeData, QEvent
from Qt.QtCore import QPropertyAnimation, QParallelAnimationGroup, QAbstractAnimation
from Qt.QtWidgets import QSizePolicy, QWidget, QFrame, QPushButton, QToolButton, QScrollArea, QGroupBox
from Qt.QtGui import QCursor, QPixmap, QIcon, QFont, QColor, QPalette, QPen, QBrush, QPainter, QPolygon, QPolygonF
from Qt.QtGui import QDrag

from tpDcc import dcc
from tpDcc.libs.python import python
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import layouts, label, dividers

if python.is_python2():
    from tpDcc.libs.python.enum import Enum
else:
    from enum import Enum


class PanelState(Enum):
    CLOSED = 0
    OPEN = 1


class ExpandablePanel(base.BaseWidget, object):

    def __init__(self, header_text, min_height=30, max_height=1000,
                 show_header_text=True, is_opened=False, parent=None):

        self._header_text = header_text
        self._show_header_text = show_header_text
        self._min_height = min_height
        self._max_height = max_height

        if is_opened:
            self._panel_state = PanelState.OPEN
        else:
            self._panel_state = PanelState.CLOSED
        self._collapse_icon = QIcon()
        self._icon = QPushButton()
        self._icon.setMaximumSize(20, 20)
        self._icon.setIcon(self._collapse_icon)

        super(ExpandablePanel, self).__init__(parent=parent)

        self.setObjectName('ExpandablePanel')
        self.update_size()
        self.update_icon()

    def ui(self):
        super(ExpandablePanel, self).ui()

        widget_palette = QPalette()
        widget_palette.setColor(QPalette.Background, QColor.fromRgb(60, 60, 60))

        self.setAutoFillBackground(True)
        self.setPalette(widget_palette)

        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Sunken)
        self.main_layout.addWidget(frame)

        main_layout = layouts.VerticalLayout(spacing=0, margins=(2, 2, 2, 2), parent=frame)
        main_layout.setAlignment(Qt.AlignTop)

        self._header_area = QWidget()
        self._header_area.setMinimumHeight(20)
        self._widget_area = QWidget()
        self._widget_area.setAutoFillBackground(True)
        self._widget_area.setPalette(widget_palette)

        self._header_text_label = dividers.Divider(self._header_text)

        self._widget_layout = layouts.VerticalLayout(spacing=5)
        self._widget_layout.setMargin(5)
        self._widget_area.setLayout(self._widget_layout)

        header_layout = layouts.HorizontalLayout(margins=(0, 0, 0, 0))
        header_layout.addWidget(self._icon)
        header_layout.addWidget(self._header_text_label)
        self._header_area.setLayout(header_layout)

        main_layout.addWidget(self._header_area)
        main_layout.addWidget(self._widget_area)

        self._icon.clicked.connect(self.change_state)

    def update_icon(self):

        if self._panel_state == PanelState.OPEN:
            self._icon.setStyleSheet(
                'QLabel {image: url(:/icons/open_hover_collapsible_panel) no-repeat;} '
                'QLabel:hover {image:url(:/icons/open_hover_collapsible_panel) no-repeat;}')
            self._icon.setToolTip('Close')
            self._widget_area.show()
        else:
            self._icon.setStyleSheet(
                'QLabel {image: url(:/icons/closed_collapsible_panel) no-repeat;} '
                'QLabel:hover {image:url(:/icons/closed_hover_collapsible_panel) no-repeat;}')
            self._icon.setToolTip('Open')
            self._widget_area.hide()

    def update_size(self):
        if self._panel_state == PanelState.OPEN:
            self.setMaximumHeight(self._max_height)
            self.setMinimumHeight(self._min_height)
        else:
            self.setMaximumHeight(self._min_height)
            self.setMinimumHeight(self._min_height)

    def change_state(self):

        if not self._show_header_text:
            self._header_text_label.setVisible(False)

        if self._panel_state == PanelState.OPEN:
            self._panel_state = PanelState.CLOSED
            # self._header_text_label.setText('Closed')
            self._widget_area.hide()
        else:
            self._panel_state = PanelState.OPEN
            # self._header_text_label.setText('Open')
            self._widget_area.show()
        self.update_icon()
        self.update_size()

    def add_widget(self, widget):
        self._widget_layout.addWidget(widget)

    def add_layout(self, layout):
        self._widget_layout.addLayout(layout)


class ExpandableLine(QWidget, object):
    def __init__(self, title='', animation_duration=300, parent=None):
        super(ExpandableLine, self).__init__(parent=parent)

        self._animation_duration = animation_duration

        base_layout = layouts.GridLayout(margins=(0, 0, 0, 0))
        base_layout.setVerticalSpacing(0)
        self.setLayout(base_layout)

        self.expand_btn = QToolButton()
        self.expand_btn.setText(str(title))
        self.expand_btn.setStyleSheet('QToolButton { border : none; }')
        self.expand_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.expand_btn.setArrowType(Qt.ArrowType.RightArrow)
        self.expand_btn.setCheckable(True)
        self.expand_btn.setChecked(True)

        header_line = QFrame()
        header_line.setFrameShape(QFrame.HLine)
        header_line.setFrameShadow(QFrame.Sunken)
        header_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.content_area = QScrollArea()
        self.content_area.setStyleSheet('QScrollArea { border: none;}')
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)

        self.toggle_anim = QParallelAnimationGroup()
        self.toggle_anim.addAnimation(QPropertyAnimation(self, 'minimumHeight'))
        self.toggle_anim.addAnimation(QPropertyAnimation(self, 'maximumHeight'))
        self.toggle_anim.addAnimation(QPropertyAnimation(self.content_area, 'maximumHeight'))

        row = 0
        base_layout.addWidget(self.expand_btn, row, 0, 1, 1, Qt.AlignLeft)
        base_layout.addWidget(header_line, row, 2, 1, 1)
        row += 1
        base_layout.addWidget(self.content_area, row, 0, 1, 3)

        def expand_view(checked):
            arrow_type = Qt.DownArrow if checked else Qt.RightArrow
            direction = QAbstractAnimation.Forward if checked else QAbstractAnimation.Backward
            self.expand_btn.setArrowType(arrow_type)
            self.toggle_anim.setDirection(direction)
            self.toggle_anim.start()

        # === SIGNALS === #
        self.expand_btn.toggled.connect(expand_view)

        expand_view(True)

    def set_content_layout(self, content_layout):
        self.content_area.destroy()
        self.content_area.setLayout(content_layout)
        collapsed_height = self.sizeHint().height() - self.content_area.maximumHeight()
        content_height = content_layout.sizeHint().height() + 300
        for i in range(self.toggle_anim.animationCount() - 1):
            expand_anim = self.toggle_anim.animationAt(i)
            expand_anim.setDuration(self._animation_duration)
            expand_anim.setStartValue(collapsed_height)
            expand_anim.setEndValue(collapsed_height + content_height)
        content_anim = self.toggle_anim.animationAt(self.toggle_anim.animationCount() - 1)
        content_anim.setDuration(self._animation_duration)
        content_anim.setStartValue(0)
        content_anim.setEndValue(content_height)


class ExpandableFrame(base.BaseFrame, object):

    def __init__(self, title='', icon=None, parent=None):
        self._is_collapsed = True
        self._title_frame = None
        self._content = None
        self._title = title
        self._icon = icon
        self._content_layout = None

        super(ExpandableFrame, self).__init__(parent=parent)

    def ui(self):
        super(ExpandableFrame, self).ui()

        title_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        self._title_frame = TitleFrame(title=self._title, icon=self._icon, collapsed=self._is_collapsed)
        self._icon_button = label.BaseLabel(parent=self)
        if self._icon:
            self._icon_button.setPixmap(self._icon.pixmap(QSize(20, 20)))
        else:
            self._icon_button.setVisible(False)
        title_layout.addWidget(self._icon_button)
        title_layout.addWidget(self._title_frame)
        title_layout.addStretch()

        self._content = QWidget()
        self._content_layout = layouts.VerticalLayout()
        self._content.setLayout(self._content_layout)
        self._content.setVisible(not self._is_collapsed)

        self.main_layout.addLayout(title_layout)
        self.main_layout.addWidget(self._content)

    def setup_signals(self):
        self._title_frame.clicked.connect(self._on_toggle_collapsed)
        self._icon_button.clicked.connect(self._on_toggle_collapsed)

    def addWidget(self, widget):
        self._content_layout.addWidget(widget)

    def addLayout(self, layout):
        self._content_layout.addLayout(layout)

    def set_title(self, title):
        self._title_frame.set_title(title)

    def _on_toggle_collapsed(self):
        self._content.setVisible(self._is_collapsed)
        self._is_collapsed = not self._is_collapsed
        self._title_frame._arrow.setArrow(self._is_collapsed)


class ExpandableGroup(QGroupBox, object):
    def __init__(self, title='', parent=None):
        super(ExpandableGroup, self).__init__(title, parent)

        self.close_btn = QPushButton('-', self)
        self.close_btn.clicked.connect(self.toggle)

        self.setMouseTracking(True)

        self.setFont(QFont('Verdana', 10, QFont.Bold))
        self.setTitle('     ' + self.title())

        self.expanded = True

        self.hitbox = QRect(0, 0, self.width(), 18)

    def mouseMoveEvent(self, event):
        if self.hitbox.contains(event.pos()):
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if self.hitbox.contains(event.pos()):
            self.toggle()

    def wheelEvent(self, event):
        (self.collapse, self.expand)[event.delta() > 0]()

    def resizeEvent(self, event):
        self.hitbox = QRect(0, 0, self.width(), 18)
        self.close_btn.setGeometry(6, 1, 18, 18)

    def expand(self):
        """
        Expands the group
        """

        self.toggle(False)

    def collapse(self):
        """
        Collapses the group
        """

        self.toggle(True)

    def toggle(self, force=-1):
        """
        Toggle group expand/collapse state
        :param force: int, if we want a specific state to be applied
        """

        state = self.expanded if force == -1 else force

        p = [c for c in self.children() if c is not self.close_btn]
        widgets = list()
        i = 0

        while i < len(p):
            try:
                p[i].isVisible()
                widgets.append(p[i])
            except AttributeError:
                # We have hit a layout ...
                p.extend(p[i].children())
            i += 1

        # toggle visibility
        for c in widgets:
            c.setVisible(not state)

        self.close_btn.setText('-+'[state])
        self.expanded = not state


class TitleFrame(QFrame, object):

    clicked = Signal()

    def __init__(self, title='', icon=None, collapsed=False, parent=None):
        super(TitleFrame, self).__init__(parent=parent)

        self.setMinimumHeight(24)
        # self.move(QPoint(24, 0))
        # self.setStyleSheet('border 1px solid rgb(41, 41, 41);') CHANGED

        layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(layout)

        self._arrow = ExpandableArrow(collapsed=collapsed)
        # self._arrow.setStyleSheet('border:0px;') CHANGED

        self._title = label.BaseLabel(title, parent=self).strong()
        self._title.setMinimumHeight(24)
        # self._title.move(QPoint(24, 0))
        # self._title.setStyleSheet('border: 0px;') CHANGED

        layout.addWidget(self._arrow)
        layout.addWidget(self._title)

    def mousePressEvent(self, event):
        self.clicked.emit()
        return super(TitleFrame, self).mousePressEvent(event)

    def set_title(self, title):
        self._title.setText(title)


class ExpandableArrow(QFrame):
    def __init__(self, collapsed=False, parent=None):
        super(ExpandableArrow, self).__init__(parent=parent)
        self.setMaximumSize(24, 24)
        self.setMinimumWidth(24)

        self._arrow = None

        # Define vertical and horizontal arrow to avoid the deletion of its items during garbage collection
        # (this gc produces errors when trying to paint the arrow if we do not save them in a local variable
        self._arrow = None
        self._vertical = QPolygonF([QPointF(8.0, 7.0), QPointF(13.0, 12.0), QPointF(8.0, 17.0)])
        self._horizontal = QPolygonF([QPointF(7.0, 8.0), QPointF(17.0, 8.0), QPointF(12.0, 13.0)])

        self.setArrow(bool(collapsed))

    def setArrow(self, collapsed):
        if collapsed is True:
            self._arrow = self._vertical
        else:
            self._arrow = self._horizontal

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setBrush(QColor(192, 192, 192))
        painter.setPen(QColor(64, 64, 64))
        painter.drawPolygon(self._arrow)
        painter.end()


class ExpanderStyles(object):
    Boxed = 0
    Rounded = 1
    Square = 2
    Maya = 3


class ExpanderDragDropModes(object):
    NoDragDrop = 0
    InternalMove = 1


class ExpanderItem(QGroupBox, object):
    def __init__(self, expander, title, widget):
        super(ExpanderItem, self).__init__(expander)

        self._expanderWidget = expander
        self._rolloutStyle = ExpanderStyles.Rounded
        self._dragDropMode = ExpanderDragDropModes.NoDragDrop
        self._widget = widget
        self._collapsed = False
        self._collapsible = True
        self._clicked = False
        self._customData = dict()
        self._margin = 2

        layout = layouts.VerticalLayout(spacing=0, margins=(2, 2, 2, 2))
        layout.addWidget(widget)
        self.setAcceptDrops(True)
        self.setLayout(layout)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setTitle(title)

    # ====================================================================================

    def dragEnterEvent(self, event):
        if not self._dragDropMode:
            return
        source = event.source()
        if source and source != self and source.parent() == self.parent() and isinstance(source, ExpanderItem):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if not self._dragDropMode:
            return
        source = event.source()
        if source != self and source.parent() == self.parent() and isinstance(source, ExpanderItem):
            event.acceptProposedAction()

    def dropEvent(self, event):
        widget = event.source()
        layout = self.parent().layout()
        layout.insertWidget(layout.indexOf(self), widget)
        self._expanderWidget.emitItemsReordered()

    def enterEvent(self, event):
        self.expanderWidget().enterEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._clicked and self.expandCollapseRect().contains(event.pos()):
            self.toggleCollapsed()
            event.accept()
        else:
            event.ignore()
        self._clicked = False

    def mouseMoveEvent(self, event):
        event.ignore()

    def mousePressEvent(self, event):
        if self.dragDropMode() and event.button() == Qt.LeftButton and self.dragDropRect().contains(event.pos()):
            pixmap = QPixmap.grabWidget(self, self.rect())
            mimeData = QMimeData()
            mimeData.setText('ItemTitle::%s' % self.title())
            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            if not drag.exec_():
                self._expanderWidget.emitItemDragFailed(self)
            event.accept()
        elif event.button() == Qt.LeftButton and self.expandCollapseRect().contains(event.pos()):
            self._clicked = True
            event.accept()
        else:
            event.ignore()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(painter.Antialiasing)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        x = self.rect().x()
        y = self.rect().y()
        w = self.rect().width() - 1
        h = self.rect().height() - 1
        _rect = 8
        if self._rolloutStyle == ExpanderStyles.Rounded:
            painter.drawText(x + 33, y + 3, w, 16, Qt.AlignLeft | Qt.AlignTop, self.title())
            self.__drawTriangle(painter, x, y)
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.6)
            painter.setPen(pen)
            painter.drawRoundedRect(x + 1, y + 1, w - 1, h - 1, _rect, _rect)
            pen.setColor(self.palette().color(QPalette.Shadow))
            painter.setPen(pen)
            painter.drawRoundedRect(x, y, w - 1, h - 1, _rect, _rect)
        if self._rolloutStyle == ExpanderStyles.Square:
            painter.drawText(x + 33, y + 3, w, 16, Qt.AlignLeft | Qt.AlignTop, self.title())
            self.__drawTriangle(painter, x, y)
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.2)
            painter.setPen(pen)
            painter.drawRect(x + 1, y + 1, w - 1, h - 1)
            pen.setColor(self.palette().color(QPalette.Shadow))
            painter.setPen(pen)
            painter.drawRect(x, y, w - 1, h - 1)
        if self._rolloutStyle == ExpanderStyles.Maya:
            painter.drawText(
                x + (45 if self.dragDropMode() == ExpanderDragDropModes.InternalMove else 25),
                y + 3, w, 16, Qt.AlignLeft | Qt.AlignTop, self.title())
            painter.setRenderHint(QPainter.Antialiasing, False)
            self.__drawTriangle(painter, x, y)
            header_height = 20
            header_rect = QRect(x + 1, y + 1, w - 1, header_height)
            header_rect_shadow = QRect(x - 1, y - 1, w + 1, header_height + 2)
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.4)
            # painter.setPen(pen)
            painter.setPen(Qt.NoPen)
            painter.drawRect(header_rect)
            painter.fillRect(header_rect, QColor(255, 255, 255, 18))
            pen.setColor(self.palette().color(QPalette.Dark))
            painter.setPen(pen)
            painter.drawRect(header_rect_shadow)
            if not self.isCollapsed():
                # pen = QPen(self.palette().color(QPalette.Background))
                # painter.setPen(pen)
                offset = header_height + 3
                body_rect = QRect(x, y + offset, w, h - offset)
                # body_rect_shadow = QRect(x + 1, y + offSet, w + 1, h - offSet + 1)
                painter.drawRect(body_rect)
                # pen.setColor(self.palette().color(QPalette.Foreground))
                # pen.setWidthF(0.4)
                # painter.setPen(pen)
                # painter.drawRect(body_rect_shadow)
        elif self._rolloutStyle == ExpanderStyles.Boxed:
            if self.isCollapsed():
                arect = QRect(x + 1, y + 9, w - 1, 4)
                brect = QRect(x, y + 8, w - 1, 4)
                text = '+'
            else:
                arect = QRect(x + 1, y + 9, w - 1, h - 9)
                brect = QRect(x, y + 8, w - 1, h - 9)
                text = '-'
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.6)
            painter.setPen(pen)
            painter.drawRect(arect)
            pen.setColor(self.palette().color(QPalette.Shadow))
            painter.setPen(pen)
            painter.drawRect(brect)
            painter.setRenderHint(painter.Antialiasing, False)
            painter.setBrush(self.palette().color(QPalette.Window).darker(120))
            painter.drawRect(x + 10, y + 1, w - 20, 16)
            painter.drawText(x + 16, y + 1, w - 32, 16, Qt.AlignLeft | Qt.AlignVCenter, text)
            painter.drawText(x + 10, y + 1, w - 20, 16, Qt.AlignCenter, self.title())
        if self.dragDropMode():
            rect = self.dragDropRect()
            _layout = rect.left()
            _rect = rect.right()
            center_y = rect.center().y()
            pen = QPen(self.palette().color(self.isCollapsed() and QPalette.Shadow or QPalette.Mid))
            painter.setPen(pen)
            for y in (center_y - 3, center_y, center_y + 3):
                painter.drawLine(_layout, y, _rect, y)
        painter.end()

    # ====================================================================================

    def showMenu(self):
        if QRect(0, 0, self.width(), 20).contains(self.mapFromGlobal(QCursor.pos())):
            self._expanderWidget.emitItemMenuRequested(self)

    def toggleCollapsed(self):
        self.setCollapsed(not self.isCollapsed())

    # ====================================================================================

    def widget(self):
        return self._widget

    def expanderWidget(self):
        return self._expanderWidget

    def customData(self, key, default=None):
        return self._customData.get(str(key), default)

    def setCustomData(self, key, value):
        self._customData[str(key)] = value

    def dragDropRect(self):
        return QRect(21, 8, 10, 6)

    def dragDropMode(self):
        return self._dragDropMode

    def setDragDropMode(self, mode):
        self._dragDropMode = mode

    def expandCollapseRect(self):
        return QRect(0, 0, self.width(), 20)

    def rolloutStyle(self):
        return self._rolloutStyle

    def margin(self):
        return self._margin

    def setMargin(self, margin):
        self._margin = margin
        self.setRolloutStyle(self.rolloutStyle())

    def rolloutStyle(self):
        return self._rolloutStyle

    def setRolloutStyle(self, style):
        self._rolloutStyle = style
        m = self.margin()
        if style == ExpanderStyles.Maya:
            self.layout().setContentsMargins(m, m + 9, m, m)
        else:
            self.layout().setContentsMargins(m, m, m, m)

    def isCollapsible(self):
        return self._collapsible

    def setCollapsible(self, state=True):
        self._collapsible = state

    def isCollapsed(self):
        return self._collapsed

    def setCollapsed(self, state=True):
        if self.isCollapsible():
            expander = self.expanderWidget()
            expander.setUpdatesEnabled(False)
            self._collapsed = state
            if state:
                self.setMinimumHeight(22)
                self.setMaximumHeight(22)
                self.widget().setVisible(False)
            else:
                self.setMinimumHeight(0)
                self.setMaximumHeight(1000000)
                self.widget().setVisible(True)
            self._expanderWidget.emitItemCollapsed(self)
            expander.setUpdatesEnabled(True)

    def __drawTriangle(self, painter, x, y):
        if self.rolloutStyle() == ExpanderStyles.Maya:
            brush = QBrush(QColor(255, 0, 0, 160), Qt.SolidPattern)
        else:
            brush = QBrush(QColor(255, 255, 255, 160), Qt.SolidPattern)
        if not self.isCollapsed():
            tl, tr, tp = QPoint(x + 9, y + 8), QPoint(x + 19, y + 8), QPoint(x + 14, y + 13)
            points = [tl, tr, tp]
            triangle = QPolygon(points)
        else:
            tl, tr, tp = QPoint(x + 11, y + 5), QPoint(x + 16, y + 10), QPoint(x + 11, y + 15)
            points = [tl, tr, tp]
            triangle = QPolygon(points)
        currentPen = painter.pen()
        currentBrush = painter.brush()
        painter.setPen(Qt.NoPen)
        painter.setBrush(brush)
        painter.drawPolygon(triangle)
        painter.setPen(currentPen)
        painter.setBrush(currentBrush)


class ExpanderWidget(QScrollArea, object):
    itemCollapsed = Signal(ExpanderItem)
    itemMenuRequested = Signal(ExpanderItem)
    itemDragFailed = Signal(ExpanderItem)
    itemsReordered = Signal()

    def __init__(self, parent=None):
        super(ExpanderWidget, self).__init__(parent=parent)

        self._rolloutStyle = ExpanderStyles.Maya if dcc.client().is_maya() else ExpanderStyles.Square
        self._dragDropMode = ExpanderDragDropModes.NoDragDrop
        self._scrolling = False
        self._scrollInitY = 0
        self._scrollInitVal = 0
        self._itemClass = ExpanderItem

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setAutoFillBackground(False)
        self.setWidgetResizable(True)
        self.setMouseTracking(True)
        widget = QWidget(self)
        layout = layouts.VerticalLayout(spacing=2, margins=(2, 2, 2, 2))
        layout.setAlignment(Qt.AlignTop)
        widget.setLayout(layout)
        self.setWidget(widget)

    # ====================================================================================

    def addItem(self, title, widget, collapsed=False):
        self.setUpdatesEnabled(False)
        item = self.itemClass()(self, title, widget)
        item.setRolloutStyle(self.rolloutStyle())
        item.setDragDropMode(self.dragDropMode())
        layout = self.widget().layout()
        layout.insertWidget(layout.count() - 1, item)
        layout.setStretchFactor(item, 0)
        if collapsed:
            item.setCollapsed(collapsed)
        self.setUpdatesEnabled(True)
        return item

    def clear(self):
        self.setUpdatesEnabled(False)
        layout = self.widget().layout()
        while layout.count() > 1:
            item = layout.itemAt(0)
            w = item.widget()
            layout.removeItem(item)
            w.close()
            w.deleteLater()

    # ====================================================================================

    def eventFilter(self, obj, event):
        if not event:
            return False

        if event.type() == QEvent.MouseButtonPress:
            self.mousePressEvent(event)
            return True
        if event.type() == QEvent.MouseMove:
            self.mouseMoveEvent(event)
            return True
        if event.type() == QEvent.MouseButtonRelease:
            self.mouseReleaseEvent(event)
            return True
        return False

    def mouseMoveEvent(self, event):
        if self._scrolling:
            sbar = self.verticalScrollBar()
            smax = sbar.maximum()
            dy = event.globalY() - self._scrollInitY
            dval = smax * (dy / float(sbar.height()))
            sbar.setValue(self._scrollInitVal - dval)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.canScroll():
            self._scrolling = True
            self._scrollInitY = event.globalY()
            self._scrollInitVal = self.verticalScrollBar().value()
            self.setCursor(Qt.ClosedHandCursor)
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._scrolling:
            self.setCursor(Qt.ArrowCursor)
        self._scrolling = False
        self._scrollInitY = 0
        self._scrollInitVal = 0
        event.accept()

    # ====================================================================================

    def moveItemDown(self, index):
        layout = self.widget().layout()
        if layout.count() - 1 > index + 1:
            widget = layout.takeAt(index).widget()
            layout.insertWidget(index + 1, widget)

    def moveItemUp(self, index):
        if index > 0:
            layout = self.widget().layout()
            widget = layout.takeAt(index).widget()
            layout.insertWidget(index - 1, widget)

    def rolloutStyle(self):
        return self._rolloutStyle

    def set_rollout_style(self, rolloutStyle):
        self._rolloutStyle = rolloutStyle
        for item in self.findChildren(ExpanderItem):
            item.set_rollout_style(self._rolloutStyle)

    def itemClass(self):
        return self._itemClass

    def setItemClass(self, itemClass):
        self._itemClass = itemClass

    def canScroll(self):
        return self.verticalScrollBar().maximum() > 0

    def count(self):
        return self.widget().layout().count() - 1

    def dragDropMode(self):
        return self._dragDropMode

    def setDragDropMode(self, dragDropMode):
        self._dragDropMode = dragDropMode
        for item in self.findChildren(ExpanderItem):
            item.setDragDropMode(self._dragDropMode)

    def indexOf(self, widget):
        layout = self.widget().layout()
        for index in range(layout.count()):
            if layout.itemAt(index).widget().widget() == widget:
                return index
        return -1

    def itemAt(self, index):
        layout = self.widget().layout()
        if 0 <= index and index < layout.count() - 1:
            return layout.itemAt(index).widget()
        else:
            return None

    def takeAt(self, index):
        self.setUpdatesEnabled(False)
        layout = self.widget().layout()
        widget = None
        if 0 <= index and index < layout.count() - 1:
            item = layout.itemAt(index)
            widget = item.widget()
            layout.removeItem(item)
            widget.close()
        self.setUpdatesEnabled(True)
        return widget

    def widgetAt(self, index):
        item = self.itemAt(index)
        if item:
            return item.widget()
        else:
            return None

    def isBoxedMode(self):
        return self._rolloutStyle == ExpanderStyles.Boxed

    def setBoxedMode(self, state):
        if state:
            self._rolloutStyle = ExpanderStyles.Boxed
        else:
            self._rolloutStyle = ExpanderStyles.Rounded

    def setSpacing(self, space):
        self.widget().layout().setSpacing(space)

    def setMargin(self, margin):
        if isinstance(margin, int):
            self.widget().layout().setContentsMargins(margin, margin, margin, margin)
        elif isinstance(margin, list) and len(margin) == 4:
            self.widget().layout().setContentsMargins(*margin)

    # ====================================================================================

    def emitItemCollapsed(self, item):
        if not self.signalsBlocked():
            self.itemCollapsed.emit(item)

    def emitItemDragFailed(self, item):
        if not self.signalsBlocked():
            self.itemDragFailed.emit(item)

    def emitItemMenuRequested(self, item):
        if not self.signalsBlocked():
            self.itemMenuRequested.emit(item)

    def emitItemsReordered(self):
        if not self.signalsBlocked():
            self.itemsReordered.emit()
