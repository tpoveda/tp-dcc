from __future__ import annotations

import os
import typing
import logging
from typing import Any
from functools import partial

from maya import cmds

from ...qt import icons
from ...plugin import Plugin

if typing.TYPE_CHECKING:
    from .layout import MarkingMenuLayout
    from .manager import MarkingMenusManager

logger = logging.getLogger(__name__)


class MarkingMenu:
    """
    Class that acts a wrap to a Maya marking menu object.
    """

    def __init__(
        self,
        marking_menu_layout: MarkingMenuLayout,
        name: str,
        parent: str,
        marking_menu_manager: MarkingMenusManager,
    ):
        super().__init__()

        self._layout = marking_menu_layout
        self._name = name
        self._parent = parent
        self._manager = marking_menu_manager
        self._popup_menu: str | None = None
        self._command_arguments: dict = {}
        self._options = {
            "allowOptionBoxes": True,
            "altModifier": False,
            "button": 1,
            "ctrlModifier": False,
            "postMenuCommandOnce": True,
            "shiftModifier": False,
        }

        if cmds.popupMenu(self._name, exists=True):
            cmds.deleteUI(self._name)

    @property
    def options(self) -> dict[str, bool]:
        """
        Getter that returns the options of the marking menu.

        :return: dictionary with the options of the marking menu.
        """

        return self._options

    @classmethod
    def build_from_layout_data(
        cls,
        layout_data: MarkingMenuLayout,
        menu_name: str,
        parent: str,
        options: dict[str, Any],
        arguments: list[dict] | None = None,
    ) -> MarkingMenu:
        """
        Creates a new marking menu instance from the given marking menu layout data.

        :param layout_data: marking menu layout data.
        :param menu_name: name of the menu.
        :param parent: parent of the menu.
        :param options: additional options to be passed to the menu.
        :param arguments: additional arguments to base passed to the `attach` or
            `create` methods.
        :return: new marking menu instance.
        :raises ValueError: If the menu already exists.
        """

        from .manager import MarkingMenusManager

        if menu_name in MarkingMenusManager().active_menus:
            if not cmds.popupMenu(menu_name, exists=True):
                del MarkingMenusManager().active_menus[menu_name]
            else:
                raise ValueError(
                    f'Menu "{menu_name}" already exists! '
                    f"Multiple marking menus with the same name are not allowed!"
                )

        new_menu = cls(
            layout_data,
            name=menu_name,
            parent=parent,
            marking_menu_manager=MarkingMenusManager(),
        )
        new_menu.options.update(options)
        if cmds.popupMenu(parent, exists=True):
            new_menu.attach(**arguments or {})
        else:
            new_menu.create(**arguments or {})
        MarkingMenusManager().active_menus[menu_name] = new_menu

        return new_menu

    @staticmethod
    def remove_existing_menu(menu_name: str) -> bool:
        """
        Removes the existing menu with the given name.

        :param menu_name: name of the menu to remove.
        :return: True if the menu was successfully removed; False otherwise.
        """

        marking_menu = MarkingMenusManager().active_menus.get(menu_name)
        if marking_menu is None:
            return False

        marking_menu.shutdown()
        del MarkingMenusManager().active_menus[menu_name]

        return True

    @staticmethod
    def remove_all_active_menus():
        """
        Removes all current active marking menus.
        """

        for menu_name in MarkingMenusManager().active_menus.keys():
            MarkingMenu.remove_existing_menu(menu_name)

        MarkingMenusManager().active_menus.clear()

    def attach(self, **arguments: dict[str, Any]):
        """
        Generates the marking menu using the parent marking menu.

        The given arguments will be passed to each and every menu item command.

        :param arguments: dictionary or keyword arguments to pass to each menu item
            command.
        :return: True if the menu was successfully attached; False otherwise.
        """

        if not cmds.popupMenu(self._parent, exists=True):
            return False

        self._command_arguments = arguments
        self._show(self._parent, self._parent)

        return True

    def create(self, **arguments: dict[str, Any]) -> MarkingMenu:
        """
        Creates a new popup marking menu.

        :param arguments: dictionary or keyword arguments to pass to each menu item
            command.
        :return: instance of this marking menu.
        """

        self.shutdown()

        self._command_arguments = arguments
        self._popup_menu = cmds.popupMenu(
            self._name,
            parent=self._parent,
            markingMenu=True,
            postMenuCommand=self._show,
            **self._options,
        )

        return self

    def add_separator(self, menu: str, item: dict[str, Any] | None = None):
        """
        Adds a separator to the given menu.

        :param menu: name of the menu to add the separator to.
        :param item: name of the item to add the separator after.
        """

        if item and item.get("id"):
            command = self._manager.command_factory.load_plugin(item["id"])
            command_argument_override = dict(**self._command_arguments)
            command_argument_override.update(item.get("arguments", {}))
            ui_data = command.ui_data(command_argument_override)
            ui_data.update(item)
            if ui_data.get("show") is False:
                return

        cmds.menuItem(parent=menu, divider=True)

    def add_command(
        self, item: dict[str, Any], parent: str, radial_position: str | None = None
    ) -> bool:
        """
        Adds the given command to the menu.

        :param item: dictionary with the command data.
        :param parent: name of the parent menu.
        :param radial_position: optional radial position of the command.
        :return: True if the command was successfully added; False otherwise.
        """

        command = self._manager.command_factory.load_plugin(item["id"])
        if command is None:
            logger.warning(f'Failed to load command "{item["id"]}"')
            return False

        command_arg_override = dict(**self._command_arguments)
        command_arg_override.update(item.get("arguments", {}))
        ui_data = command.ui_data(command_arg_override)
        ui_data.update(item)
        try:
            label = ui_data["label"]
        except KeyError:
            logger.error('Command data must have a "label" key!')
            return False
        option_box = ui_data.get("optionBox", False)
        enable = ui_data.get("enable", True)
        show = ui_data.get("show", True)
        checkbox = ui_data.get("checkBox", None)
        radio_button_state = ui_data.get("radioButtonState", False)
        icon_path = ui_data.get("icon", "")
        icon_option_box = ui_data.get("optionBoxIcon", "")
        if not show:
            return True

        arguments = dict(
            label=label,
            parent=parent,
            command=partial(command._execute, command_arg_override, False),
            optionBox=False,
            enable=enable,
        )
        if icon_path:
            new_icon_path = icons.icon_path_for_name(icon_path)
            if new_icon_path:
                icon_path = new_icon_path
            arguments["image"] = icon_path
        if ui_data.get("isRadioButton", False):
            arguments["radioButton"] = radio_button_state
        if ui_data.get("italic", False):
            arguments["italicized"] = True
        if ui_data.get("bold", False):
            arguments["boldFont"] = True
        if radial_position is not None:
            arguments["radialPosition"] = radial_position
        if checkbox is not None:
            arguments["checkBox"] = checkbox

        cmds.menuItem(**arguments)

        if option_box:
            icon_option_box = icons.icon_path_for_name(icon_option_box)
            if os.path.exists(icon_option_box):
                arguments["optionBoxIcon"] = icon_option_box
            arguments.update(
                dict(
                    optionBox=option_box,
                    command=partial(command._execute, command_arg_override, True),
                )
            )
            cmds.menuItem(**arguments)

        return True

    def show(self, layout: MarkingMenuLayout, menu: str, parent: str):
        """
        Shows the marking menu.

        :param layout: marking menu layout to show.
        :param menu: menu full path where commands will be attached to.
        :param parent: parent full path name.
        """

        for item, data in layout.items():
            if not data:
                continue
            if item == "generic":
                self._build_generic(data, menu)
                continue
            elif isinstance(data, MarkingMenuLayout):
                radial_menu = cmds.menuItem(
                    label=data["id"],
                    subMenu=True,
                    parent=menu,
                    radialPosition=item.upper(),
                )
                self.show(data, radial_menu, parent)
            elif data["type"] == "command":
                self.add_command(data, parent=menu, radial_position=item.upper())

    def shutdown(self):
        """
        Destroys the popup marking menu from Maya.
        """

        if cmds.popupMenu(self._name, exists=True):
            cmds.deleteUI(self._name)

    def _show(self, menu: str, parent: str):
        """
        Internal function that shows the marking menu.

        :param menu: name of the menu to show.
        :param parent: name of the parent menu.
        """

        cmds.setParent(menu, menu=True)
        cmds.menu(menu, edit=True, deleteAllItems=True)
        self.show(self._layout, menu, parent)

    def _build_generic(self, data: list[dict[str, Any]], menu: str):
        """
        Internal function that builds a generic menu item.

        :param data: dictionary with the data to build the generic menu item.
        :param menu: name of the menu to attach the generic menu item to.
        """

        for item in data:
            if item["type"] == "command":
                self.add_command(item, menu)
                continue
            elif item["type"] == "menu":
                sub_menu = cmds.menuItem(
                    label=item["label"],
                    subMenu=True,
                    parent=menu,
                )
                self._build_generic(item["children"], sub_menu)
            elif item["type"] == "radioButtonMenu":
                sub_menu = cmds.menuItem(label=item["label"], subMenu=True, parent=menu)
                cmds.radioMenuItemCollection(parent=sub_menu)
                self._build_generic(item["children"], sub_menu)
            elif item["type"] == "separator":
                self.add_separator(menu, item)


class MarkingMenuDynamic(Plugin):
    """
    Class that defines a dynamic marking menu that allows for subclasses to dynamically
    generate the marking menu layout.
    """

    ID = ""
    DOCUMENTATION = __doc__

    def execute(
        self, layout: MarkingMenuLayout, arguments: dict[str, Any]
    ) -> MarkingMenuLayout:
        """
        Function that is called when the marking menu is executed.

        :param layout: marking menu layout instance.
        :param arguments: dictionary with the arguments to use to generate the marking menu.
        :return: marking menu layout instance.
        """

        raise NotImplementedError("execute function must be implemented in subclasses!")
