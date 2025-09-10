from __future__ import annotations

from typing import Any

from tp.libs.plugin import Plugin
from tp.libs.maya.triggers import callbacks


class MarkingMenuCommand(Plugin):
    """Class that defines a single marking menu action."""

    ID = ""
    DOCUMENTATION = __doc__

    @staticmethod
    def ui_data(arguments: dict[str, Any]) -> dict[str, Any]:
        """Function that returns the UI data for the marking menu command.

        :param arguments: dictionary with the arguments to use to generate the UI data.
        :return: dictionary with the UI data for the marking menu command.
        """

        return {
            "icon": arguments.get("icon", ""),
            "label": arguments.get("label", ""),
            "bold": False,
            "italic": False,
            "optionBox": False,
            "enable": True,
            "checkBox": None,
        }

    def execute(self, arguments: dict[str, Any]):
        """Function that is called when the marking menu command is executed.

        :param arguments: dictionary with the arguments to use to generate the marking
            menu.
        """

        pass

    def execute_ui(self, arguments: dict[str, Any]):
        """Function that is called when the marking menu command is executed with the
        option box.

        :param arguments: dictionary with the arguments to use to generate the marking
            menu.
        """

        pass

    def _execute(self, arguments: dict[str, Any], option_box: bool = False, *args):
        """Internal function that is called when the marking menu command is executed.

        :param arguments: dictionary with the arguments to use to generate the marking
            menu.
        :param option_box: bool, whether to show the option box or not.
        :param args: optional arguments to pass to the command.
        """

        with callbacks.block_selection_callback():
            self.execute_ui(arguments) if option_box else self.execute(arguments)
