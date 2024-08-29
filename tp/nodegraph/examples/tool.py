from __future__ import annotations

from Qt.QtWidgets import QWidget

from . import model, hook, view
from ...core import tool


class NodeGraphTool(tool.Tool):
    """
    Tool that allows to create node graphs.
    """

    id = "tp.nodegraph"
    creator = "Tomas Poveda"
    ui_data = tool.UiData(label="Node Graph")
    tags = ["nodegraph"]

    def __init__(self, *args, **kwargs):
        self._model: model.NodeGraphModel = kwargs.pop("model")
        self._hook: hook.NodeGraphHook = kwargs.pop("hook")

        super().__init__(*args, **kwargs)

        self._view: view.NodeGraphToolView | None = None

    @property
    def view(self) -> view.NodeGraphToolView:
        """
        Getter method that returns the view of the tool.

        :return: noddle view
        """

        return self._view

    def contents(self) -> list[QWidget]:
        self._view = view.NodeGraphToolView(self._model)
        return [self._view]


def show() -> NodeGraphTool:
    tool_model = model.NodeGraphModel()
    tool_hook = hook.NodeGraphHook()
    new_tool = NodeGraphTool(model=tool_model, hook=tool_hook)
    main_window = new_tool.execute()

    main_window.parent_container.resize(1000, 800)

    new_tool.view.windowTitleChanged.connect(lambda title: main_window.set_title(title))

    tool_model.createNewGraph.connect(tool_hook.new_build_graph)

    tool_model.new_graph()

    return new_tool
