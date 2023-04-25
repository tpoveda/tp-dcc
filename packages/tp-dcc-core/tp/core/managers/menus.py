#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for DCC menus
"""

import logging
from functools import partial

from tp.core import dcc
from tp.core.managers import resources
from tp.common.python import helpers
from tp.common.qt import menu
from tp.common.qt.managers import toolsets

_MENUS = dict()
_MENU_NAMES = dict()
_OBJECT_MENU_NAMES = dict()

logger = logging.getLogger('tpDcc-core')


def get_menu(menu_name, package_name=None):
    """
    Returns menu object if exists
    :param package_name: str
    :param menu_name: str
    :return: QMenu
    """

    for pkg_name, _ in _MENUS.items():
        if package_name and pkg_name != package_name:
            continue
        # if menu_name == self._menu.objectName():
        #     return self._menus[menu_name]

    return _MENUS.get(package_name, dict()).get(menu_name, None)


def create_main_menu(package_name, force_creation=True, icon=None):
    """
    Creates main menu for given package
    :param package_name: str
    :param force_creation: bool
    :param icon: QIcon
    """

    if not package_name:
        return None

    object_menu_name = _OBJECT_MENU_NAMES[
        package_name] if package_name in _OBJECT_MENU_NAMES else '{}_Menu'.format(package_name)
    if package_name in _MENUS and _MENUS.get(package_name, None) and object_menu_name in _MENUS[package_name]:
        if not force_creation:
            return _MENUS[package_name][object_menu_name]
    remove_previous_menus(package_name=package_name)
    menu_name = _MENU_NAMES[package_name] if package_name in _MENU_NAMES else package_name

    main_win = dcc.get_main_window()
    parent_menu_bar = main_win.menuBar() if main_win else None
    if not parent_menu_bar:
        logger.warning(
            'Impossible to create Tools main menu for "{}" because not found menu bar to attach menu to!'.format(
                package_name))
        return None
    main_menu = menu.SearchableMenu(objectName=object_menu_name, title=menu_name, parent=parent_menu_bar)
    if icon:
        main_menu.setIcon(icon)
    parent_menu_bar.addMenu(main_menu)
    main_menu.setObjectName(object_menu_name)
    main_menu.setTearOffEnabled(True)
    _MENU_NAMES.setdefault(package_name, list())
    _MENUS.setdefault(package_name, dict())
    _MENUS[package_name].setdefault(object_menu_name, main_menu)
    _MENU_NAMES[package_name].append(object_menu_name)

    return main_menu


def create_menus(package_name, dev=False, icon=None, force_main_menu_creation=True):
    """
    Loops through all loaded plugins and creates a menu/action for each one.
    Function that should be implemented in specific DCC Menu Managers to create proper menu
    """

    def _menu_creator(parent_menu, data):
        """
        Internal function that manages the creation of the menus
        :param parent_menu: QWidget
        :param data:
        :return:
        """

        def _add_action(item_info, parent):

            item_type = item_info.get('type', 'tool')
            if item_type == 'tool' or item_type == 'toolset':
                _add_tool_action(item_info, parent)
            else:
                _add_menu_item_action(item_info, parent)

        def _add_menu_item_action(item_info, parent):
            menu_item_id = item_info.get('id', None)

            menu_item_ui = item_info.get('ui', None)
            if not menu_item_ui:
                logger.warning('Menu Item "{}" has not a ui specified!. Skipping ...'.format(menu_item_id))
                return
            menu_item_command = item_info.get('command', None)
            if not menu_item_command:
                logger.warning(
                    'Menu Item "{}" does not defines a command to execute. Skipping ...'.format(menu_item_id))
                return
            menu_item_language = item_info.get('language', 'python')

            menu_item_icon_name = menu_item_ui.get('icon', 'tpDcc')
            menu_item_icon = resources.icon(menu_item_icon_name)
            menu_item_label = menu_item_ui.get('label', 'No_label')
            is_checkable = menu_item_ui.get('is_checkable', False)
            is_checked = menu_item_ui.get('is_checked', False)
            tagged_action = menu.SearchableTaggedAction(label=menu_item_label, icon=menu_item_icon, parent=parent)
            if is_checkable:
                tagged_action.setCheckable(is_checkable)
                tagged_action.setChecked(is_checked)
                tagged_action.connect(partial(launch_command, menu_item_command, menu_item_language))
                tagged_action.toggled.connect(partial(launch_command, menu_item_command, menu_item_language))
                if menu_item_ui.get('load_on_startup', False):
                    launch_command(menu_item_command, menu_item_language, is_checked)
            else:
                tagged_action.triggered.connect(partial(launch_command, menu_item_command, menu_item_language))
                if menu_item_ui.get('load_on_startup', False):
                    launch_command(menu_item_command, menu_item_language)

            tagged_action.tags = set(item_info.get('tags', []))

            parent.addAction(tagged_action)

        def _add_tool_action(item_info, parent):
            tool_id = item_info.get('id', None)
            tool_type = item_info.get('type', 'tool')

            # NOTE: Here we don't pass the package for now. If we pass a package, for example, tpRigTooklit, tpDcc
            # packages will not be added to the menu
            tool_config = configs.get_tool_config(tool_id)
            if not tool_config:
                return

            tool_menu_ui_data = tool_config.data.get('menu_ui', {})
            tool_icon_name = tool_menu_ui_data.get('icon', '')
            if not tool_icon_name:
                tool_icon_name = tool_config.data.get('icon', None)
            if not tool_icon_name:
                tool_icon_name = 'tpDcc'
            tool_icon = resources.icon(tool_icon_name)
            if not tool_icon or tool_icon.isNull():
                tool_icon = resources.icon('tpDcc')

            label = tool_menu_ui_data.get('label', 'No_label')
            tagged_action = menu.SearchableTaggedAction(label=label, icon=tool_icon, parent=parent)
            is_checkable = tool_menu_ui_data.get('is_checkable', False)
            is_checked = tool_menu_ui_data.get('is_checked', False)
            if is_checkable:
                tagged_action.setCheckable(is_checkable)
                tagged_action.setChecked(is_checked)
                # tagged_action.connect(partial(self._launch_tool, tool_data))
                tagged_action.toggled.connect(partial(_launch_tool_by_id, tool_id))
            else:
                tagged_action.triggered.connect(partial(_launch_tool_by_id, tool_id))

            icon = tool_menu_ui_data.get('icon', 'tpDcc')
            if icon:
                pass

            tagged_action.tags = set(tool_config.data.get('tags', []))

            parent.addAction(tagged_action)

        def _launch_tool_by_id(tool_id, **kwargs):
            """
            Internal function that launch a tool by its ID
            :param tool_id: str
            :param kwargs: dict
            """

            do_reload = kwargs.get('do_reload', False)

            tools.ToolsManager().launch_tool_by_id(tool_id, do_reload=do_reload)

        if 'label' not in data:
            return
        found_menu = get_menu(data['label'], package_name=package_name)
        if found_menu is None and data.get('type', '') == 'menu':
            only_dev = data.get('only_dev', False)
            if only_dev and dev:
                return
            icon_name = data.get('icon', None)
            found_menu = parent_menu.addMenu(data['label'])
            found_menu.setObjectName(data['label'])
            found_menu.setTearOffEnabled(True)
            if icon_name:
                icon = resources.icon(icon_name)
                if icon:
                    found_menu.setIcon(icon)
            _MENUS.setdefault(package_name, dict())
            _MENUS[package_name][data['label']] = found_menu

        if 'children' not in data:
            return

        for child in iter(data['children']):
            action_type = child.get('type', 'command')
            only_dev = child.get('only_dev', False)
            if only_dev and not dev:
                continue
            if action_type == 'separator':
                found_menu.addSeparator()
                continue
            elif action_type == 'group':
                sep = found_menu.addSeparator()
                sep.setText(child['label'])
                continue
            elif action_type == 'menu':
                _menu_creator(found_menu, child)
                continue
            _add_action(child, found_menu)

    main_menu = create_main_menu(package_name=package_name, icon=icon, force_creation=force_main_menu_creation)
    if not main_menu:
        logger.warning('Impossible to create main menu for "{}"'.format(package_name))
        return False

    toolset_menus = toolsets.ToolsetsManager().toolset_menu(package_name=package_name)
    for toolset_menu in toolset_menus:
        for i in iter(toolset_menu):
            if helpers.is_string(i) and i == 'separator':
                main_menu.addSeparator()
                continue
            _menu_creator(main_menu, i)

    return True


def get_tools_menus():
    """
    Returns dictionary with the menu info for all the registered tools
    :return: dict
    """

    tool_menus = dict()

    for package_name, package_data in tools.ToolsManager().plugins.items():
        for tool_name, tool_data in package_data.items():
            tool_config = tool_data['config']
            if not tool_config:
                continue
            menu_data = tool_config.data.get('menu', None)
            if not menu_data:
                continue
            if package_name not in tool_menus:
                tool_menus[package_name] = dict()

            tool_menus[package_name][tool_name] = menu_data

    return tool_menus


def remove_previous_menus(package_name=None, parent=None):
    """
    Removes any DCC tool menu from DCC by iterating through the children of the main window looking for any widget
    with proper objectName
    """

    logger.info('Closing menus for: {}'.format(package_name))

    deleted_menus = list()
    parent = parent or dcc.get_main_window()
    if not parent:
        return

    object_menu_name = _OBJECT_MENU_NAMES[
        package_name] if package_name in _OBJECT_MENU_NAMES else '{}_Menu'.format(package_name)

    if not parent:
        return

    for child_widget in parent.menuBar().children():
        child_name = child_widget.objectName()
        for pkg_name, menus_data in _MENUS.items():
            if package_name and pkg_name != package_name:
                continue
            for menu_name, menu_wigdet in menus_data.items():
                if child_name == menu_wigdet.objectName():
                    child_action = child_widget.menuAction()
                    parent.menuBar().removeAction(child_action)
                    child_action.deleteLater()
                    child_widget.deleteLater()
                    _MENUS.pop(package_name)
                    deleted_menus.append(child_name)
        if child_name == object_menu_name and child_name not in deleted_menus:
            child_action = child_widget.menuAction()
            parent.menuBar().removeAction(child_action)
            child_action.deleteLater()
            child_widget.deleteLater()


def launch_command(command, language='python', *args, **kwargs):
    """
    Internal function that launches the given command
    :param command: str
    :param args: list
    :param kwargs: dict
    """

    if language == 'python':
        exec(command)
    else:
        raise NotImplementedError('Commands of of language "{}" are not supported!'.format(language))
