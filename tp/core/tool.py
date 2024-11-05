from __future__ import annotations

import sys
import logging
import traceback
from dataclasses import dataclass

from Qt.QtCore import Signal, QObject
from Qt.QtWidgets import QWidget, QStackedWidget

from ..dcc import callback
from ..python import decorators, plugin
from ..qt.widgets import window

logger = logging.getLogger(__name__)


@dataclass
class UiData:
    """
    A data class for storing UI-related data for a tool.

    Attributes
    ----------
    label : str
        The label to be displayed for the UI element. Defaults to an empty string.
    icon : str
        The path to the icon to be used for the UI element. Defaults to an empty string.
    tooltip : str
        The tooltip text for the UI element. Defaults to an empty string.
    """

    label: str = ""
    icon: str = ""
    tooltip: str = ""


class Tool(QObject):
    """
    Base class used by tp-dcc-tools framework to implement DCC tools that have access to tp-dcc-tools functionality.
    """

    ID: str = ""

    closed = Signal()

    def __init__(self, factory: plugin.PluginFactory | None = None):
        super(Tool, self).__init__()

        self._factory = factory
        self._stats = plugin.PluginStats(self)
        self._widgets: list[QWidget] = []
        self._stacked_widget: QStackedWidget | None = None
        self._closed = False
        self._callbacks = callback.FnCallback()

    # noinspection PyMethodParameters
    @decorators.classproperty
    def id(cls) -> str:
        """
        Gets the identifier associated with the class.

        This class property returns the identifier associated with the class.
        """

        return ""

    # noinspection PyMethodParameters
    @decorators.classproperty
    def creator(cls) -> str:
        """
        Gets the creator associated with the class.

        This class property returns the creator associated with the class.
        """

        return "Tomi Poveda"

    @decorators.classproperty
    def ui_data(cls) -> UiData:
        """
        Gets the UI data associated with the class.

        This class property returns the UI data associated with the class.
        """

        return UiData()

    # noinspection PyMethodParameters
    @decorators.classproperty
    def tags(cls) -> list[str]:
        """
        Gets the tags associated with the class.

        This class property returns the tags associated with the class.
        """

        return []

    @property
    def stats(self) -> plugin.PluginStats:
        """
        Gets the statistics associated with the instance.

        This property returns the statistics associated with the instance.
        """

        return self._stats

    @property
    def callbacks(self) -> callback.FnCallback:
        """
        Gets the callbacks associated with the instance.

        This property returns the callbacks associated with the instance.
        """

        return self._callbacks

    # noinspection PyUnusedLocal
    def execute(self, *args, **kwargs) -> window.Window:
        """
        Executes the tool with the specified arguments and keyword arguments.

        This method executes the function with the provided arguments and keyword arguments.

        :param args: Positional arguments to pass to the function.
        :param kwargs: Keyword arguments to pass to the function.
        :return: The frameless window resulting from the function execution.
        """

        win = window.Window()
        win.closed.connect(self.closed.emit)
        win.set_title(self.ui_data.label)
        self._stacked_widget = QStackedWidget(parent=win)
        win.main_layout().addWidget(self._stacked_widget)

        self.pre_content_setup()

        for widget in self.contents():
            self._stacked_widget.addWidget(widget)
            self._widgets.append(widget)

        self.post_content_setup()

        win.show()
        win.closed.connect(self._run_teardown)

        return win

    def widgets(self) -> list[QWidget]:
        """
        Returns a list of widgets associated with the instance.

        This method returns a list of widgets associated with the instance.

        :return: A list of widgets associated with the instance.
        """

        return self._widgets

    def pre_content_setup(self):
        """
        Function that is called before tool UI is created.
        Can be override in tool subclasses.
        """

        pass

    # noinspection PyMethodMayBeStatic
    def contents(self) -> list[QWidget]:
        """
        Function that returns tool widgets.
        """

        return []

    def post_content_setup(self):
        """
        Function that is called after tool UI is created.
        Can be override in tool subclasses.
        """

        pass

    def teardown(self):
        """
        Function that shutdown tool.
        """

        self._callbacks.clear()

    def run(self):
        """
        Runs the tool.

        This method runs the tool.
        """

        pass

    def _execute(self, *args, **kwargs) -> Tool:
        """
        Internal function that executes tool in a safe way.
        """

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
        """
        Internal function that tries to tear down the tool in a safe way.
        """

        if self._closed:
            logger.warning(f'Tool f"{self}" already closed')
            return

        try:
            self.teardown()
            self._closed = True
        except RuntimeError:
            logger.error(f"Failed to teardown tool: {self.id}", exc_info=True)
