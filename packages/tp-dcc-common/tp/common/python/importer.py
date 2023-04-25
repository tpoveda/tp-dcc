#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains basic class for Python importers
"""

import os
import sys
import pkgutil
import traceback
import importlib
from collections import OrderedDict

from tp.common.python import helpers


def import_module(module_name):
    """
    Static function used to import a function given its complete name
    :param module_name: str, name of the module we want to import
    """

    try:
        mod = importlib.import_module(module_name)
        # print('Imported: {} | {}'.format(module_name, mod))
        return mod
    except Exception:
        try:
            print('FAILED IMPORT: {} -> {}'.format(str(module_name), str(traceback.format_exc())))
        except Exception:
            print('FAILED IMPORT: {}'.format(module_name))


def reload_module(module_to_reload):
    """
    Reloads given module
    :param module_to_reload: mode
    """

    if sys.version[0] <= '2':
        reload(module_to_reload)
    else:
        importlib.reload(module_to_reload)


def import_submodules(package_dot_path, skip_modules, recursive=True):
    """
    Import all the modules of the package
    """

    extra_skip = tuple(['{}.'.format(mod) for mod in skip_modules])

    def _import_submodules(pkg):

        found_modules = list()

        if helpers.is_string(pkg):
            pkg = import_module(pkg)
        if not pkg:
            return found_modules

        pkg_paths = tuple([os.path.normpath(pkg_path) for pkg_path in pkg.__path__ if pkg is not None])
        for pkg_path in list(pkg_paths):
            for loader, name, is_pkg in pkgutil.walk_packages(pkg_paths):
                loader_path = os.path.normpath(loader.path)
                full_name = pkg.__name__ + '.' + name
                if not loader_path.startswith(pkg_path):
                    # print('Trying to import non valid module: {} | {}'.format(full_name, loader_path))
                    continue
                if full_name in skip_modules or full_name.startswith(extra_skip):
                    # print('Skipping .... {}'.format(full_name))
                    continue
                found_modules.append(full_name)
                if recursive and is_pkg:
                    found_modules.extend(_import_submodules(full_name))

        return found_modules

    modules_to_import = [package_dot_path]
    modules_to_import.extend(list(set(_import_submodules(package_dot_path))))

    loaded_modules = OrderedDict()

    for full_name in modules_to_import:
        loaded_modules[full_name] = import_module(full_name)

    return loaded_modules


class PackageImporter(object):
    """
    Base class that allows to import/reload all the modules in a given package and in a given order
    """

    def __init__(self, package):
        super(PackageImporter, self).__init__()

        self._package = package

        self.loaded_modules = OrderedDict()
        self.reload_modules = list()

    def import_package(self, skip_modules=None):
        skip_modules = skip_modules if skip_modules else list()
        skip_modules = tuple(mod for mod in skip_modules)

        return import_submodules(self._package, skip_modules=skip_modules)


def init_importer(package, skip_modules=None):
    """
    Initializes importer
    :param package:
    :param skip_modules: bool
    :return:
    """

    new_importer = PackageImporter(package)
    new_importer.import_package(skip_modules=skip_modules)

    return new_importer
