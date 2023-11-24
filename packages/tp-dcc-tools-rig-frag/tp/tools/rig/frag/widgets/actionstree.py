from __future__ import annotations

from tp.common.qt import api as qt
from tp.tools.rig.frag.core import blueprint


class ActionsTree(qt.QWidget):
    """
    Widget that displays all build actions in a Blueprint.
    Build action items can be selected, and the shared selection model can be used to display info selected
    Build actions in other UIs.
    """

    def __init__(self, parent: qt.QWidget | None = None):
        super().__init__()

        self._blueprint_model = blueprint.BlueprintModel.get()
        self._model = self._blueprint_model.build_step_tree_model

        self.setLayout(qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0)))

        self._main_stack = qt.sliding_opacity_stacked_widget(parent=self)

        self._active_page = qt.widget(layout=qt.vertical_layout(spacing=2, margins=(0, 0, 0, 0)), parent=self)
        self._search_edit = qt.line_edit(placeholder_text='Search...', parent=self)
        self._actions_tree_view = ActionsTreeView(self._blueprint_model, parent=self)
        self._actions_tree_view.setModel(self._model)
        self._actions_tree_view.expandAll()
        self._active_page.layout().addWidget(self._search_edit)
        self._active_page.layout().addWidget(self._actions_tree_view)

        self._inactive_page = qt.widget(layout=qt.vertical_layout(spacing=2, margins=(0, 0, 0, 0)), parent=self)
        self._help_label = qt.label('Create Blueprint to begin', parent=self)
        self._help_label.setAlignment(qt.Qt.AlignCenter)
        font = self._help_label.font()
        font.setBold(True)
        font.setPointSize(12)
        self._help_label.setFont(font)
        self._inactive_page.layout().addWidget(self._help_label)

        self._main_stack.addWidget(self._active_page)
        self._main_stack.addWidget(self._inactive_page)

        self.layout().addWidget(self._main_stack)

        self._model.modelReset.connect(self._on_model_reset)
        self._blueprint_model.fileChanged.connect(self._on_blueprint_model_file_changed)

        self._update_stack()

    def _update_stack(self):
        """
        Internal function that updates stack based on whether a blueprint file is opened.
        """

        if self._blueprint_model.is_changing_scenes:
            return

        if self._blueprint_model.is_file_open():
            self._main_stack.setCurrentWidget(self._active_page)
        else:
            self._main_stack.setCurrentWidget(self._inactive_page)

    def _on_model_reset(self):
        """
        Internal callback function that is called each time model is reset.
        """

        self._actions_tree_view.expandAll()

    def _on_blueprint_model_file_changed(self):
        """
        Internal callback function that is called each time blueprint model file is changed.
        """

        self._update_stack()


class ActionsTreeView(qt.QTreeView):
    """
    Tree view that displays build actions in a Blueprint.
    """

    def __init__(self, blueprint_model: blueprint.BlueprintModel, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._blueprint_model = blueprint_model

        self.setHeaderHidden(True)
        self.setAcceptDrops(True)
        self.setRootIsDecorated(False)
        self.setExpandsOnDoubleClick(False)
        self.setDefaultDropAction(qt.Qt.MoveAction)
        self.setSelectionMode(qt.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setIndentation(14)
        self.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOn)
