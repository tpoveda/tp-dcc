#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager that handles the registration of new tpRigToolkit plugins
"""

from tp.core import log, dcc, plugin
from tp.common.python import helpers

logger = log.tpLogger

_PLUGIN_CLASSES = dict()
_PLUGINS = dict()


def plugin_classes(package_name):
    if package_name not in _PLUGIN_CLASSES:
        return list()
    return _PLUGIN_CLASSES[package_name]


def get_registered_plugins(package_name, class_name_filters=None):
    """
    Returns a list with all registered plugin instances
    :param package_name: str
    :param class_name_filters: str, String to filter plugins to search for
    :return: list(str)
    """

    if package_name not in _PLUGINS:
        return list()

    class_name_filters = helpers.force_list(class_name_filters)

    if not class_name_filters:
        return _PLUGINS[package_name]

    result = list()
    for plugin_inst in _PLUGINS[package_name]:
        if plugin_inst.__class__.__name__ in class_name_filters:
            result.append(plugin_inst)

        return result


def is_plugin_opened(package_name, plugin_name):
    """
    Returns whether or not a plugin with given name is already opened
    :param package_name: str
    :param plugin_name: str
    :return: bool
    """

    if package_name not in _PLUGINS:
        return False

    return plugin_name in [t.NAME for t in _PLUGINS[package_name]]


def close_all_package_plugins(package_name):
    """
    Closes all plugins of a specific package
    :param package_name: str
    """

    if package_name not in _PLUGINS:
        return False

    plugins_to_close = _PLUGINS[package_name]
    _PLUGINS.pop(package_name)
    for plugin_instance in plugins_to_close:
        plugin_instance.close()


def get_plugin_instance(package_name, plugin_name):
    """
    Returns plugin instance of the given plugin
    :param package_name: str
    :param plugin_name: str
    :return: list(object)
    """

    if package_name not in _PLUGINS:
        return None

    plugins_found = list()
    for plugin_instance in _PLUGINS[package_name]:
        if plugin_instance.NAME == plugin_name:
            plugins_found.append(plugin_instance)

    return plugins_found


def register_plugin_class(package_name, plugin_class):
    """
    Registers given tool class
    :param package_name: str
    :param plugin_class: cls
    """

    _PLUGIN_CLASSES.setdefault(package_name, list())
    if not plugin_class or plugin_class in _PLUGIN_CLASSES[package_name]:
        return

    _PLUGIN_CLASSES[package_name].append(plugin_class)


def invoke_dock_plugin_by_name(package_name, plugin_name, parent_window=None, settings=None, **kwargs):
    plugin_class = None
    parent_window = parent_window or dcc.get_main_window()

    if package_name not in _PLUGIN_CLASSES:
        logger.warning('Plugin Package with name "{}" not registered'.format(package_name))
        return None

    for t in _PLUGIN_CLASSES[package_name]:
        if t.NAME == plugin_name:
            plugin_class = t
            break
    if not plugin_class:
        logger.warning('No registered tool found with name: "{}"'.format(plugin_name))
        return None

    _PLUGINS.setdefault(package_name, set())
    tool_instance = plugin.create_plugin_instance(plugin_class, _PLUGINS[package_name], **kwargs)
    if not tool_instance:
        return None
    if plugin_class.NAME in [t.NAME for t in _PLUGINS[package_name]] and plugin_class.IS_SINGLETON:
        return tool_instance

    register_plugin_instance(package_name, tool_instance)

    if settings:
        tool_instance.restore_state(settings)
        # if not restoreDockWidget(tool_instance):
        #     pass
    else:
        parent_window.addDockWidget(tool_instance.DEFAULT_DOCK_AREA, tool_instance)

    tool_instance.app = parent_window
    tool_instance.show_plugin()

    return tool_instance


def register_plugin_instance(package_name, instance):
    """
    Internal function that registers given plugin instance
    Used to prevent plugin classes being garbage collected and to save plugin widgets states
    :param package_name: str
    :param instance: Tool
    """

    _PLUGINS.setdefault(package_name, set())
    instance.PACKAGE_NAME = package_name
    _PLUGINS[package_name].add(instance)


def unregister_plugin_instance(instance):
    """
    function that unregister plugin instance
    :param package_name: str
    :param instance: Tool
    """

    if not hasattr(instance, 'PACKAGE_NAME'):
        return False

    package_name = getattr(instance, 'PACKAGE_NAME')

    if package_name not in _PLUGINS or instance not in _PLUGINS[package_name]:
        return False

    _PLUGINS[package_name].remove(instance)

    return True
