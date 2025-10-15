from __future__ import annotations

import typing
from functools import partial

from loguru import logger
from Qt.QtWidgets import QMenu
from Qt.QtGui import QIcon

from tp.libs.python.paths import canonical_path

if typing.TYPE_CHECKING:
    from ..ui.widgets.editor import NodeGraphEditor
    from ..ui.core.editor_command import NodeGraphEditorCommand


def fill_menu_from_commands_layout(
    editor: NodeGraphEditor,
    layout: list[str],
    menu: QMenu,
):
    """Fill a menu with commands from a layout.

    Args:
        editor: The node graph editor instance.
        layout: The layout of the commands.
        menu: The menu to fill.
    """

    for (
        command_class,
        command_type,
        variant_id,
    ) in editor.commands_manager.iterate_commands_from_layout(layout):
        if command_type == "PLUGIN":
            command = command_class(editor=editor)
            if not command.is_visible():
                continue
            add_command_to_menu(
                editor,
                command,
                menu,
                variant_id=variant_id,
            )
        elif command_type == "SEPARATOR":
            menu.addSeparator()


def add_command_to_menu(
    editor: NodeGraphEditor,
    command: NodeGraphEditorCommand,
    menu: QMenu,
    variant_id: str | None = None,
):
    """Add a command to a menu.

    Args:
        editor: The node graph editor instance.
        command: The command to add.
        menu: The menu to add the command to.
        variant_id: The variant ID of the command to add. If None, the default
            variant will be used.
    """

    ui_data = command.ui_data
    label = ui_data["label"]
    icon_name = ui_data["icon"]
    shortcut = ui_data.get("shortcut", None)
    checkable = ui_data.get("checkable", False)

    if variant_id:
        try:
            variant = [x for x in command.variants() if x["id"] == variant_id][0]
            label = variant["name"]
            icon_name = variant.get("icon", icon_name)
            shortcut = variant.get("shortcut", shortcut)
        except IndexError:
            logger.warning(
                f'Variant ID "{variant_id}" not found for command "{command}"'
            )
            return
        except Exception:
            raise Exception(f"Variant ID '{variant_id}' doesn't exist for '{command}'")

    command_icon = QIcon(canonical_path(f"../resources/icons/{icon_name}"))
    action = menu.addAction(label)
    action.setIcon(command_icon)
    action.setCheckable(checkable)
    action.setChecked(command.is_checked())
    if shortcut:
        action.setShortcut(shortcut)
    action.setProperty("command", command)
    action.setProperty("variant", variant_id)

    # noinspection PyUnresolvedReferences
    action.triggered.connect(partial(editor.execute_command, command, variant_id))
