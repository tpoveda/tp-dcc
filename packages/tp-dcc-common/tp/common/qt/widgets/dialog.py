#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains extended Qt dialog classes
"""

import os
import string
import getpass
from functools import partial

from Qt.QtCore import Qt, Signal, QSize, QRectF, QFileInfo, QDir
from Qt.QtWidgets import QApplication, QGroupBox, QDesktopWidget, QDialog, QStatusBar, QSizePolicy, QGraphicsView
from Qt.QtWidgets import QGraphicsScene, QFileIconProvider, QListWidgetItem, QMessageBox, QInputDialog
from Qt.QtWidgets import QWidget, QLabel, QFrame, QPushButton, QSlider, QLineEdit, QComboBox, QCheckBox, QRadioButton

from tp.core import dcc
from tp.core.managers import resources
from tp.core.abstract import dialog as abstract_dialog
# from tp.common.resources import theme
from tp.common.qt import qtutils, animation, dragger, resizers
from tp.common.qt.widgets import layouts, dividers


class BaseDialog(QDialog, abstract_dialog.AbstractDialog):
    """
    Class to create basic Maya docked windows
    """

    dialogResizedFinished = Signal()
    closed = Signal()
    themeUpdated = Signal(object)
    styleReloaded = Signal(object)

    def __init__(self, **kwargs):

        parent = kwargs.get('parent', None) or dcc.get_main_window()
        super(BaseDialog, self).__init__(parent=parent)

        self._setup_resizers()

        title = kwargs.get('title', '')
        name = kwargs.get('name', title or self.__class__.__name__)
        width = kwargs.get('width', 600)
        height = kwargs.get('height', 800)
        show_on_initialize = kwargs.get('show_on_initialize', False)
        self._theme = None
        self._dpi = kwargs.get('dpi', 1.0)
        self._fixed_size = kwargs.get('fixed_size', False)
        self._has_title = kwargs.pop('has_title', False)
        self._size = kwargs.pop('size', (200, 125))
        self._title_pixmap = kwargs.pop('title_pixmap', None)
        self._toolset = kwargs.get('toolset', None)

        self.setObjectName(str(name))
        self.setFocusPolicy(Qt.StrongFocus)

        frameless = kwargs.get('frameless', True)
        self.set_frameless(frameless)

        self.ui()
        self.setup_signals()

        self._status_bar = QStatusBar(self)
        self.main_layout.addWidget(self._status_bar)
        if self._fixed_size:
            self._status_bar.hide()
        self._status_bar.hide()

        self.setWindowTitle(title)

        auto_load = kwargs.get('auto_load', True)
        if auto_load:
            self.load_theme()

        if show_on_initialize:
            self.center()
            self.show()

        if self._toolset:
            self.main_layout.addWidget(self._toolset)

        self.resize(width, height)

    def default_settings(self):
        """
        Returns default settings values
        :return: dict
        """

        return {
            "theme": {
                "accentColor": "rgb(80, 80, 80, 255)",
                "backgroundColor": "rgb(45, 45, 45, 255)",
            }
        }

    def load_theme(self):
        def_settings = self.default_settings()
        theme_settings = def_settings.get('theme', dict())

        self.set_theme_settings(theme_settings)

    def set_width_height(self, width, height):
        """
        Sets the width and height of the dialog
        :param width: int
        :param height: int
        """

        x = self.geometry().x()
        y = self.geometry().y()
        self.setGeometry(x, y, width, height)

    def is_frameless(self):
        """
        Returns whether or not frameless functionality for this window is enable or not
        :return: bool
        """

        return self.window().windowFlags() & Qt.FramelessWindowHint == Qt.FramelessWindowHint

    def set_frameless(self, flag):

        window = self.window()

        if flag and not self.is_frameless():
            window.setAttribute(Qt.WA_TranslucentBackground)
            if qtutils.is_pyside2() or qtutils.is_pyqt5():
                window.setWindowFlags(window.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            else:
                window.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.set_resizer_active(True)
        elif not flag and self.is_frameless():
            window.setAttribute(Qt.WA_TranslucentBackground)
            if qtutils.is_pyside2() or qtutils.is_pyqt5():
                window.setWindowFlags(window.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            else:
                self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.set_resizer_active(False)

        # window.show()
        #
        # if self._frameless:
        #     self.setAttribute(Qt.WA_TranslucentBackground)
        #     if qtutils.is_pyside2():
        #         self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        #     else:
        #         self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

    def center(self, to_cursor=False):
        """
        Move the dialog to the center of the current window
        """

        frame_geo = self.frameGeometry()
        if to_cursor:
            pos = QApplication.desktop().cursor().pos()
            screen = QApplication.desktop().screenNumber(pos)
            center_point = QApplication.desktop().screenGeometry(screen).center()
        else:
            center_point = QDesktopWidget().availableGeometry().center()
        frame_geo.moveCenter(center_point)
        self.move(frame_geo.topLeft())

    def fade_close(self):
        animation.fade_window(start=1, end=0, duration=400, object=self, on_finished=self.close)

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout(spacing=0, margins=(2, 2, 2, 2))
        return main_layout

    def ui(self):

        self._central_layout = layouts.VerticalLayout(margins=(0, 0, 0, 0), spacing=0)
        self.setLayout(self._central_layout)

        self._top_widget = QWidget()
        self._top_layout = layouts.VerticalLayout(margins=(0, 0, 0, 0), spacing=0)
        self._top_widget.setLayout(self._top_layout)

        for r in self._resizers:
            r.setParent(self)
            r.windowResizedFinished.connect(self.dialogResizedFinished)
        self.set_resize_directions()

        self._dragger = dragger.DialogDragger(parent=self)
        self._dragger.setVisible(self.is_frameless())
        self._top_layout.addWidget(self._dragger)

        self.main_widget = DialogContents()
        self.main_layout = self.get_main_layout()
        self.main_widget.setLayout(self.main_layout)

        self.logo_view = QGraphicsView()
        self.logo_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.logo_view.setMaximumHeight(100)
        self._logo_scene = QGraphicsScene()
        self._logo_scene.setSceneRect(QRectF(0, 0, 2000, 100))
        self.logo_view.setScene(self._logo_scene)
        self.logo_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.logo_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.logo_view.setFocusPolicy(Qt.NoFocus)

        if self._has_title and self._title_pixmap:
            self._logo_scene.addPixmap(self._title_pixmap)
            self._top_layout.addWidget(self.logo_view)

        title_background_pixmap = self._get_title_pixmap()
        if self._has_title and title_background_pixmap:
            self._logo_scene.addPixmap(title_background_pixmap)
            self._top_layout.addWidget(self.logo_view)
        else:
            self.logo_view.setVisible(False)

        grid_layout = layouts.GridLayout()
        grid_layout.setHorizontalSpacing(0)
        grid_layout.setVerticalSpacing(0)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(self._top_widget, 1, 1, 1, 1)
        grid_layout.addWidget(self.main_widget, 2, 1, 1, 1)
        grid_layout.addWidget(self._top_left_resizer, 0, 0, 1, 1)
        grid_layout.addWidget(self._top_resizer, 0, 1, 1, 1)
        grid_layout.addWidget(self._top_right_resizer, 0, 2, 1, 1)
        grid_layout.addWidget(self._left_resizer, 1, 0, 2, 1)
        grid_layout.addWidget(self._right_resizer, 1, 2, 2, 1)
        grid_layout.addWidget(self._bottom_left_resizer, 3, 0, 1, 1)
        grid_layout.addWidget(self._bottom_resizer, 3, 1, 1, 1)
        grid_layout.addWidget(self._bottom_right_resizer, 3, 2, 1, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(2, 1)

        # Shadow effect for dialog
        # BUG: This causes some rendering problems when using other shadow effects in child widgets of the window
        # BUG: Also detected problems when updating wigets (tree views, web browsers, etc)
        # https://bugreports.qt.io/browse/QTBUG-35196
        # shadow_effect = QGraphicsDropShadowEffect(self)
        # shadow_effect.setBlurRadius(qtutils.dpi_scale(15))
        # shadow_effect.setColor(QColor(0, 0, 0, 150))
        # shadow_effect.setOffset(qtutils.dpi_scale(0))
        # self.setGraphicsEffect(shadow_effect)

        self._central_layout.addLayout(grid_layout)

        for r in self._resizers:
            r.windowResizedFinished.connect(self.dialogResizedFinished)

        if self._size:
            self.resize(self._size[0], self._size[1])

    def statusBar(self):
        """
        Returns status bar of the dialog
        :return: QStatusBar
        """

        return self._status_bar

    def dpi(self):
        """
        Return the current dpi for the window
        :return: float
        """

        return float(self._dpi)

    def set_dpi(self, dpi):
        """
        Sets current dpi for the window
        :param dpi: float
        """

        self._dpi = dpi

    def theme(self):
        """
        Returns the current theme
        :return: Theme
        """

        if not self._theme:
            self._theme = theme.Theme()

        return self._theme

    def set_theme(self, theme):
        """
        Sets current window theme
        :param theme: Theme
        """

        self._theme = theme
        self._theme.updated.connect(self.reload_stylesheet)
        self.reload_stylesheet()

    def set_theme_settings(self, settings):
        """
        Sets the theme settings from the given settings
        :param settings: dict
        """

        # TODO: We should be able to give a dialog a theme to load
        # TODO: This will allow to setup specific themes if dialogs are launch from windows with
        # TODO: specific themes

        new_theme = resources.theme('default')
        if not new_theme:
            new_theme = theme.Theme()
        new_theme.set_settings(settings)
        self.set_theme(new_theme)

    def reload_stylesheet(self):
        """
        Reloads the stylesheet to the current theme
        """

        current_theme = self.theme()
        if not current_theme:
            return
        current_theme.set_dpi(self.dpi())
        stylesheet = current_theme.stylesheet()
        self.setStyleSheet(stylesheet)
        self.styleReloaded.emit(current_theme)

    def setup_signals(self):
        pass

    def set_logo(self, logo, offset=(930, 0)):
        logo = self._logo_scene.addPixmap(logo)
        logo.setOffset(offset[0], offset[1])

    def resizeEvent(self, event):
        # TODO: Take the width from the QGraphicsView not hardcoded :)
        if hasattr(self, 'logo_view'):
            self.logo_view.centerOn(1000, 0)
        return super(BaseDialog, self).resizeEvent(event)

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()

    def setWindowIcon(self, icon):
        if self.is_frameless() or (hasattr(self, '_dragger') and self._dragger):
            self._dragger.set_icon(icon)
        super(BaseDialog, self).setWindowIcon(icon)

    def setWindowTitle(self, title):
        if self.is_frameless() or (hasattr(self, '_dragger') and self._dragger):
            self._dragger.set_title(title)
        super(BaseDialog, self).setWindowTitle(title)

    # ============================================================================================================
    # RESIZERS
    # ============================================================================================================

    def set_resizer_active(self, flag):
        """
        Sets whether resizers are enable or not
        :param flag: bool
        """

        if flag:
            for r in self._resizers:
                r.show()
        else:
            for r in self._resizers:
                r.hide()

    def set_resize_directions(self):
        """
        Sets the resize directions for the resizer widget of this window
        """

        self._top_resizer.set_resize_direction(resizers.ResizeDirection.Top)
        self._bottom_resizer.set_resize_direction(resizers.ResizeDirection.Bottom)
        self._right_resizer.set_resize_direction(resizers.ResizeDirection.Right)
        self._left_resizer.set_resize_direction(resizers.ResizeDirection.Left)
        self._top_left_resizer.set_resize_direction(resizers.ResizeDirection.Left | resizers.ResizeDirection.Top)
        self._top_right_resizer.set_resize_direction(resizers.ResizeDirection.Right | resizers.ResizeDirection.Top)
        self._bottom_left_resizer.set_resize_direction(resizers.ResizeDirection.Left | resizers.ResizeDirection.Bottom)
        self._bottom_right_resizer.set_resize_direction(
            resizers.ResizeDirection.Right | resizers.ResizeDirection.Bottom)

    def get_resizers_height(self):
        """
        Returns the total height of the vertical resizers
        :return: float
        """

        resizers = [self._top_resizer, self._bottom_resizer]
        total_height = 0
        for r in resizers:
            if not r.isHidden():
                total_height += r.minimumSize().height()

        return total_height

    def get_resizers_width(self):
        """
        Returns the total widht of the horizontal resizers
        :return: float
        """

        resizers = [self._left_resizer, self._right_resizer]
        total_width = 0
        for r in resizers:
            if not r.isHidden():
                total_width += r.minimumSize().width()

        return total_width

    def _setup_resizers(self):
        """
        Internal function that setup window resizers
        """

        self._top_resizer = resizers.VerticalResizer(parent=self)
        self._bottom_resizer = resizers.VerticalResizer(parent=self)
        self._right_resizer = resizers.HorizontalResizer(parent=self)
        self._left_resizer = resizers.HorizontalResizer(parent=self)
        self._top_left_resizer = resizers.CornerResizer(parent=self)
        self._top_right_resizer = resizers.CornerResizer(parent=self)
        self._bottom_left_resizer = resizers.CornerResizer(parent=self)
        self._bottom_right_resizer = resizers.CornerResizer(parent=self)

        self._resizers = [
            self._top_resizer, self._top_right_resizer, self._right_resizer, self._bottom_right_resizer,
            self._bottom_resizer, self._bottom_left_resizer, self._left_resizer, self._top_left_resizer
        ]

    def _get_title_pixmap(self):
        """
        Internal function that sets the pixmap used for the title
        """

        return None


class BaseColorDialog(BaseDialog, object):

    def_title = 'Select Color'

    maya_colors = [
        (.467, .467, .467), (.000, .000, .000), (.247, .247, .247), (.498, .498, .498), (0.608, 0, 0.157),
        (0, 0.016, 0.373), (0, 0, 1), (0, 0.275, 0.094), (0.145, 0, 0.263), (0.78, 0, 0.78), (0.537, 0.278, 0.2),
        (0.243, 0.133, 0.122), (0.6, 0.145, 0), (1, 0, 0), (0, 1, 0), (0, 0.255, 0.6), (1, 1, 1), (1, 1, 0),
        (0.388, 0.863, 1), (0.263, 1, 0.635), (1, 0.686, 0.686), (0.89, 0.675, 0.475), (1, 1, 0.384), (0, 0.6, 0.325),
        (0.627, 0.412, 0.188), (0.62, 0.627, 0.188), (0.408, 0.627, 0.188), (0.188, 0.627, 0.365),
        (0.188, 0.627, 0.627), (0.188, 0.404, 0.627), (0.435, 0.188, 0.627), (0.627, 0.188, 0.404)]

    def __init__(self, name='MayaColorDialog', parent=None, **kwargs):
        parent = parent or dcc.get_main_window()

        super(BaseColorDialog, self).__init__(name=name, parent=parent, **kwargs)

        self._color = None

    def get_color(self):
        return self._color

    color = property(get_color)

    def ui(self):

        self.color_buttons = list()

        super(BaseColorDialog, self).ui()

        grid_layout = layouts.GridLayout()
        grid_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addLayout(grid_layout)
        color_index = 0
        for i in range(0, 4):
            for j in range(0, 8):
                color_btn = QPushButton()
                color_btn.setMinimumHeight(35)
                color_btn.setMinimumWidth(35)
                self.color_buttons.append(color_btn)
                color_btn.setStyleSheet('background-color:rgb(%s,%s,%s);' % (
                    self.maya_colors[color_index][0] * 255,
                    self.maya_colors[color_index][1] * 255,
                    self.maya_colors[color_index][2] * 255
                ))
                grid_layout.addWidget(color_btn, i, j)
                color_index += 1
        selected_color_layout = layouts.HorizontalLayout()
        self.main_layout.addLayout(selected_color_layout)
        self.color_slider = QSlider(Qt.Horizontal)
        self.color_slider.setMinimum(0)
        self.color_slider.setMaximum(31)
        self.color_slider.setValue(2)
        self.color_slider.setStyleSheet(
            "QSlider::groove:horizontal {border: 1px solid #999999;height: 25px; /* the groove expands "
            "to the size of the slider by default. by giving it a height, it has a fixed size */background: "
            "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);margin: 2px 0;}"
            "QSlider::handle:horizontal {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4,"
            " stop:1 #8f8f8f);border: 1px solid #5c5c5c;width: 10px;margin: -2px 0; /* handle is placed by "
            "default on the contents rect of the groove. Expand outside the groove */border-radius: 1px;}")
        selected_color_layout.addWidget(self.color_slider)

        color_label_layout = layouts.HorizontalLayout(margins=(10, 10, 10, 10))
        self.main_layout.addLayout(color_label_layout)

        self.color_lbl = QLabel()
        self.color_lbl.setStyleSheet("border: 1px solid black; background-color:rgb(0, 0, 0);")
        self.color_lbl.setMinimumWidth(45)
        self.color_lbl.setMaximumWidth(80)
        self.color_lbl.setMinimumHeight(80)
        self.color_lbl.setAlignment(Qt.AlignCenter)
        color_label_layout.addWidget(self.color_lbl)

        bottom_layout = layouts.HorizontalLayout()
        bottom_layout.setAlignment(Qt.AlignRight)
        self.main_layout.addLayout(bottom_layout)

        self.ok_btn = QPushButton('Ok')
        self.cancel_btn = QPushButton('Cancel')
        bottom_layout.addLayout(dividers.DividerLayout())
        bottom_layout.addWidget(self.ok_btn)
        bottom_layout.addWidget(self.cancel_btn)

    def setup_signals(self):

        for i, btn in enumerate(self.color_buttons):
            btn.clicked.connect(partial(self._on_set_color, i))
        self.color_slider.valueChanged.connect(self._on_set_color)

        self.ok_btn.clicked.connect(self._on_ok_btn)
        self.cancel_btn.clicked.connect(self._on_cancel_btn)

    def _on_set_color(self, color_index):
        self.color_lbl.setStyleSheet('background-color:rgb(%s,%s,%s);' % (
            self.maya_colors[color_index][0] * 255,
            self.maya_colors[color_index][1] * 255,
            self.maya_colors[color_index][2] * 255
        ))
        self.color_slider.setValue(color_index)

    def _on_set_slider(self, color_index):
        self._set_color(color_index=color_index)

    def _on_ok_btn(self):
        self._color = self.color_slider.value()
        self.close()

    def _on_cancel_btn(self):
        self._color = None
        self.close()


class BaseFileFolderDialog(BaseDialog, abstract_dialog.AbstractFileFolderDialog):
    """
    Base dialog classes for folders and files
    """

    def_title = 'Select File'
    def_size = (200, 125)
    def_use_app_browser = False

    def __init__(self,
                 name='BaseFileFolder', parent=None, **kwargs):
        super(BaseFileFolderDialog, self).__init__(name=name, parent=parent)

        self.directory = None
        self.filters = None
        self._use_app_browser = kwargs.pop('use_app_browser', self.def_use_app_browser)

        self.set_filters('All Files (*.*)')

        # By default, we set the directory to the user folder
        self.set_directory(os.path.expanduser('~'))
        self.center()

    def open_app_browser(self):
        return

    def ui(self):
        super(BaseFileFolderDialog, self).ui()

        from tp.common.qt.widgets import directory

        self.places = dict()

        self.grid = layouts.GridLayout()
        sub_grid = layouts.GridLayout()
        self.grid.addWidget(QLabel('Path:'), 0, 0, Qt.AlignRight)

        self.path_edit = QLineEdit(self)
        self.path_edit.setReadOnly(True)
        self.filter_box = QComboBox(self)
        self.file_edit = QLineEdit(self)

        self.view = directory.FileListWidget(self)
        self.view.setWrapping(True)
        self.view.setFocusPolicy(Qt.StrongFocus)

        self.open_button = QPushButton('Select', self)
        self.cancel_button = QPushButton('Cancel', self)

        size = QSize(32, 24)
        self.up_button = QPushButton('Up')
        self.up_button.setToolTip('Go up')
        self.up_button.setMinimumSize(size)
        self.up_button.setMaximumSize(size)

        size = QSize(56, 24)
        self.refresh_button = QPushButton('Reload')
        self.refresh_button.setToolTip('Reload file list')
        self.refresh_button.setMinimumSize(size)
        self.refresh_button.setMaximumSize(size)

        self.show_hidden = QCheckBox('Hidden')
        self.show_hidden.setChecked(False)
        self.show_hidden.setToolTip('Toggle show hidden files')

        sub_grid.addWidget(self.up_button, 0, 1)
        sub_grid.addWidget(self.path_edit, 0, 2)
        sub_grid.addWidget(self.refresh_button, 0, 3)
        sub_grid.addWidget(self.show_hidden, 0, 4)
        self.grid.addLayout(sub_grid, 0, 1)
        self.grid.addWidget(self.get_drives_widget(), 1, 0)
        self.grid.addWidget(self.view, 1, 1)
        self.grid.addWidget(QLabel('File name:'), 7, 0, Qt.AlignRight)
        self.grid.addWidget(self.file_edit, 7, 1)
        self.filter_label = QLabel('Filter:')
        self.grid.addWidget(self.filter_label, 8, 0, Qt.AlignRight)
        self.grid.addWidget(self.filter_box, 8, 1)
        hbox = layouts.GridLayout()
        hbox.addWidget(self.open_button, 0, 0, Qt.AlignRight)
        hbox.addWidget(self.cancel_button, 0, 1, Qt.AlignRight)
        self.grid.addLayout(hbox, 9, 1, Qt.AlignRight)
        self.main_layout.addLayout(self.grid)
        self.setGeometry(200, 100, 600, 400)

        self.open_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.up_button.clicked.connect(self.go_up)
        self.refresh_button.clicked.connect(self.update_view)
        self.show_hidden.stateChanged.connect(self.update_view)
        self.view.directory_activated.connect(self.activate_directory_from_view)
        self.view.file_activated.connect(self.activate_file_from_view)
        self.view.file_selected.connect(self.select_file_item)
        self.view.folder_selected.connect(self.select_folder_item)
        self.view.up_requested.connect(self.go_up)
        self.view.update_requested.connect(self.update_view)

    def exec_(self, *args, **kwargs):
        if self._use_app_browser:
            return self.open_app_browser()
        else:
            self.update_view()
            self.filter_box.currentIndexChanged.connect(self.update_view)
            accepted = super(BaseFileFolderDialog, self).exec_()
            self.filter_box.currentIndexChanged.disconnect(self.update_view)
            return self.get_result() if accepted == 1 else None

    def set_filters(self, filters, selected=0):
        self.filter_box.clear()
        filter_types = filters.split(';;')
        for ft in filter_types:
            extensions = string.extract(ft, '(', ')')
            filter_name = string.rstrips(ft, '({})'.format(extensions))
            extensions = extensions.split(' ')
            self.filter_box.addItem('{} ({})'.format(filter_name, ','.join(extensions)), extensions)
        if 0 <= selected < self.filter_box.count():
            self.filter_box.setCurrentIndex(selected)
        self.filters = filters

    def get_drives_widget(self):
        """
        Returns a QGroupBox widget that contains all disk drivers of the PC in a vertical layout
        :return: QGroupBox
        """

        w = QGroupBox('')
        w.setParent(self)
        box = layouts.VerticalLayout()
        box.setAlignment(Qt.AlignTop)
        places = [(getpass.getuser(), os.path.realpath(os.path.expanduser('~')))]
        places += [(q, q) for q in [os.path.realpath(x.absolutePath()) for x in QDir().drives()]]
        for label, loc in places:
            icon = QFileIconProvider().icon(QFileInfo(loc))
            drive_btn = QRadioButton(label)
            drive_btn.setIcon(icon)
            drive_btn.setToolTip(loc)
            drive_btn.setProperty('path', loc)
            drive_btn.clicked.connect(self.go_to_drive)
            self.places[loc] = drive_btn
            box.addWidget(drive_btn)
        w.setLayout(box)
        return w

    def go_to_drive(self):
        """
        Updates widget to show the content of the selected disk drive
        """

        sender = self.sender()
        self.set_directory(sender.property('path'), False)

    def get_result(self):
        tf = self.file_edit.text()
        sf = self.get_file_path(tf)
        return sf, os.path.dirname(sf), tf.split(os.pathsep)

    def get_filter_patterns(self):
        """
        Get list of filter patterns that are being used by the widget
        :return: list<str>
        """

        idx = self.filter_box.currentIndex()
        if idx >= 0:
            return self.filter_box.itemData(idx)
        else:
            return []

    def get_file_path(self, file_name):
        """
        Returns file path of the given file name taking account the selected directory
        :param file_name: str, name of the file without path
        :return: str
        """

        sname = file_name.split(os.pathsep)[0]
        return os.path.realpath(os.path.join(os.path.abspath(self.directory), sname))

#     def accept(self):
#         self._overlay.close()
#         super(BaseFileFolderDialog, self).accept()
#
#
#     def reject(self):
#         self._overlay.close()
#         super(BaseFileFolderDialog, self).reject()

    def update_view(self):
        """
        Updates file/folder view
        :return:
        """

        self.view.clear()
        qdir = QDir(self.directory)
        qdir.setNameFilters(self.get_filter_patterns())
        filters = QDir.Dirs | QDir.AllDirs | QDir.Files | QDir.NoDot | QDir.NoDotDot
        if self.show_hidden.isChecked():
            filters = filters | QDir.Hidden
        entries = qdir.entryInfoList(filters=filters, sort=QDir.DirsFirst | QDir.Name)
        file_path = self.get_file_path('..')
        if os.path.exists(file_path) and file_path != self.directory:
            icon = QFileIconProvider().icon(QFileInfo(self.directory))
            QListWidgetItem(icon, '..', self.view, 0)
        for info in entries:
            icon = QFileIconProvider().icon(info)
            suf = info.completeSuffix()
            name, tp = (
                info.fileName(), 0) if info.isDir() else ('%s%s' % (info.baseName(), '.%s' % suf if suf else ''), 1)
            QListWidgetItem(icon, name, self.view, tp)
        self.view.setFocus()

    def set_directory(self, path, check_drive=True):
        """
        Sets the directory that you want to explore
        :param path: str, valid path
        :param check_drive: bool,
        :return:
        """

        self.directory = os.path.realpath(path)
        self.path_edit.setText(self.directory)
        self.file_edit.setText('')

        # If necessary, update selected disk driver
        if check_drive:
            for loc in self.places:
                rb = self.places[loc]
                rb.setAutoExclusive(False)
                rb.setChecked(loc.lower() == self.directory.lower())
                rb.setAutoExclusive(True)

        self.update_view()
        self.up_button.setEnabled(not self.cant_go_up())

    def go_up(self):
        """
        Updates the current directory to go to its parent directory
        """

        self.set_directory(os.path.dirname(self.directory))

    def cant_go_up(self):
        """
        Checks whether we can naviage to current selected parent directory or not
        :return: bool
        """

        return os.path.dirname(self.directory) == self.directory

    def activate_directory_from_view(self, name):
        """
        Updates selected directory
        :param name: str, name of the directory
        """

        self.set_directory(os.path.join(self.directory, name))

    def activate_file_from_view(self, name):
        """
        Updates selected file text and returns its info by accepting it
        :param name: str, name of the file
        """

        self.select_file_item(name=name)
        self.accept()

    def select_file_item(self, name):
        """
        Updates selected file text and returns its info by accepting it
        :param name: str, name of the file
        """

        self.file_edit.setText(name)

    def select_folder_item(self, name):
        """
        Updates selected folder text and returns its info by accepting it
        :param name: str, name of the folder
        """

        self.file_edit.setText(name)


class BaseOpenFileDialog(BaseFileFolderDialog, object):
    """
    Open file dialog
    """

    def __init__(
            self,
            name='OpenFile',
            multi=False,
            title='Open File',
            size=(200, 125),
            fixed_size=False,
            frame_less=True,
            hide_title=False,
            parent=None,
            use_app_browser=False):

        parent = parent or dcc.get_main_window()

        super(BaseOpenFileDialog, self).__init__(
            name=name, title=title, size=size, fixed_size=fixed_size, frame_less=frame_less,
            hide_title=hide_title, use_app_browser=use_app_browser, parent=parent
        )

        self._multi = multi
        if multi:
            self.setExtendedSelection()

    def accept(self, *args, **kwargs):
        selected_file, selected_dir, selected_file_name = self.get_result()
        if not os.path.isdir(selected_file):
            if os.path.exists(selected_file):
                super(BaseOpenFileDialog, self).accept()
            else:
                message_box = QMessageBox()
                message_box.setWindowTitle('Confirme file selection')
                message_box.setText('File "{0}" does not exists!'.format(selected_file))
                message_box.exec_()

    def select_file_item(self, names):
        if self._multi:
            self.file_edit.setText(os.pathsep.join(names))
        else:
            super(BaseOpenFileDialog, self).select_file_item(names)


class BaseSaveFileDialog(BaseFileFolderDialog, object):
    def __init__(self,
                 name='SaveFile',
                 title='Save File',
                 size=(200, 125),
                 fixed_size=False,
                 frame_less=True,
                 hide_title=False,
                 parent=None,
                 use_app_browser=False):

        parent = parent or dcc.get_main_window()

        super(BaseSaveFileDialog, self).__init__(
            name=name, title=title, size=size, fixed_size=fixed_size, frame_less=frame_less, hide_title=hide_title,
            use_app_browser=use_app_browser, parent=parent)

        self._open_button.setText('Save')
        size = QSize(42, 24)
        self.new_directory_button = QPushButton('New')
        self.new_directory_button.setToolTip('Create new directory')
        self.new_directory_button.setMinimumSize(size)
        self.new_directory_button.setMaximumWidth(size)
        self.new_directory_button.clicked.connect(self.create_new_directory)
        self.grid.itemAtPosition(0, 1).addWidget(self.new_directory_button, 0, 5)

    def accept(self, *args, **kwargs):
        selected_file, selected_dir, selected_filename = self.get_result()
        if not os.path.isdir(selected_file):
            if os.path.exists(selected_file):
                message_box = QMessageBox()
                message_box.setWindowTitle('Confirm File Selection')
                message_box.setText('File "%s" exists.\nDo you want to overwrite it?' % selected_file)
                message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                message_box.setDefaultButton(QMessageBox.No)
                rv = message_box.exec_()
                if rv == QMessageBox.Yes and not os.path.isdir(selected_file):
                    super(BaseSaveFileDialog, self).accept()
        else:
            super(BaseSaveFileDialog, self).accept()

    def create_new_directory(self):
        name, ok = QInputDialog.getText(self, 'New directory name', 'Name:', QLineEdit.Normal, 'New Directory')
        if ok and name:
            path = os.path.join(self.directory, name)
            if os.path.exists(path):
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle('Error')
                msg_box.setText('Directory already exists')
                msg_box.exec_()
            else:
                try:
                    os.makedirs(path)
                    self.update_view()
                except os.error as e:
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle('Error')
                    msg_box.setText('Cannot create directory')
                    msg_box.exec_()


class BaseSelectFolderDialog(BaseFileFolderDialog, object):
    def __init__(self,
                 name='SelectFolder',
                 title='Select Folder',
                 size=(200, 125),
                 fixed_size=False,
                 frame_less=True,
                 hide_title=False,
                 use_app_browser=False,
                 parent=None,
                 **kwargs):

        parent = parent or dcc.get_main_window()

        super(BaseSelectFolderDialog, self).__init__(
            name=name, title=title, size=size, fixed_size=fixed_size, frame_less=frame_less, hide_title=hide_title,
            use_app_browser=use_app_browser, parent=parent, **kwargs
        )

    def accept(self, *args, **kwargs):
        selected_file, selected_dir, selected_filename = self.get_result()
        super(BaseSelectFolderDialog, self).accept()

    def exec_(self, *args, **kwargs):
        self.set_filters('')
        return super(BaseSelectFolderDialog, self).exec_()


class BaseNativeDialog(abstract_dialog.AbstractNativeDialog, object):
    """
    Dialog that opens DCC native dialogs
    """

    pass


class DialogContents(QFrame, object):
    """
    Widget that defines the core contents of frameless window
    Can be used to custom CSS for frameless windows contents
    """

    def __init__(self, parent=None):
        super(DialogContents, self).__init__(parent=parent)
