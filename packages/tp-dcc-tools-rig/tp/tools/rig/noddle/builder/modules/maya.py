from __future__ import annotations

import inspect
import importlib

import maya.cmds as cmds

from tp.tools.rig.noddle.builder.graph import registers

importlib.reload(registers)


def load_plugins():
    """
    Loads Noddle editor plugins
    """

    registers.load_plugins()


def registered_nodes() -> dict:
    found_nodes = {}
    for node_id, node_module in registers.NODES_REGISTER.items():
        found_nodes[node_id] = {
            'name': node_module.__name__,
            'path': inspect.getfile(node_module),
            'category': node_module.CATEGORY,
            'palette_label': node_module.PALETTE_LABEL if hasattr(
                node_module, 'PALETTE_LABEL') else node_module.DEFAULT_TITLE,
            'icon': node_module.ICON,
            'is_exec': node_module.IS_EXEC,
            'auto_init_execs': node_module.AUTO_INIT_EXECS,
            'default_title': node_module.DEFAULT_TITLE,
            'unique': node_module.UNIQUE if hasattr(node_module, 'UNIQUE') else False
        }
    return found_nodes


def open_file(file_path: str, force: bool = False) -> bool:
    """
    Open file within DCC scene.

    :param str file_path: absolute file path pointing to a valid Maya file.
    :param bool force: whether to force the opening of the file.
    :return: True if file was opened successfully; False otherwise.
    :rtype: bool
    """

    cmds.file(file_path, open=True, force=force)
    return True


def reference_file(file_path: str) -> bool:
    """
    References file within DCC scene.

    :param str file_path: absolute file path pointing to a valid Maya file.
    :return: True if file was opened successfully; False otherwise.
    :rtype: bool
    """

    cmds.file(file_path, reference=True)
    return True
