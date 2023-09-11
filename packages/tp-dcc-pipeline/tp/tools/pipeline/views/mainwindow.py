from __future__ import annotations

import os
import inspect

from overrides import override

from tp.common.python import path
from tp.common.qt import api as qt
from tp.common.resources import ui

from tp.tools.pipeline import style


class MainWindow(qt.FramelessWindow):
    def __init__(self, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        stylesheet = self.styleSheet()
        custom_css = style.PipelineUiStyle.load_css(':/styles/default')
        if custom_css:
            stylesheet = stylesheet + '\n\n/*Included from custom Pipeline style*/\n\n' + custom_css
        self.setStyleSheet(stylesheet)

    @override
    def setup_ui(self):
        super().setup_ui()

        root_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        ui_path = path.join_path(root_path, 'mainwindow.ui')
        self.ui = ui.ui_importer(ui_path)

        main_layout = self.main_layout()
        main_layout.addWidget(self.ui)


