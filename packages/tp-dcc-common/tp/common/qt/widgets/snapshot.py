#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget implementation for taking snapshots
"""

import os
import logging

from Qt.QtCore import Qt, Signal, QPoint, QRect, QSize
from Qt.QtWidgets import QSizePolicy, QWidget, QFrame
from Qt.QtGui import QResizeEvent

from tpDcc.dcc import window
from tpDcc.managers import resources
from tpDcc.libs.python import fileio, path as path_utils, folder as folder_utils
from tpDcc.libs.qt.core import qtutils
from tpDcc.libs.qt.widgets import layouts, label, lineedit, buttons

LOGGER = logging.getLogger('tpDcc-libs-qt')


class SnapshotWindow(window.Window(as_class=True), object):
    saved = Signal(str)

    def __init__(self, path=None, image_type='png', width=512, height=512, on_save=None, parent=None):

        self._default_width = width
        self._default_height = height
        self._save_path = path
        self._image_type = image_type
        self._keep_aspect = True
        self._locked = False
        self._last_saved_location = None

        super(SnapshotWindow, self).__init__(title='Snapshot', height=height, width=width, parent=parent)

        if on_save:
            self.saved.connect(on_save)

        self.set_snapshot_size(width, height)

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout(spacing=0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(SnapshotWindow, self).ui()

        camera_icon = resources.icon('camera')
        cancel_icon = resources.icon('delete')
        self._link_icon = resources.icon('link')
        self._unlink_icon = resources.icon('unlink')
        self._lock_icon = resources.icon('lock')
        self._unlock_icon = resources.icon('unlock')

        self.window().setWindowFlags(self.window().windowFlags() | Qt.WindowStaysOnTopHint)

        self._setup_dragger()
        self.main_widget.setStyleSheet('WindowContents { background-color: transparent; }')

        snap_layout = layouts.HorizontalLayout(spacing=0)

        self._snap_widget = QWidget()
        self._snap_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_panel = SnapshotFrame(self)
        left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        left_panel.setFixedWidth(qtutils.dpi_scale(5))
        right_panel = SnapshotFrame(self)
        right_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        right_panel.setFixedWidth(qtutils.dpi_scale(5))
        snap_layout.addWidget(left_panel)
        snap_layout.addWidget(self._snap_widget, stretch=1)
        snap_layout.addWidget(right_panel)

        buttom_layout = layouts.HorizontalLayout(margins=(5, 5, 5, 5))
        self._bottom_bar = SnapshotFrame(self)
        self._bottom_bar.setLayout(buttom_layout)
        self._bottom_bar.setFixedHeight(qtutils.dpi_scale(33))

        self._image_size_lbl = label.BaseLabel('Image Size')
        qtutils.set_horizontal_size_policy(self._image_size_lbl, QSizePolicy.Ignored)
        self._image_size_lbl.setMaximumWidth(self._image_size_lbl.sizeHint().width())
        self._width_line = lineedit.BaseLineEdit(input_mode='int')
        self._width_line.setMinimumWidth(qtutils.dpi_scale(19))
        qtutils.set_size_hint(self._width_line, qtutils.size_by_dpi(QSize(40, self._width_line.sizeHint().height())))
        self._height_line = lineedit.BaseLineEdit(input_mode='int')
        self._height_line.setMinimumHeight(qtutils.dpi_scale(19))
        qtutils.set_size_hint(self._height_line, qtutils.size_by_dpi(QSize(40, self._height_line.sizeHint().height())))
        self._aspect_link_button = buttons.BaseToolButton()
        self._aspect_link_button.setIcon(self._link_icon)
        self._aspect_link_button.setCheckable(True)
        self._aspect_link_button.setMinimumWidth(qtutils.dpi_scale(24))
        self._aspect_link_button.setChecked(True)
        self._lock_button = buttons.BaseToolButton()
        self._lock_button.setCheckable(True)
        self._lock_button.setIcon(self._unlock_icon)
        self._snapshot_button = buttons.BaseButton('Snapshot', camera_icon)
        self._snapshot_button.setMaximumWidth(self._snapshot_button.sizeHint().width())
        self._cancel_button = buttons.BaseButton('Cancel', cancel_icon)
        qtutils.set_horizontal_size_policy(self._cancel_button, QSizePolicy.Ignored)
        self._cancel_button.setMaximumWidth(self._cancel_button.sizeHint().width())

        self._cancel_button.setMinimumWidth(qtutils.dpi_scale(24))

        buttom_layout.addWidget(self._image_size_lbl, 4)
        buttom_layout.addWidget(self._width_line)
        buttom_layout.addWidget(self._aspect_link_button)
        buttom_layout.addWidget(self._height_line)
        buttom_layout.addWidget(self._lock_button)
        buttom_layout.addStretch()
        buttom_layout.addWidget(self._snapshot_button, 3)
        buttom_layout.addWidget(self._cancel_button, 3)

        self.main_layout.addLayout(snap_layout)
        self.main_layout.addWidget(self._bottom_bar)

        self.window().setMinimumSize(98, 142)

    def setup_signals(self):
        [r.windowResized.connect(self._on_window_resize) for r in self.get_horizontal_resizers()]
        [r.windowResized.connect(self._on_vertical_resize) for r in self.get_vertical_resizers()]
        [r.windowResized.connect(self._on_window_resize) for r in self.get_corner_resizers()]
        self._width_line.editingFinished.connect(self._on_size_edit_changed)
        self._height_line.editingFinished.connect(self._on_size_edit_changed)
        self._aspect_link_button.clicked.connect(self._on_toggle_aspect)
        self._lock_button.clicked.connect(self._on_toggle_lock)
        self._snapshot_button.clicked.connect(self.snapshot)
        self._cancel_button.clicked.connect(self.fade_close)

    def showEvent(self, event):
        super(SnapshotWindow, self).showEvent(event)

        if hasattr(self, '_snap_widget'):
            self.set_snapshot_size(512, 512)
            qtutils.process_ui_events()
            self._update_widgets()
            self.resizeEvent(QResizeEvent(self.size(), self.size()))

    def resizeEvent(self, event):
        super(SnapshotWindow, self).resizeEvent(event)

        widgets_to_hide = ((self._image_size_lbl, 250), (self._lock_button, 240),
                           (self._aspect_link_button, 185), (self._cancel_button, 155))
        for widget, size in widgets_to_hide:
            widget.setVisible(self.width() > qtutils.dpi_scale(size))

        spacer_threshold = 120

        self._bottom_bar.layout().setSpacing(0) if self.width() < spacer_threshold else \
            self._bottom_bar.layout().setSpacing(6)

    def set_save_path(self, file_path):
        """
        Sets the path where snapshot will be saved
        :param file_path: str
        """

        self._save_path = file_path

    def set_snapshot_size(self, width, height):
        """
        Sets the size of the snapshot widget
        :param width: int
        :param height: int
        """

        width_offset = self._get_width_offset()
        height_offset = self._get_height_offset()

        if self._keep_aspect:
            if self.sender() == self._width_line:
                self.window().resize(width + width_offset, width + height_offset)
            elif self.sender() == self._height_line:
                self.window().resize(height + width_offset, height + height_offset)
            else:
                self.window().resize(width + width_offset, width + height_offset)
        else:
            self.window().resize(width + width_offset, height + height_offset)

        self._update_widgets()

    def snapshot(self):
        """
        Takes snapshot
        """

        if not self._save_path:
            LOGGER.error('Path not specificed for snapshot.')
            return

        rect = QRect(self._snap_widget.rect())
        pos = self._snap_widget.mapToGlobal(QPoint(0, 0))
        rect.translate(pos.x(), pos.y())
        self.setWindowOpacity(0)
        self._snapshot_pixmap = qtutils.desktop_pixmap_from_rect(rect)
        dir_path = os.path.dirname(self._save_path)
        if not os.path.exists(os.path.dirname(dir_path)):
            os.makedirs(dir_path)

        self.save(self._save_path, self._image_type)

        self.close()

    def save(self, file_path, image_type='png'):
        """
        Saves screen to a file
        :param file_path: str, path to save image into
        :param image_type: str, image type (png or jpg)
        """

        saved = None
        if not file_path:
            LOGGER.error('Path not specificed for snapshot.')
            self.saved.emit(saved)
            return
        file_dir, file_name, file_ext = path_utils.split_path(file_path)
        if not os.path.isdir(file_dir):
            folder_utils.create_folder(file_dir)
        else:
            if os.path.isfile(file_path):
                fileio.delete_file(file_path)

        image_type = image_type if image_type.startswith('.') else '.{}'.format(image_type)
        if image_type != file_ext:
            if file_ext not in ('.png', '.jpg'):
                LOGGER.warning('Image of type "{}" is not supported by snapshot!'.format(file_ext))
                return
            image_type = file_ext

        if image_type.startswith('.'):
            image_type = image_type[1:]
        image_type = image_type.upper()

        saved = self._snapshot_pixmap.save(file_path, image_type)
        self._last_saved_location = file_path
        self.saved.emit(file_path if saved else None)

    def _setup_dragger(self):
        """
        Internal function that setup window dragger
        :return:
        """

        self._dragger.set_minimize_enabled(False)
        self._dragger.set_maximized_enabled(False)
        self._dragger.set_height(20)
        self._dragger.hide_logo()

    def _get_width_offset(self):
        return self.window().size().height() - self._snap_widget.height()

    def _get_height_offset(self):
        return self.window().size().width() - self._snap_widget.width()

    def _get_bottom_size(self):
        return self._bottom_bar.height() + self._bottom_resizer.height() + qtutils.dpi_scale(2)

    def _update_widgets(self):
        self._width_line.blockSignals(True)
        self._height_line.blockSignals(True)
        try:
            self._width_line.setText(str(self._snap_widget.width()))
            self._height_line.setText(str(self._snap_widget.height()))
            self.setFocus()
        finally:
            self._width_line.blockSignals(False)
            self._height_line.blockSignals(False)

    def _on_toggle_aspect(self):
        """
        Internal callback function that is called when toggle aspect ratio button is clicked by the user
        """

        self._keep_aspect = not self._keep_aspect
        if self._keep_aspect:
            self._aspect_link_button.setIcon(self._link_icon)
            self.window().resize(
                self.window().height() + self._get_width_offset(), self.window().height() + self._get_height_offset())
            self._update_widgets()
        else:
            self._aspect_link_button.setIcon(self._unlink_icon)

    def _on_toggle_lock(self):
        """
        Internal callback function that is called when the lock button is clicked by the user
        """

        self._locked = not self._locked
        if self._locked:
            self.set_resizers_enabled(False)
            self._lock_button.setIcon(self._lock_icon)
            self._lock_button.setChecked(True)
            self._width_line.setEnabled(False)
            self._height_line.setEnabled(False)
            self._aspect_link_button.setEnabled(False)
        else:
            self.set_resizers_enabled(True)
            self._lock_button.setIcon(self._unlock_icon)
            self._lock_button.setChecked(False)
            self._width_line.setEnabled(True)
            self._height_line.setEnabled(True)
            self._aspect_link_button.setEnabled(True)

    def _on_window_resize(self):
        """
        Internal callback function that is called when window is resized in width or through the corners
        """

        if self._keep_aspect:
            self.window().resize(self.window().width(), self.window().width() + self._get_bottom_size())
        self._update_widgets()

    def _on_vertical_resize(self):
        """
        Internal callback function that is called when window is resized vertically
        """

        if self._keep_aspect:
            self.window().resize(self.window().height() - self._get_bottom_size(), self.window().height())
        self._update_widgets()

    def _on_size_edit_changed(self):
        """
        Internal callback function that is called when height/width line edit values are changed
        """

        if self._locked or (self.sender() is not None and self.sender().signalsBlocked()):
            return

        width = int(self._width_line.text())
        height = int(self._height_line.text())
        self.set_snapshot_size(width, height)


class SnapshotFrame(QFrame, object):
    pass
