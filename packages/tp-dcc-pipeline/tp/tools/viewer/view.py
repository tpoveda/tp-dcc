from __future__ import annotations

from overrides import override

from tp.common.qt import api as qt
from tp.common.resources import api as resources


class ViewerWindow(qt.FramelessWindow):

    @override
    def setup_widgets(self):

        self._menu_bar = qt.QMenuBar(parent=self)
        self._file_menu = self._menu_bar.addMenu('File')
        self._load_action = self._file_menu.addAction(resources.icon('folder'), 'Load')

        self._viewer_splitter = qt.QSplitter(qt.Qt.Horizontal, parent=self)
        self._viewer_splitter.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        self._viewer = qt.QOpenGLWidget(parent=self)
        self._viewer.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        self._tab_widget = qt.QTabWidget(parent=self)
        self._viewer_splitter.addWidget(self._viewer)
        self._viewer_splitter.addWidget(self._tab_widget)

        self._data_widget = qt.widget(layout=qt.vertical_layout(), parent=self)
        self._settings_widget = qt.widget(layout=qt.vertical_layout(), parent=self)
        self._tab_widget.addTab(self._data_widget, 'Data')
        self._tab_widget.addTab(self._settings_widget, 'Settings')

    @override
    def setup_layouts(self):

        main_layout = self.set_main_layout(qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0)))

        viewer_layout = qt.horizontal_layout(spacing=0, margins=(0, 0, 0, 0))
        viewer_layout.addWidget(self._viewer_splitter)

        main_layout.addWidget(self._menu_bar)
        main_layout.addLayout(viewer_layout)

    @override
    def setup_signals(self):
        pass
