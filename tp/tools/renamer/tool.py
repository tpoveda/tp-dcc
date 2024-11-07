from __future__ import annotations

import typing

from Qt.QtWidgets import QWidget

from tp.core.tool import Tool, UiData

from . import consts
from .view import RenamerView
from .model import RenamerModel
from .controller import RenamerControllerFactory

if typing.TYPE_CHECKING:
    from .controllers.abstract import ARenamerController


class RenamerTool(Tool):
    """Tool used to rename nodes."""

    id = consts.TOOL_ID
    ui_data = UiData(label="Renamer")
    tags = ["tp", "renamer", "tool"]

    def __init__(self, *args, **kwargs):
        self._model: RenamerModel = kwargs.pop("model")
        self._controller: ARenamerController = kwargs.pop("controller")
        self._view: RenamerView | None = None

        super().__init__(*args, **kwargs)

    def contents(self) -> list[QWidget]:
        self._view = RenamerView(self._model)
        return [self._view]


def show() -> RenamerTool:
    """
    Function to show the Renamer tool.

    :return: Renamer tool instance created by this function.
    """

    def _resize_window():
        window.parent_container.resize(window.parent_container.size().width(), 0)

    model = RenamerModel()
    controller = RenamerControllerFactory.controller()
    tool = RenamerTool(model=model, controller=controller)
    window = tool.execute()

    # noinspection PyUnresolvedReferences
    tool.widgets()[0].closeRequested.connect(_resize_window)

    model.updateNodeTypes.connect(controller.update_node_types)
    model.updatePrefixesSuffixes.connect(controller.update_prefixes_suffixes)
    model.renameBaseName.connect(controller.rename_base_name)
    model.searchReplace.connect(controller.search_replace)
    model.addPrefix.connect(controller.add_prefix)
    model.addSuffix.connect(controller.add_suffix)
    model.removePrefix.connect(controller.remove_prefix)
    model.removeSuffix.connect(controller.remove_suffix)
    model.editIndex.connect(controller.edit_index)
    model.shuffleIndex.connect(controller.shuffle_index)
    model.changePadding.connect(controller.change_padding)
    model.doRenumber.connect(controller.renumber)
    model.removeNumbers.connect(controller.remove_numbers)
    model.assignNamespace.connect(controller.assign_namespace)
    model.deleteSelectedNamespace.connect(controller.delete_selected_namespace)
    model.deleteUnusedNamespaces.connect(controller.delete_unused_namespaces)
    model.openNamespaceEditor.connect(controller.open_namespace_editor)
    model.openReferenceEditor.connect(controller.open_reference_editor)
    model.autoPrefix.connect(controller.auto_prefix)
    model.autoSuffix.connect(controller.auto_suffix)
    model.makeUniqueName.connect(controller.make_unique_name)

    model.update_node_types()
    model.update_prefixes_suffixes()
    model.update_widgets_from_properties()

    return tool
