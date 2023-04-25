#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation to reload modules recursively
"""

import os
import sys
import inspect
import logging
from distutils import sysconfig

from types import ModuleType

SCRIPT_NAME = 'reloader'
DEBUG_LOG_TITLE = '#' + SCRIPT_NAME + ': '

_processed_modules = set()
_reloaded_modules = set()
_remapping_data = list()

_verbosity = 0
_debug_offset = 0
_debug_offset_string = ''

TAB_SIZE = 4

IGNORE_DIRECTORIES = [
    sysconfig.get_python_lib(standard_lib=True).lower(),
    'autodesk\\maya',
    'pythonpackages',
    'pyqt',
    'keyring',
]


logger = logging.getLogger('tpDcc-libs-python')


def debug_log(*args, **kwargs):
    verbosity = kwargs.get('verbosity', 1)
    title = kwargs.get('title', True)
    if verbosity <= _verbosity:
        logger.debug((DEBUG_LOG_TITLE if title else '') + _debug_offset_string + ''.join(args))


def debug_log_empty():
    debug_log('', verbosity=1, title=True)


def change_dbg_offset(amount):
    global _debug_offset, _debug_offset_string
    _debug_offset += amount
    _debug_offset_string = ('|' + ' ' * (TAB_SIZE - 1)) * _debug_offset


def need_to_be_ignored(moduleFilename):
    # This is original check for builtin path. Not valid if run in Maya.

    # pyStdLib = sysconfig.get_python_lib(standard_lib=True).lower()
    # pySitePkg = sysconfig.get_python_lib().lower()
    # if moduleFilepath.startswith(pyStdLib) and (not moduleFilepath.startswith(pySitePkg)):
    #     continue

    module_dir = os.path.dirname(moduleFilename).lower()
    for s in IGNORE_DIRECTORIES:
        if s in module_dir:
            return True
    return False


class ImportRemapData(object):

    def __init__(
            self,
            dest_module_name,
            dest_attr_name,
            source_module_name,
            source_attr_name,
            attr_type
    ):

        self._dest_module_name = dest_module_name
        self._dest_attr_name = dest_attr_name
        self._source_module_name = source_module_name
        self._source_attr_name = source_attr_name
        self._attr_type = attr_type

    def remap(self):
        source_module = sys.modules[self._source_module_name]

        if self._attr_type == ModuleType:
            newAttrVal = sys.modules[self._source_attr_name]
        else:
            newAttrVal = getattr(source_module, self._source_attr_name)

        destModule = sys.modules[self._dest_module_name]
        setattr(destModule, self._dest_attr_name, newAttrVal)


def reloader(module, remapping=False, verbosity=0):

    global _verbosity
    _verbosity = verbosity

    debug_log_empty()
    debug_log('RELOAD STARTED.', verbosity=1)

    do_reload(module, remapping=remapping)

    if remapping:
        debug_log('remapping process begins...', verbosity=1)
        for remapData in _remapping_data:
            remapData.remap()
        debug_log('remapping done.', verbosity=1)
    else:
        debug_log('remapping skipped.', verbosity=1)

    _processed_modules.clear()
    _reloaded_modules.clear()
    del _remapping_data[:]

    debug_log('RELOAD FINISHED.', verbosity=1)
    debug_log('', verbosity=1, title=False)


def do_reload(module, remapping=False):

    change_dbg_offset(1)

    debug_log_empty()
    debug_log(module.__name__, ': START PROCESSING.', verbosity=1)
    debug_log_empty()

    _processed_modules.add(module)

    attr_names = dir(module)
    attr_count = len(attr_names)

    detected_modules = set()

    dbg_phase_title = module.__name__ + ': attribute analyzing phase: '
    debug_log(dbg_phase_title, 'analyzing ', str(attr_count), ' module attributes.', verbosity=1)

    for attrName in attr_names:

        attr_val = getattr(module, attrName)
        attr_module = inspect.getmodule(attr_val)

        if not attr_module:
            debug_log(
                dbg_phase_title, '"', attrName, '"(attr): cannot get module for attribute. Skipped.', verbosity=2)
            continue

        debug_log(
            dbg_phase_title, '"', attrName, '"(attr): attribute belongs to module "',
            attr_module.__name__, '"', verbosity=2)

        if attr_module.__name__ in sys.builtin_module_names:
            debug_log(dbg_phase_title, '"', attr_module.__name__, '"(module): builtin. Skipped.', verbosity=2)
            continue

        if not hasattr(attr_module, '__file__'):
            debug_log(
                dbg_phase_title, '"', attr_module.__name__, '"(module): no "__file__" attribute. Skipped.', verbosity=2)
            continue

        if attr_module == sys.modules[__name__]:
            debug_log(
                dbg_phase_title, '"', attr_module.__name__, '"(module): ', SCRIPT_NAME,
                ' itself. Skipped.', verbosity=2)
            continue

        if attr_module in _processed_modules:
            debug_log(
                dbg_phase_title, '"', attr_module.__name__, '"(module): already processed. Skipped.', verbosity=2)
            continue

        if need_to_be_ignored(attr_module.__file__.lower()):
            debug_log(dbg_phase_title, '"', attr_module.__name__, '"(module): in ignore list. Skipped.', verbosity=2)
            continue

        detected_modules.add(attr_module)
        debug_log(
            dbg_phase_title, '"', attr_module.__name__, '"(module): added to list of detected modules.', verbosity=2)

        if remapping:

            if not hasattr(attr_val, '__name__'):
                continue

            orig_name = attr_val.__name__

            if attr_module != module:
                debug_log(' '.join((dbg_phase_title + 'preparing mapping data:', module.__name__, attrName, '<-',
                                    attr_module.__name__, orig_name, str(type(attr_val)))), verbosity=2)
                remap_data = ImportRemapData(
                    module.__name__,
                    attrName,
                    attr_module.__name__,
                    orig_name,
                    type(attr_val)
                )
                _remapping_data.append(remap_data)

    if _verbosity > 0:
        dbg_phase_title = module.__name__ + ': detected modules summary: '
        debug_log_empty()
        if detected_modules:
            debug_log(dbg_phase_title, 'following modules must be processed:', verbosity=1)
            for md in detected_modules:
                debug_log(md.__name__, )
        else:
            debug_log(dbg_phase_title, 'no modules to process.', verbosity=1)

    debug_log_empty()

    dbg_phase_title = module.__name__ + ': recursion entrance phase: '
    for detectedModule in detected_modules:
        if detectedModule in _reloaded_modules:
            debug_log(
                dbg_phase_title,
                'module "' + detectedModule.__name__ + '" was already reloaded. Skipping recursion.', verbosity=1)
            continue
        debug_log(
            dbg_phase_title,
            'module "' + detectedModule.__name__ + '" is not analyzed. Entering recursion.', verbosity=1)
        do_reload(detectedModule)

    dbg_phase_title = module.__name__ + ': reload phase: '
    if module.__name__ != '__main__':
        debug_log(dbg_phase_title, 'reloading module "' + module.__name__ + '".', verbosity=1)
        try:
            reload(module)
        except Exception:
            return
        _reloaded_modules.add(module)
    else:
        debug_log(dbg_phase_title, 'cannot reload "__main__" module. Skipped', verbosity=1)

    debug_log_empty()
    debug_log(module.__name__, ': PROCESSING FINISHED.', verbosity=1)
    debug_log_empty()

    change_dbg_offset(-1)
