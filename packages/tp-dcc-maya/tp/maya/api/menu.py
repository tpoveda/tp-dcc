from __future__ import annotations

from typing import Any

from overrides import override

import maya.cmds as cmds

from tp.core import log
from tp.core.abstract import menu as abstract_menu
from tp.maya.cmds import menu

logger = log.tpLogger


class MayaMenuItem(abstract_menu.AbstractMenuItem):

    @override
    def teardown(self):
        cmds.deleteUI(self._name, menu=True)

    @override(check_signature=False)
    def _default_root_parent(self) -> str:
        if self._parent_path:
            parent_path = menu.compatible_name(self._parent_path)
            return menu.find_menu_by_path(parent_path)

    @override(check_signature=False)
    def _setup_separator(self, parent_native_node: Any) -> str:
        self._name = menu.unique_compatible_name(self._label, parent=parent_native_node)
        self._kwargs.setdefault('divider', True)
        self._kwargs.setdefault('dividerLabel', self._label)
        self._kwargs.setdefault('parent', parent_native_node)
        return cmds.menuItem(self._name, **self._kwargs)

    @override(check_signature=False)
    def _setup_menu_item(self, parent_native_node: Any) -> str:
        self._name = menu.unique_compatible_name(self._label, parent=parent_native_node)
        self._kwargs.setdefault('label', self._label)
        self._kwargs.setdefault('command', self.run)
        self._kwargs.setdefault('parent', parent_native_node)
        self._kwargs.setdefault('image', self._icon or '')
        self._kwargs.setdefault('annotation', self._tooltip or '')
        return cmds.menuItem(self._name, **self._kwargs)

    @override(check_signature=False)
    def _setup_sub_menu(self, parent_native_node: Any) -> str:
        self._name = menu.unique_compatible_name(self._label, parent=parent_native_node)
        self._kwargs.setdefault('tearOff', True)
        if not parent_native_node:
            return menu.create_root_menu(self._label, kwargs=self._kwargs)
        else:
            self._kwargs.setdefault('subMenu', True)
            self._kwargs.setdefault('label', self._label)
            self._kwargs.setdefault('parent', parent_native_node)
            return cmds.menuItem(self._name, **self._kwargs)
