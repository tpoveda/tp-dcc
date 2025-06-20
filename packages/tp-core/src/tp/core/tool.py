from __future__ import annotations

import sys
import traceback
from typing import TypedDict

from loguru import logger
from Qt.QtWidgets import QWidget, QStackedWidget

from tp.libs.dcc import callback
from tp.libs.plugin import Plugin, PluginsManager, PluginExecutionStats


class UiData(TypedDict, total=False):
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
    ui_data: UiData = {}

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

    # noinspection PyUnusedLocal
    def execute(self, *args, **kwargs):
        """Execute the tool with the specified arguments.

        This method executes the function with the provided arguments and
        keyword arguments.

        Args:
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """

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
