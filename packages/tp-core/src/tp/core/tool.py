from __future__ import annotations

import sys
import typing
import traceback
from typing import cast, Type, TypedDict

from loguru import logger
from Qt.QtWidgets import QWidget, QStackedWidget

from tp.dcc import callback
from tp.core.host import current_host
from tp.libs.qt.widgets import Window
from tp.libs.plugin import Plugin, PluginsManager, PluginExecutionStats

if typing.TYPE_CHECKING:
    from tp.libs.qt.mvc import Model, Controller
    from tp.tools.hub.widgets.toolpanel import ToolPanelWidget


class ToolUiData(TypedDict, total=False):
    """A data class for storing UI-related data for a tool.

    Attributes:
    ----------
    label : str
        The label to be displayed for the UI element.
            Defaults to an empty string.
    icon : str
        The path to the icon to be used for the UI element.
            Defaults to an empty string.
    tooltip : str
        The tooltip text for the UI element. Defaults to an empty string.
    tags : list[str]
        The tags associated with the UI element. Defaults to an empty list.
    color : str
        The color to be used for the UI element.
    background_color : str
        The background color to be used for the UI element.
    is_checkable : bool
        Whether the UI element is checkable. Defaults to False.
    is_checked : bool
        Whether the UI element is checked. Defaults to False.
    load_on_startup : bool
        Whether the tool should be loaded on startup. Defaults to False.
    class_name: str
        The class name of the tool. Defaults to an empty string.
    """

    label: str
    icon: str
    tooltip: str
    tags: list[str]
    color: str
    background_color: str
    is_checkable: bool
    is_checked: bool
    load_on_startup: bool
    class_name: str


