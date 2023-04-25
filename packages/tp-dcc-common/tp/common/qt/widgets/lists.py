#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to create different types of lists
"""

from Qt.QtCore import Qt, Signal, QRect, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QAbstractAnimation
from Qt.QtWidgets import QWidget, QFrame, QPushButton, QLineEdit, QListWidget, QTreeWidget, QListWidgetItem
from Qt.QtWidgets import QAbstractItemView

from tpDcc.libs.qt.widgets import layouts


class EditableList(QTreeWidget):
    """
    List list with editable list items
    """

    itemUpdated = Signal(str, str)
    editing = False

    class EditLine(QLineEdit):
        def __init__(self, *args):
            super(EditableList.EditLine, self).__init__(*args)

        def keyPressEvent(self, event):
            if event.key() == Qt.Key_Escape:
                self.deleteLater()
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.parent().parent().update_item()
            else:
                super(EditableList.EditLine, self).keyPressEvent(event)

    def __init__(self, parent=None):
        super(EditableList, self).__init__(parent=parent)
        self.itemClicked.connect(self._on_click)
        self.itemDoubleClicked.connect(self._on_double_click)

    def update_item(self):
        """
        If an item has been edited we update the list
        """

        i = self.editing
        w = self.itemWidget(i, 0)

        if w and not self.findItems(w.text(), Qt.MatchExactly, 0):
            self.itemUpdated.emit(i.text(0), w.text())
            i.setText(0, w.text())
            self.scrollToItem(i)
            self.editing = False
        if i:
            self.removeItemWidget(i, 0)

    def _on_click(self, item, col):
        if self.editing and item is not self.editing:
            self.update_item()

    def _on_double_click(self, item, col):
        edit = EditableList.EditLine(item.text(0), self)
        self.setItemWidget(item, 0, edit)
        edit.selectAll()
        self.editing = item


class WidgetItem(QFrame, object):

    closed = Signal(QWidget)
    deleted = Signal(QWidget)

    def __init__(self, item_height=150, item_width=300, height_offset=10, width_offset=10,
                 has_title=True, editable_title=True, is_closable=True, parent=None):
        super(WidgetItem, self).__init__(parent=parent)

        self._item_height = item_height
        self._item_width = item_width
        self._height_offset = height_offset
        self._width_offset = width_offset
        self._has_title = has_title
        self._editable_title = editable_title
        self._is_closable = is_closable
        self._animation = None

        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

        self.ui()

    def ui(self):

        self.setLayout(layouts.VerticalLayout(spacing=0, margins=(3, 1, 3, 3)))

        self.main_layout = layouts.VerticalLayout(spacing=5, margins=(2, 2, 2, 2))
        main_widget = QWidget()

        if self._item_height:
            main_widget.setFixedHeight(self._item_height - self._height_offset)
        if self._item_width:
            main_widget.setFixedWidth(self._item_width - self._width_offset)

        main_widget.setLayout(self.main_layout)
        self.layout().addWidget(main_widget)

        # =====================================================

        # This layout is used to add custom widgets before the title of the node
        self.buttons_layout = layouts.VerticalLayout(spacing=2, margins=(2, 2, 2, 2))

        title_layout = layouts.HorizontalLayout()
        title_layout.addLayout(self.buttons_layout)

        title_line = QLineEdit('Untitled')
        if not self._editable_title:
            title_line.setEnabled(False)

        if self._has_title:
            title_layout.addWidget(title_line)

        self._close_btn = QPushButton('X')
        self._close_btn.setFixedHeight(20)
        self._close_btn.setFixedWidth(20)
        self._close_btn.clicked.connect(self.close_widget)
        if self._is_closable:
            title_layout.addWidget(self._close_btn)

        self.main_layout.addLayout(title_layout)

    def hide_close_button(self, value=True):
        self._close_btn.setVisible(not(value))

    def close_widget(self):
        if self._is_closable:
            self.closed.emit(self)

    def delete_widget(self):
        self.deleted.emit(self)

    def _animate_expand(self, value):

        size_anim = QPropertyAnimation(self, 'geometry')
        geometry = self.geometry()
        width = geometry.width()
        x, y, _, _ = geometry.getCoords()
        size_start = QRect(x, y, width, int(not(value)) * 150)
        size_end = QRect(x, y, width, value * 150)
        size_anim.setStartValue(size_start)
        size_anim.setEndValue(size_end)
        size_anim.setDuration(300)
        size_anim_curve = QEasingCurve()
        if value:
            size_anim_curve.setType(QEasingCurve.InQuad)
        else:
            size_anim_curve.setType(QEasingCurve.OutQuad)
        size_anim.setEasingCurve(size_anim_curve)

        # =================================================== Animation Sequence

        self._animation = QSequentialAnimationGroup()
        self._animation.addAnimation(size_anim)
        size_anim.valueChanged.connect(self._force_resize)
        if not value:
            self._animation.finished.connect(self.delete_widget)
        self._animation.start(QAbstractAnimation.DeleteWhenStopped)

    def _force_resize(self, new_height):

        # Force widget item parent to reevaluate its size
        self.setFixedHeight(new_height.height())


class ItemWidgetsList(QListWidget, object):
    def __init__(self, parent=None):
        super(ItemWidgetsList, self).__init__(parent=parent)

        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setFocusPolicy(Qt.NoFocus)

    def addWidget(self, widget):

        item = QListWidgetItem(self)
        item.setSizeHint(widget.sizeHint())
        super(ItemWidgetsList, self).addItem(item)


class WidgetsList(QWidget, object):

    def __init__(self, parent=None):
        super(WidgetsList, self).__init__(parent=parent)

        self._widgets_list = list()

        self.main_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        self.main_layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.main_layout)

        self.widgets_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        self.main_layout.addLayout(self.widgets_layout)

        button_layout = layouts.HorizontalLayout(margins=(5, 5, 5, 5))
        button_layout.setAlignment(Qt.AlignRight)
        self.main_layout.addLayout(button_layout)

        self.add_button = QPushButton('New...', parent=self)
        button_layout.addWidget(self.add_button)

    def add_widget(self, widget):
        self.widgets_layout.addWidget(widget)
        self._widgets_list.append(widget)

        # The first widget of the list cannot be deleted
        if len(self._widgets_list) <= 1:
            self._widgets_list[0].hide_close_button(True)

        # When the close button is pressed we delete the widget
        widget.closed.connect(self.remove_widget)

        widget.setFixedHeight(0)
        widget._animate_expand(True)

    def remove_widget(self, widget):

        # We use try/catch to avoid an error when closing/creating new widgets too quicly in the UI
        widget.deleted.connect(self.delete_widget)
        self._widgets_list.remove(widget)
        widget._animate_expand(False)

    def delete_widget(self, widget):
        self.widgets_layout.removeWidget(widget)
        widget._animation = None
        widget.deleteLater()
