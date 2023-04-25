#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt tab bar widgets
"""

from Qt.QtCore import Qt, Signal, QPoint, QRect, QSize, QEvent, QRegExp, QMimeData
from Qt.QtWidgets import QApplication, QPushButton, QTabBar, QLineEdit, QStyle, QStylePainter, QStyleOptionTab
from Qt.QtGui import QCursor, QPixmap, QPainter, QMouseEvent, QDrag, QRegExpValidator

from tp.core import log
from tp.common.python import name as naming

logger = log.tpLogger

# ======================================================================================================================

nameRegExp = QRegExp('\\w+')

# ======================================================================================================================


class EditableAddButton(QPushButton, object):
    """
    Button that is used in editable tabs to add new tabs
    """

    def __init__(self, parent=None):
        super(EditableAddButton, self).__init__(parent=parent)

        self.setText('+')
        self.setFixedSize(20, 20)

    # def event(self, evt):
    #     if isinstance(evt, QHelpEvent):
    #         pos = evt.pos()
    #         if self.rect().contains(pos):
    #             QToolTip.showText(evt.globalPos(), 'Add Picker:\nClick this to add a new picker')
    #         else:
    #             QToolTip.hideText()
    #     return super(EditableAddButton, self).event(evt)


class EditableTabBar(QTabBar, object):
    """
    Basic implementation of an editable tab bar
    """

    addTabClicked = Signal()
    tabRenamed = Signal(object, object, object)

    def __init__(self, parent=None):
        super(EditableTabBar, self).__init__(parent=parent)

        self._is_editable = True

        self._editor = QLineEdit(self)
        self._editor.setWindowFlags(Qt.Popup)
        self._editor.setFocusProxy(self)
        self._editor.editingFinished.connect(self.handle_editing_finished)
        self._editor.installEventFilter(self)

        self.add_tab_btn = EditableAddButton(parent=self)
        self._move_add_tab_btn()

        self.setDrawBase(False)

        self.add_tab_btn.clicked.connect(self.addTabClicked.emit)

    def is_editable(self):
        """
        Returns whether the tab bar enables rename mode when the user double clicks on the tab
        :return: bool
        """

        return self._is_editable

    def set_is_editable(self, flag):
        """
        Sets whether the tabs are editable or not
        :param flag: bool
        """

        self._is_editable = bool(flag)

    def edit_tab(self, index):
        """
        Function that is called when the tab is going to be edited
        :param index:
        :return:
        """

        if not self._is_editable:
            return

        rect = self.tabRect(index)
        self._editor.setFixedSize(rect.size())
        self._editor.move(self.parent().mapToGlobal(rect.topLeft()))
        self._editor.setText(self.tabText(index))
        self._editor.selectAll()
        if not self._editor.isVisible():
            self._editor.show()

    def handle_editing_finished(self):
        """
        Function that is called when the tab edit has been completed
        """

        index = self.currentIndex()
        if index >= 0:
            self._editor.hide()
            for i in range(self.count()):
                if self.tabText(i) == self._editor.text():
                    logger.warning('Impossible to rename category because exists a tab with the same name!')
                    return
            old_name = self.tabText(index)
            self.setTabText(index, self._editor.text())
            self.tabRenamed.emit(index, self.tabText(index), old_name)

    def sizeHint(self):
        """
        Return the size of the tab bar with increased width for the add tab button
        :return: QSize, size of the tab bar
        """

        size_hint = super(EditableTabBar, self).sizeHint()
        return QSize(size_hint.width() + 25, size_hint.height())

    def resizeEvent(self, event):
        """
        Resize the widget and make sure the add tab button is in the correct location
        """

        super(EditableTabBar, self).resizeEvent(event)
        self._move_add_tab_btn()

    def tabLayoutChange(self):
        """
        This virtual handler is called whenever the tab layout changes.
        If anything changes make sure the add char btn is in the correct location
        """

        super(EditableTabBar, self).tabLayoutChange()
        self._move_add_tab_btn()

    def eventFilter(self, widget, event):
        if ((event.type() == QEvent.MouseButtonPress and not self._editor.geometry().contains(event.globalPos())) or (
                event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape)):
            self._editor.hide()
            return True
        return QTabBar.eventFilter(self, widget, event)

    def mouseDoubleClickEvent(self, event):
        index = self.tabAt(event.pos())
        if index >= 0:
            if not self._is_editable:
                return
            self.edit_tab(index)

    def _move_add_tab_btn(self):

        """
        Move the add tab button to the correct location
        """

        # Find the width of all of the tabs
        size = sum([self.tabRect(i).width() for i in range(self.count())])
        # Set the add tab button location in a visible area
        h = self.geometry().top()
        w = self.width()
        if size > w:
            self.add_tab_btn.move(w - 50, h)
        else:
            self.add_tab_btn.move(size, h)


class TearOffTabBar(QTabBar, object):
    """
    Custom tab bar that allows to drag each tab widget inside it and also to tear off if
    outside the tab widget
    """

    tabDetached = Signal(int, QPoint)      # Signal emitted when a tab is teared off
    tabMoved = Signal(int, int)

    def __init__(self, parent=None):
        super(TearOffTabBar, self).__init__(parent=parent)

        self._select_tab_index = -1

        self.setAcceptDrops(True)
        self.setElideMode(Qt.ElideRight)
        self.setSelectionBehaviorOnRemove(QTabBar.SelectLeftTab)
        self.setMovable(True)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)             # We want to track mouse events even if no buttons are pressed
        self.setIconSize(QSize(12, 12))
        self.setDrawBase(False)

        self._select_tab_index = -1
        self._drag_initiated = False
        self._drag_dropped_pos = QPoint()
        self._drag_start_pos = QPoint()

    def mousePressEvent(self, event):
        """
        Override the behaviour when the mouse is pressed
        """

        self._drag_initiated = False
        self._drag_dropped_pos = QPoint()

        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier:
            self._drag_start_pos = event.pos()

            # Get mouse position and store the area rectangle of the selected tab
            pos = event.pos()
            self._select_tab_index = self.tabAt(pos)
            rect = self.tabRect(self._select_tab_index)

            # Store a pixmap of the selected tab and a pixmap of the close hand cursor image
            # After that we draw the tab and also the hand cursor in the middle of the tab
            pixmap = QPixmap.grabWidget(self, rect)
            painter = QPainter(pixmap)
            cursor_pm = QPixmap(':/icons/close_hand_cursor.png')
            cursor_pos = QPoint(*map(lambda x, y: (x - y) * 0.5, rect.size().toTuple(), cursor_pm.size().toTuple()))
            painter.drawPixmap(cursor_pos, cursor_pm)
            painter.end()

            # Update cursor
            cursor = QCursor(pixmap)
            self.setCursor(cursor)

        super(TearOffTabBar, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Override the behaviour when the mouse is moved
        Doing this we avoid that the tab is moved when tearing off the tab
        """

        if self._select_tab_index < -1:
            pass
        else:
            if event.modifiers() == Qt.ControlModifier:
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

        if not event.buttons() == Qt.LeftButton:
            return

        if not self._drag_start_pos.isNull() and (
                event.pos() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            self._drag_initiated = True

        if (event.buttons() == Qt.LeftButton) and self._drag_initiated and not self.geometry().contains(event.pos()):
            finish_move_event = QMouseEvent(QEvent.MouseMove, event.pos(), Qt.NoButton, Qt.NoButton, Qt.NoModifier)
            super(TearOffTabBar, self).mouseMoveEvent(finish_move_event)

            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setData('action', 'application/tab-detach')
            drag.setMimeData(mime_data)

            rect = self.tabRect(self.tabAt(event.pos()))
            pixmap_big = QPixmap.grabWidget(self.parentWidget().currentWidget()).scaled(640, 480, Qt.KeepAspectRatio)
            drag.setPixmap(pixmap_big)
            drag.setDragCursor(QPixmap(), Qt.LinkAction)

            dragged = drag.exec_(Qt.MoveAction)
            if dragged == Qt.IgnoreAction:
                # moved outside of tab widget
                event.accept()
                self.tabDetached.emit(self.tabAt(self._drag_start_pos), QCursor.pos())
            elif dragged == Qt.MoveAction:
                # moved inside of tab widget
                if not self._drag_dropped_pos.isNull():
                    event.accept()
                    self.tabMoved.emit(self.tabAt(self._drag_start_pos), self.tabAt(self._drag_dropped_pos))
                    self._drag_dropped_pos = QPoint()
        else:
            super(TearOffTabBar, self).mouseMoveEvent(event)

    def enterEvent(self, event):
        """
        When the mouse enters in, the tab bar will receive all keyboards events
        """

        self.grabKeyboard()
        super(TearOffTabBar, self).enterEvent(event)

    def dragEnterEvent(self, event):
        mime_data = event.mimeData()
        formats = mime_data.formats()
        if 'action' in formats and mime_data.data('action') == 'application/tab-detach':
            event.acceptProposedAction()
        super(TearOffTabBar, self).dragEnterEvent(event)

    def dropEvent(self, event):
        self._drag_dropped_pos = event.pos()
        event.acceptProposedAction()
        super(TearOffTabBar, self).dropEvent(event)

    def leaveEvent(self, event):
        """
        When the mouse leaves out, the tab bar will release the own over keyboards events
        """

        self.releaseKeyboard()
        super(TearOffTabBar, self).leaveEvent(event)

    def keyPressEvent(self, event):
        """
        If we press control key while tab bar own keyboard events, we update the cursor
        """

        if event.modifiers() == Qt.ControlModifier:
            self.setCursor(Qt.OpenHandCursor)
        super(TearOffTabBar, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """
        If we release a key while tab bar own keyboard events, we update the cursor
        """

        if self.cursor().shape() != Qt.ArrowCursor:
            self.setCursor(Qt.ArrowCursor)
        super(TearOffTabBar, self).keyReleaseEvent(event)

    # TODO: This was causing to break Maya in some ocassions (specailly after reloading). CHECK WHY!!!!
    # def event(self, event):
    #     """
    #     Override so we can emit the tearOff signal
    #     """
    #
    #     if event.type() == QEvent.MouseButtonRelease:
    #         # self.tabDetached.emit(self._select_tab_index, event.globalPos())
    #
    #         self._select_tab_index = -1
    #         self.setCursor(Qt.ArrowCursor)
    #     return QTabBar.event(self, event)


class EditableTearOffTabBar(TearOffTabBar, object):
    """
    Extended implementation of an editable tab bar with:
        - Rename functionality
        - Tear off functionality
    """

    tab_label_renamed = Signal(str, str)
    request_remove = Signal(int)
    tab_changed = Signal(int)

    def __init__(self, parent=None):
        super(EditableTearOffTabBar, self).__init__(parent=parent)

        self._editor = QLineEdit(self)
        self._editor.setWindowFlags(Qt.Popup)
        self._editor.setFocusProxy(self)
        self._editor.setFocusPolicy(Qt.StrongFocus)
        self._editor.editingFinished.connect(self.handle_editing_finished)
        self._editor.installEventFilter(self)
        self._editor.setValidator(QRegExpValidator(nameRegExp))
        self._edit_index = -1

    def edit_tab(self, index):
        """
        This set the tab in edit mode
        This method is called when double click on the tab
        :param index: int, Index of the tab to be renamed
        """

        # Show the editable line and position it on top of the selected tab
        rect = self.tabRect(index)
        self._editor.setFixedSize(rect.size())
        self._editor.move(self.parent().mapToGlobal(rect.topLeft()))
        self._editor.setText(self.tabText(index))
        if not self._editor.isVisible():
            self._editor.show()
            self._edit_index = index

    def handle_editing_finished(self):
        """
        This finish the edit of the tab name
        """

        # This method only works of we are editing any tab
        if self._edit_index >= 0:
            # Hide the text and update tab text
            self._editor.hide()
            old_text = self.tabText(self.__editIndex)
            new_text = self._editor.text()
            if old_text != new_text:
                names = [self.tabText(i) for i in range(self.count())]
                new_text = naming.get_numeric_name(new_text, names)
                self.setTabText(self._edit_index, new_text)
                self.tab_label_renamed.emit(old_text, new_text)
                self._edit_index = -1

    def eventFilter(self, widget, event):
        """
        If we click (with mouse or keyboard) on registered widgets we hide the editor
        """

        if event.type() == QEvent.MouseButtonPress and not self._editor.geometry().contains(
                event.globalPos()) or event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self._editor.hide()
            return False
        return QTabBar.eventFilter(self, widget, event)


class FingerTabBar(QTabBar, object):
    def __init__(self, *args, **kwargs):
        super(FingerTabBar, self).__init__(*args, **kwargs)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QRect(QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QStyle.CE_TabBarTabLabel, opt)
            painter.restore()

    def tabSizeHint(self, index):
        s = QTabBar.tabSizeHint(self, index)
        s.transpose()
        return s