class Tool(Plugin):
    """Base class used by tp-dcc-tools framework to implement DCC tools that
    have access to tp-dcc-tools functionality.

    Attributes:
    ----------
    id : str
        The unique identifier for the tool. This is the ID that will be used
        by `ToolsManager` to identify and run the tool.
    creator: str
        The creator of the tool.
    tags: list[str]
        A list of tags associated with the tool.
    ui_data : UiData
        The UI data associated with the tool.
    """

    id: str = ""
    creator: str = "Tomi Poveda"
    tags: list[str] = []
    ui_data: ToolUiData = {}
    tool_panel_class: Type[ToolPanelWidget] | None = None
    tool_model: Model = None
    tool_controller: Controller = None
    tool_view: QWidget = None

    def __init__(self, manager: PluginsManager | None = None):
        super(Tool, self).__init__()

        self._manager = manager
        self._stats = PluginExecutionStats(self)
        self._widgets: list[QWidget] = []
        self._stacked_widget: QStackedWidget | None = None
        self._closed = False
        self._callbacks = callback.FnCallback()

    @property
    def stats(self) -> PluginExecutionStats:
        """The statistics associated with the instance."""

        return self._stats

    @property
    def callbacks(self) -> callback.FnCallback:
        """The callbacks associated with the instance."""

        return self._callbacks

    # noinspection PyCallingNonCallable,PyAttributeOutsideInit
    @classmethod
    def setup(cls) -> QWidget | None:
        """Set up the tool by initializing its model, controller, and view."""

        view: QWidget | None = None
        if all(
            [
                cls.tool_model is not None,
                cls.tool_controller is not None,
                cls.tool_view is not None,
            ]
        ):
            model = cls.tool_model()
            controller = cls.tool_controller(model=model)

            cls.setup_model_controller(model=model, controller=controller)

            view = cls.tool_view(model=model)

        return view

    @classmethod
    def setup_model_controller(cls, model: Model, controller: Controller) -> None:
        """Set up the model and controller for the tool.

        Args:
            model: The model instance to set up.
            controller: The controller instance to set up.
        """

    @classmethod
    def setup_tool_panel(cls, tool_panel: ToolPanelWidget, view: QWidget) -> None:
        """Set up the tool panel with the provided view.

        Args:
            tool_panel: The tool panel widget to set up.
            view: The view widget to add to the tool panel.
        """

    # noinspection PyUnusedLocal, PyCallingNonCallable, PyAttributeOutsideInit
    def execute(self, *args, **kwargs):
        """Execute the tool with the specified arguments.

        This method executes the function with the provided arguments and
        keyword arguments.

        Args:
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """

        tool_view = self.setup()

        if tool_view is not None:
            host = current_host()
            window = cast(
                Window,
                host.show_dialog(
                    window_class=Window,
                    name=self.__class__.__name__,
                    allows_multiple=False,
                    settings_path=self.id.replace(".", "/") if self.id else "",
                ),
            )
            window.set_title(self.ui_data.get("label"))
            window.main_layout().addWidget(tool_view)
            window.closed.connect(self._run_teardown)

        # if not self.tool_panel_class:
        #     return
        #
        # tool_panel_widget = self.tool_panel_class()
        # tool_panel_widget.setup()
        # tool_panel_widget.toggle_contents(True)
        # window = Window()
        # window.main_layout().addWidget(tool_panel_widget)
        # window.set_title(self.ui_data.get("label", "Tool"))
        # window.resize(400, 600)
        # window.show()

        # host = current_host()
        # window = cast(
        #     Window,
        #     host.show_dialog(
        #         window_class=Window,
        #         name=self.id,
        #         allows_multiple=False,
        #         *args,
        #         **kwargs,
        #     ),
        # )
        # tool_panel_widget.setParent(window)
        # window.main_layout().addWidget(tool_panel_widget)

        # kwargs["name"] = self.__class__.__name__
        # kwargs["settings_path"] = self.id.replace(".", "/") if self.id else ""
        # win = window.Window(*args, **kwargs)
        # win.closed.connect(self.closed.emit)
        # win.set_title(self.ui_data.label)
        # self._stacked_widget = QStackedWidget(parent=win)
        # win.main_layout().addWidget(self._stacked_widget)
        #
        # self.pre_content_setup()
        #
        # for widget in self.contents():
        #     self._stacked_widget.addWidget(widget)
        #     self._widgets.append(widget)
        #
        # self.post_content_setup()
        #
        # win.show()
        # win.closed.connect(self._run_teardown)
        #
        # return win

    # def widgets(self) -> list[QWidget]:
    #     """Return a list of widgets associated with the instance.
    #
    #     This method returns a list of widgets associated with the instance.
    #
    #     Returns:
    #     A list of widgets associated with the instance.
    #     """
    #
    #     return self._widgets

    # def pre_content_setup(self):
    #     """Function that is called before the tool UI is created.
    #
    #     Notes:
    #         Can be overridden in tool subclasses.
    #     """
    #
    # # noinspection PyMethodMayBeStatic
    # def contents(self) -> list[QWidget]:
    #     """Function that returns tool widgets.
    #
    #     Returns:
    #             List of content widgets.
    #     """
    #
    #     return []

    # def post_content_setup(self):
    #     """Function that is called after the tool UI is created.
    #
    #     Notes:
    #         Can be overridden in tool subclasses.
    #     """

    def teardown(self):
        """Function that shutdown tool."""

    def run(self):
        """Runs the tool."""

    def _execute(self, *args, **kwargs) -> Tool:
        """Execute the tool safely."""

        self.stats.start()
        exc_type, exc_value, exc_tb = None, None, None
        try:
            self.execute(*args, **kwargs)
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            raise
        finally:
            tb = None
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            self.stats.finish(tb)

        return self

    def _run_teardown(self):
        """Tear down the tool safely."""

        if self._closed:
            logger.warning(f'Tool f"{self}" already closed')
            return

        try:
            self._callbacks.clear()
            self.teardown()
            self._closed = True
        except RuntimeError:
            logger.error(f"Failed to teardown tool: {self.id}", exc_info=True)
