from __future__ import annotations

from typing import Any
from operator import itemgetter

from maya import cmds
from maya.api import OpenMaya

from tp.maya import wrapper
from tp.maya.om import attributetypes
from tp.maya.cmds import decorators
from tp.maya.markingmenu import errors
from tp.maya.markingmenu.menu import MarkingMenu
from tp.maya.markingmenu.layout import MarkingMenuLayout
from tp.maya.markingmenu.manager import MarkingMenusManager

from ..node import TriggerNode
from ..command import TriggerCommand
from ..callbacks import block_selection_callback_decorator

TOP_LEVEL_MENU_NAME = "tpTriggerMenu"


@decorators.undo
@block_selection_callback_decorator
def build_trigger_menu(parent_menu: str, node_name: str) -> bool:
    """
    Builds and displays the trigger menu for the given node.

    :param parent_menu: Maya parent menu name.
    :param node_name: node name to build the trigger menu for. This is the node that
        is located under the mouse pointer.
    :return: True if the trigger menu was built successfully; False otherwise.
    """

    overrides: bool = False
    context_info = gather_menus_from_nodes(node_name)
    if not context_info:
        return overrides

    layout = context_info["layout"]
    if layout:
        if not layout.solve():
            return overrides
        MarkingMenu.build_from_layout_data(
            layout,
            TOP_LEVEL_MENU_NAME,
            parent_menu,
            options={},
            arguments={"nodes": context_info["nodes"]},
        )
        overrides = True

    return overrides


def gather_menus_from_nodes(node_name: str | None = None):
    """
    Returns the current selected nodes and the final composed (but not solved) trigger
    marking menu layout.

    :param node_name: Maya path to the scene node to find the initial trigger on.
    :return: dictionary containing the nodes and the marking menu layout found.
    """

    node_name = node_name or ""
    selected_nodes = list(wrapper.selected())

    # If the node name is valid, we add it to the selected nodes list.
    if cmds.objExists(node_name):
        trigger_node = wrapper.node_by_name(node_name)
        if trigger_node not in selected_nodes:
            selected_nodes.insert(0, trigger_node)
    if not selected_nodes:
        return {}

    trigger_nodes = TriggerNode.iterate_connected_trigger_nodes(
        selected_nodes, filter_class=TriggerCommand
    )
    if not trigger_nodes:
        return {}

    layouts: list[MarkingMenuLayout] = []
    visited: set[str] = set()
    for menu_node in trigger_nodes:
        trigger = TriggerNode.from_node(menu_node)
        trigger_menu_command = trigger.command
        menu_id = trigger_menu_command.menu_id()
        if menu_id in visited or not menu_id:
            continue
        visited.add(menu_id)
        layout = trigger_menu_command.execute({"nodes": selected_nodes})
        layouts.append(layout)
    if not layouts:
        return {}

    layouts.sort(key=itemgetter("sortOrder"), reverse=True)

    return {"nodes": selected_nodes, "layout": layouts[-1]}


class TriggerMenuCommand(TriggerCommand):
    ID = "triggerMenu"

    COMMAND_ATTR_NAME = "tpTriggerMenuName"

    def attributes(self) -> list[dict]:
        """
        Returns a list of dictionaries that define the attributes of the trigger command.

        :return: list of dictionaries that define the attributes of the trigger command.
        """

        return [
            {
                "name": TriggerMenuCommand.COMMAND_ATTR_NAME,
                "type": attributetypes.kMFnDataString,
                "value": "",
                "locked": True,
            }
        ]

    def menu_id(self) -> str:
        """
        Return sthe internal ID of the marking menu layout.

        :return: marking menu layout ID.
        """

        attr = self._node.attribute(TriggerMenuCommand.COMMAND_ATTR_NAME)
        return attr.value() if attr else ""

    def set_menu(self, menu_id: str, mod: OpenMaya.MDGModifier | None = None):
        """
        Sets the menu ID of the trigger command.

        :param menu_id: ID of the menu to set.
        :param mod: optional modifier to use to modify the node.
        """

        if not MarkingMenusManager().has_menu(menu_id):
            raise errors.MissingMarkingMenu(
                f"No marking menu registered with ID: {menu_id}"
            )

        attr = self._node.attribute(TriggerMenuCommand.COMMAND_ATTR_NAME)
        try:
            attr.lock(False)
            attr.set(menu_id, mod=mod)
        finally:
            attr.lock(True)

    def execute(self, arguments: dict[str, Any]) -> MarkingMenuLayout:
        """
        Function that loads the marking menu layout for the command.

        :param arguments: dictionary with the arguments to execute the command.
        :return: marking menu layout instance.
        """

        menu_id = self.menu_id()
        if not menu_id:
            return MarkingMenuLayout()

        menu_type = MarkingMenusManager().menu_type(menu_id)
        marking_menu_layout = MarkingMenuLayout(**{"items": {}})
        if menu_type == MarkingMenusManager.STATIC_LAYOUT_TYPE:
            new_layout = MarkingMenusManager.find_layout(menu_id)
        else:
            menu_plugin = MarkingMenusManager().menu_factory.load_plugin(menu_id)
            new_layout = menu_plugin.execute(marking_menu_layout, arguments=arguments)
            marking_menu_layout.merge(new_layout)

        if new_layout:
            marking_menu_layout = new_layout

        return marking_menu_layout
