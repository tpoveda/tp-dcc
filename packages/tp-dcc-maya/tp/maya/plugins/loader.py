#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tp-dcc-maya Maya plugins loader functions
"""

import os
import inspect

from tp.core import log
from tp.common.python import osplatform, path
from tp.maya.cmds import helpers
from tp.maya.plugins import apiundo

logger = log.tpLogger


def get_root_path() -> str:
    return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def load_all_plugins(reload=False):
    load_tpundo_plugin(reload=reload)
    load_apiundo_plugin(reload=reload)
    load_tpasset_plugin(reload=reload)


def unload_all_plugins():
    unload_tpasset_plugin()
    unload_apiundo_plugin()
    unload_tpundo_plugin()


def load_tpundo_plugin(reload=False):
    helpers.add_trusted_plugin_location_path(get_root_path())
    plugin_name = 'tpundo.py'
    plugin_path = path.join_path(get_root_path(), 'tpundo', 'python', plugin_name)
    return _load_plugin(plugin_name, plugin_path, reload=reload, add_to_trusted_paths=False)


def unload_tpundo_plugin():
    return _unload_plugin('tpundo.py')


def load_apiundo_plugin(reload=False):
    helpers.add_trusted_plugin_location_path(get_root_path())
    plugin_name = 'apiundo.py'
    plugin_path = path.join_path(get_root_path(), 'apiundo.py')
    logger.info('Loading Maya Plugin: {} : {}'.format(plugin_name, plugin_path))
    try:
        if reload:
            apiundo.reinstall()
        else:
            apiundo.install()
    except Exception as exc:
        logger.error('Failed to {} plugin: {}'.format(plugin_name, exc))
        return False

    return True


def unload_apiundo_plugin():
    plugin_name = 'apiundo.py'
    logger.info('Unloading Maya Plugin: {} : {}'.format(plugin_name, plugin_name))
    try:
        apiundo.uninstall()
    except Exception as exc:
        logger.error('Failed to unload {} plugin! {}'.format(plugin_name, exc))
        return False

    return True


def load_tpasset_plugin(reload=False):
    helpers.add_trusted_plugin_location_path(get_root_path())
    plugin_name = 'tpasset.py'
    plugin_path = path.join_path(get_root_path(), 'tpasset', 'python', plugin_name)
    return _load_plugin(plugin_name, plugin_path, reload=reload, add_to_trusted_paths=False)


def unload_tpasset_plugin():
    return _unload_plugin('tpasset.py')


def _load_plugin(plugin_name, plugin_path=None, reload=False, add_to_trusted_paths=True):
    logger.info('Loading Maya Plugin: {} : {}'.format(plugin_name, plugin_path))
    try:
        if path.is_dir(plugin_path):
            osplatform.append_path_env_var('MAYA_PLUG_IN_PATH', plugin_path)
        if not helpers.is_plugin_loaded(plugin_name):
            helpers.load_plugin(plugin_path)
        elif helpers.is_plugin_loaded(plugin_name) and reload:
            helpers.unload_plugin(os.path.basename(plugin_name))
            helpers.load_plugin(plugin_name)
        if path.is_dir(plugin_path) and add_to_trusted_paths:
            helpers.add_trusted_plugin_location_path(plugin_path)
        return True
    except Exception as exc:
        logger.error('Failed to {} plugin: {}'.format(plugin_name, exc))

    return False


def _unload_plugin(plugin_name):
    logger.info('Unloading Maya Plugin: {} : {}'.format(plugin_name, plugin_name))
    try:
        if helpers.is_plugin_loaded(plugin_name):
            helpers.unload_plugin(os.path.basename(plugin_name))
        return True
    except Exception as exc:
        logger.error('Failed to unload {} plugin! {}'.format(plugin_name, exc))

    return False
