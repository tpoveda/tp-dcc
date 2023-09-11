import unreal

from overrides import override

from tp.core import log
from tp.core.abstract import menu as abstract_menu
from tp.unreal.ui import menu

logger = log.tpLogger


class UnrealMenuItem(abstract_menu.AbstractMenuItem):

    @override(check_signature=False)
    def setup(self, parent_native_node: unreal.ToolMenu | None = None, backlink: bool = True) -> unreal.ToolMenu:
        native_node = super().setup(parent_native_node, backlink=False)
        unreal.ToolMenus.get().refresh_all_widgets()
        return native_node

    @override
    def teardown(self):
        raise NotImplementedError

    @override(check_signature=False)
    def _default_root_parent(self) -> unreal.ToolMenu:
        self._parent_path = self._parent_path or 'LevelEditor.MainMenu'
        return unreal.ToolMenus.get().find_menu(self._parent_path)

    @override(check_signature=False)
    def _setup_separator(self, parent_native_node: unreal.ToolMenu | None = None) -> unreal.ToolMenu:
        # TODO: Make this work
        return parent_native_node.add_section(
            section_name=self._label + "_section", label=self._label + "_label", **self._kwargs)

    @override(check_signature=False)
    def _setup_menu_item(self, parent_native_node: unreal.ToolMenu | None = None) -> unreal.ToolMenuEntry:
        if menu.check_menu_exists(self.name_path()):
            parent_label = self.parent.label if self.parent.label else None
            logger.warning(f'Menu already exists: {self.name_path()}. Parent is {parent_label}')
            raise Exception(f'Menu item "{self.label}" already exists, stopping menu item setup.')

        self._kwargs.setdefault('type', unreal.MultiBlockType.MENU_ENTRY)
        self._kwargs.setdefault('insert_position',  unreal.ToolMenuInsert('', unreal.ToolMenuInsertType.FIRST))

        # convenient hack to support kwargs for both unreal.ToolMenuEntry, and setting section_name for
        # unreal.ToolMenu.add_sub_menu same kwarg name as section_name kwarg from add_sub_menu
        section_name = self._kwargs.pop("section_name", "Scripts")

        entry = unreal.ToolMenuEntry(name=self.id, **self._kwargs)
        if self.label:
            entry.set_label(self.label)
        if self.command:
            entry.set_string_command(
                type=unreal.ToolMenuStringCommandType.PYTHON,
                string=self.command,
                custom_type=unreal.Name("_placeholder_"),
            )  # hack: unsure what custom_type does, but it's needed
        if self.tooltip:
            entry.set_tool_tip(self.tooltip)
        if self.icon:
            entry.set_icon(self.icon)  # naive implementation todo improve

        parent_native_node.add_menu_entry(section_name, entry)
        return entry

    @override(check_signature=False)
    def _setup_sub_menu(self, parent_native_node: unreal.ToolMenu | None = None) -> str:
        if menu.check_menu_exists(self.name_path()):
            parent_label = self.parent.label if self.parent.label else None
            logger.warning(f'Menu already exists: {self.name_path()}. Parent is {parent_label}')
            raise Exception(f'Menu "{self.label}" already exists, stopping menu setup.')

        self._kwargs.setdefault("section_name", "PythonTools")

        return parent_native_node.add_sub_menu(
            owner=parent_native_node.menu_name,
            name=self.id,  # TODO: check if needs to be unique like in add_to_menu
            label=self.label,  # TODO: add label support
            tool_tip=self.tooltip,
            **self._kwargs,
        )

    def name_path(self) -> str:
        """
        Returns menu path.

        :return: menu path.
        :rtype: str
        """

        if self.parent:
            return f'{self.parent.name_path()}.{self.id}'
        elif self.parent_path:
            return f'{self.parent_path}.{self.id}'
        else:
            return self.id
