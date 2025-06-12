from __future__ import annotations

import os

from . import errors
from .layout import MarkingMenuLayout
from .menu import MarkingMenu, MarkingMenuDynamic
from .command import MarkingMenuCommand
from ...python import modules, jsonio, decorators
from ...plugin import PluginFactory


class MarkingMenusManager(metaclass=decorators.Singleton):
    """
    Class that holds all available marking menu layout classes available.
    """

    MENU_ENV_VAR = "TP_DCC_MARKING_MENU_PATH"
    LAYOUT_ENV_VAR = "TP_DCC_MARKING_MENU_LAYOUT_PATH"
    COMMAND_ENV_VAR = "TP_DCC_MARKING_MENU_COMMAND_PATH"

    STATIC_LAYOUT_TYPE: int = 0
    DYNAMIC_LAYOUT_TYPE: int = 1

    def __init__(self):
        super().__init__()

        self._active_menus: dict[str, MarkingMenu] = {}
        self._layouts: dict[str, MarkingMenuLayout] = {}
        self._menu_factory = PluginFactory(interface=MarkingMenuDynamic, plugin_id="ID")
        self._command_factory = PluginFactory(
            interface=MarkingMenuCommand, plugin_id="ID"
        )

        self.register_marking_menu_layouts_by_env(MarkingMenusManager.LAYOUT_ENV_VAR)
        self._menu_factory.register_paths_from_env_var(MarkingMenusManager.MENU_ENV_VAR)
        self._command_factory.register_paths_from_env_var(
            MarkingMenusManager.COMMAND_ENV_VAR
        )

    @property
    def active_menus(self) -> dict[str, MarkingMenu]:
        """
        Getter that returns the active menus dictionary.

        :return: dict[str, MarkingMenu]
        """

        return self._active_menus

    @property
    def layouts(self) -> dict[str, MarkingMenuLayout]:
        """
        Getter that returns the layouts dictionary.

        :return: dict[str, MarkingMenuLayout]
        """

        return self._layouts

    @property
    def menu_factory(self) -> PluginFactory:
        """
        Getter that returns the menu factory.

        :return: plugin factory instance.
        """

        return self._menu_factory

    @property
    def command_factory(self) -> PluginFactory:
        """
        Getter that returns the command factory.

        :return: plugin factory instance.
        """

        return self._command_factory

    @classmethod
    def find_layout(cls, layout_id: str) -> MarkingMenuLayout | None:
        """
        Returns the layout with the given ID.

        :param layout_id: str, ID of the layout to get.
        :return: MarkingMenuLayout or None
        """

        return cls().layouts.get(layout_id)

    def load_marking_menu_layout_file(self, file_path: str):
        """
        Loads a marking menu layout file and registers it in the manager.

        :param file_path: str, path to the marking menu layout file.
        :raises InvalidMarkingMenuLayoutJsonFileFormatError: If the layout file is
            invalid.
        """

        base_name = os.path.basename(file_path)
        try:
            if file_path.endswith(".mmlayout"):
                if base_name.startswith(modules.MODULE_EXCLUDE_PREFIXES):
                    return
            data = jsonio.read_file(file_path)
            self._layouts[data["id"]] = MarkingMenuLayout(**data)
        except ValueError:
            raise errors.InvalidMarkingMenuLayoutJsonFileFormatError(
                f'Layout file "{file_path}" is invalid possibly due to the formatting'
            )

    def register_marking_menu_layouts_by_env(self, env_var: str):
        """
        Recursively registers all marking menu layout files with the extension
        '.mmlayout' and loads the JSON data with a layout instance, then adds it to
        the layouts cache.

        :param env_var: environment variable that holds the path to the marking
         menu layout files.
        """

        paths = os.environ.get(env_var, "").split(os.pathsep)
        for path in paths:
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        layout_file = os.path.join(root, file)
                        self.load_marking_menu_layout_file(layout_file)
            elif path.endswith(".mmlayout"):
                self.load_marking_menu_layout_file(path)

    def has_menu(self, menu_id: str) -> bool:
        """
        Returns whether a menu with the given ID exists or not.

        :param menu_id: str, ID of the menu to check for.
        :return: bool
        """

        return (
            menu_id not in self._menu_factory.identifiers()
            or menu_id not in self._layouts
        )

    def menu_type(self, menu_id: str) -> int:
        """
        Returns the type of the menu with the given ID.

        :param menu_id: str, ID of the menu to get the type for.
        :return: int
        """

        return (
            MarkingMenusManager.DYNAMIC_LAYOUT_TYPE
            if self._menu_factory.get_plugin_from_id(menu_id) is not None
            else MarkingMenusManager.STATIC_LAYOUT_TYPE
        )
