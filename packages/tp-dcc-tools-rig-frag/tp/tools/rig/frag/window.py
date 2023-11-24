from __future__ import annotations

import typing

from overrides import override

from tp.core import log
from tp.common.qt import api as qt

from tp.tools.rig.frag.core import blueprint
from tp.tools.rig.frag.widgets import buildtoolbar, actionstree

if typing.TYPE_CHECKING:
    from tp.tools.rig.frag.controller import FragController

logger = log.rigLogger


class FragWindow(qt.FramelessWindow):

    def __init__(self, controller: FragController, parent: qt.QWidget | None = None):

        self._controller = controller
        self._window_title = 'FRAG Builder v0.0.1'
        self._blueprint_model = blueprint.BlueprintModel.get()

        super().__init__(title=self._window_title, parent=parent)

        self.setMinimumSize(350, 500)

    @property
    def controller(self) -> FragController:
        return self._controller

    @override
    def setup_widgets(self):
        super().setup_widgets()

        self._blueprint_widget = qt.QWidget(parent=self)
        self._build_toolbar = buildtoolbar.BuildToolbar(parent=self)
        self._build_toolbar.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Maximum)
        self._actions_tree_widget = actionstree.ActionsTree(parent=self)

    @override
    def setup_layouts(self):
        super().setup_layouts()

        main_layout = self.set_main_layout(qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0)))

        blueprint_layout = qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self._blueprint_widget.setLayout(blueprint_layout)
        blueprint_layout.addWidget(self._build_toolbar)
        blueprint_layout.addWidget(self._actions_tree_widget)

        main_layout.addWidget(self._blueprint_widget)

    @override
    def setup_signals(self):
        super().setup_signals()
