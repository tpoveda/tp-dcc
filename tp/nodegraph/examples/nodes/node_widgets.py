from __future__ import annotations

import typing

from tp.nodegraph.core.node import Node
from tp.nodegraph.core import datatypes

if typing.TYPE_CHECKING:
    from tp.nodegraph.core.factory import NodeFactory


class DropdownMenuNode(Node):
    """
    Node that represents a dropdown menu.
    """

    NODE_NAME = "Menu"
    CATEGORY = "Utils"
    IS_EXEC = False

    def setup_ports(self):
        """
        Setup node ports.
        """

        super().setup_ports()

        self.add_input(datatypes.String, "in 1")
        self.add_output(datatypes.Numeric, "out 1")
        self.add_output(datatypes.Boolean, "out 2")

    def setup_widgets(self):
        """
        Setup node widgets.
        """

        super().setup_widgets()

        items = ["item 1", "item 2", "item 3"]
        self.add_combo_menu(
            "my_menu", "Menu Test", items=items, tooltip="Example Custom Tooltip"
        )


class TextInputNode(Node):
    """
    Node that represents a text input.
    """

    NODE_NAME = "Text"
    CATEGORY = "Utils"
    IS_EXEC = False

    def setup_ports(self):
        """
        Setup node ports.
        """

        super().setup_ports()

        self.add_input(datatypes.String, "in 1")
        self.add_output(datatypes.String, "out 1")

    def setup_widgets(self):
        """
        Setup node widgets.
        """

        super().setup_widgets()

        self.add_text_input("my_input", "Text Input", tooltip="Example Custom Tooltip")


class CheckboxNode(Node):
    """
    Node that represents a checkbox.
    """

    NODE_NAME = "Checkbox"
    CATEGORY = "Utils"

    def setup_ports(self):
        """
        Setup node ports.
        """

        super().setup_ports()

        self.add_input(datatypes.String, "in 1", color=(200, 100, 0))
        self.add_output(datatypes.String, "out 1", color=(0, 100, 200))

    def setup_widgets(self):
        """
        Setup node widgets.
        """

        super().setup_widgets()

        self.add_checkbox("cb_1", "" "Checkbox 1", state=True)
        self.add_checkbox("cb_2", "" "Checkbox 2", state=False)


def register_plugin(factory: NodeFactory):
    """
    Registers the plugin in the given factory.

    :param factory: factory instance used to register nodes.
    """

    factory.register_node(DropdownMenuNode, "menu")
    factory.register_node(TextInputNode, "text")
    factory.register_node(CheckboxNode, "checkbox")
