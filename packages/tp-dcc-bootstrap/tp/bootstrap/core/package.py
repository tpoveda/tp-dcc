#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc tools package manager package implementation
"""

import os
import re
import sys
import copy
import shutil
import logging
from distutils import version

import six

from tp.bootstrap import commands
from tp.bootstrap.utils import fileio, env
from tp.bootstrap.core import consts, exceptions

logger = logging.getLogger('tp-dcc-bootstrap')


class Package(object):
    def __init__(self, package_path=None):
        self._path = package_path or ''
        self._root = ''
        self._environ = dict()
        self._cache = dict()
        self._enabled = True
        self._required = False
        self._version = version.LooseVersion()
        self._name = ''
        self._display_name = ''
        self._description = ''
        self._author = ''
        self._author_email = ''
        self._tokens = dict()
        self._requirements = list()
        self._tests = list()
        self._resolved = False
        self._command_paths = list()
        self._resolved_env = dict()
        self._dccs = dict()

        if package_path is not None and os.path.exists(package_path):
            self._process_file(package_path=package_path)

    def __hash__(self):
        return hash(id(self))

    def __repr__(self):
        return self.get_search_str()

    def __eq__(self, other):
        if other is None or not isinstance(other, Package):
            return False
        return self.name == other.name and self.version == other.version

    def __ne__(self, other):
        return not self.__eq__(other)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def path(self):
        return self._path

    @property
    def root(self):
        return self._root

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value

    @property
    def requirements(self):
        return self._requirements

    @property
    def required(self):
        return self._required

    @property
    def dccs(self):
        return self._dccs

    # =================================================================================================================
    # CLASS / STATIC METHODS
    # =================================================================================================================

    @staticmethod
    def get_name_from_package_name_and_version(package_name, package_version):
        return '-'.join([package_name, package_version])

    @classmethod
    def from_data(cls, data):
        new_package = cls()
        new_package._process_data(data)
        return new_package

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def copy_to(self, destination):
        if os.path.exists(destination):
            raise FileNotFoundError(destination)
        shutil.copytree(self.get_dirname(), destination, ignore=shutil.ignore_patterns(*consts.FILE_FILTER_EXCLUDE))
        return self.__class__(os.path.join(destination, consts.PACKAGE_NAME))

    def get_dirname(self):
        return os.path.dirname(self._path)

    def get_search_str(self):
        try:
            return self.name + '-' + str(self.version)
        except AttributeError:
            return self.path + '- (Fail)'

    def set_name(self, name):
        self._name = name
        self.save()

    def set_path(self, path):
        self._path = os.path.normpath(path)
        self._root = os.path.dirname(path)

    def set_version(self, version_str):
        self._version = version.LooseVersion(version_str)
        self._cache['version'] = str(self._version)

    def set_enabled(self, flag):
        self._enabled = flag

    def resolve(self, apply_environment=True):
        environ = self._environ
        if not environ:
            logger.warning(f'Unable to resolve package environment due to invalid package: {self.path}')
            return False
        if self._dccs:
            if not env.application() in self._dccs:
                logger.debug(
                    f'Skipping package resolving because is not compatible with current DCC: {env.application()}')
                return False
            if self._dccs[env.application()] and env.application_version() not in self._dccs[env.application()]:
                logger.debug('Skipping package resolving because is not compatible with current '
                             f'DCC version: {env.application()} {env.application_version()}')
                return False

        self._command_paths = Variable('commands', self._command_paths).solve(**self._tokens)
        pkg_variables = dict()
        for key, paths in environ.items():
            var = Variable(key, [paths] if isinstance(paths, six.string_types) else paths)
            var.solve(**self._tokens)
            if apply_environment and key != 'PYTHONPATH':
                env.add_to_env(key, var.values)
            pkg_variables[key] = var
        if apply_environment and 'PYTHONPATH' in pkg_variables:
            for py_var in pkg_variables['PYTHONPATH'].values:
                py_var = env.clean_path(py_var)
                if py_var not in sys.path:
                    sys.path.append(py_var)
        self._resolved_env = pkg_variables
        logger.debug(f'Resolved {self.name}: {self.root}')
        self._resolved = True

    def run_startup(self):
        logger.debug(f'Running Startup: {self.name} | {self._command_paths}')
        for command_path in self._command_paths:
            if not os.path.exists(command_path):
                return
            mod_name = os.path.basename(command_path).split(os.extsep)[0]
            logger.debug(f'Importing package startup file: {command_path}')
            mod = commands.import_module(mod_name, os.path.realpath(command_path))
            if mod and hasattr(mod, 'startup'):
                logger.debug(f'Running startup function for module: {command_path}')
                mod.startup(self)
            if mod_name in sys.modules:
                del sys.modules[mod_name]

    def save(self):
        data = self._cache
        data.update(
            version=str(self._version), name=self._name, displayName=self._display_name, description=self._description,
            requirements=self._requirements, author=self._author, authorEmail=self._author_email)
        return fileio.save_yaml(data, self._path)

    def delete(self):
        if not os.path.exists(self.root):
            return False
        try:
            shutil.rmtree(self.root)
        except OSError:
            logger.error(f'Failed to remove package: {os.path.dirname(self.name)}', exc_info=True)

        return True

    def shutdown(self):
        _logger = logging.getLogger('tp-dcc-bootstrap')
        _logger.debug(f'Shutting down package: {self}')
        _logger.debug(f'\tCommand Paths: {self._command_paths}')
        for command_path in self._command_paths:
            if not os.path.exists(command_path):
                continue
            mod_name = os.path.basename(os.path.splitdrive(command_path)[0])
            _logger.debug(f'Importing package startup file: {command_path}')
            mod = commands.import_module(mod_name, os.path.realpath(command_path))
            _logger = logging.getLogger('tp-dcc-bootstrap')
            _logger.warning(f'Found mod: "{mod}" ...')
            if hasattr(mod, 'shutdown'):
                _logger.debug(f'Running shutdown function for module: {command_path}')
                mod.shutdown(self)
            # if mod_name in sys.modules:
            #     del sys.modules[mod_name]
        _logger.debug(f'Package shutdown completed: {self}')

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _process_file(self, package_path):
        self.set_path(package_path)
        try:
            data = fileio.load_yaml(self.path)
        except ValueError:
            logger.error(f'Failed to load package due to possible syntax error, {package_path}')
            data = dict()
        self._process_data(data)

    def _process_data(self, data):
        self._environ = data.get('environment', dict())
        self._cache = copy.deepcopy(data)
        self._version = version.LooseVersion(data.get('version', ''))
        self._required = data.get('required', False)
        self._name = data.get('name', 'NO_NAME')
        self._display_name = data.get('displayName', 'NO_NAME')
        self._description = data.get('description', 'No description')
        self._tokens = {'selftoken': self._root}
        self._requirements = data.get('requirements', list())
        self._command_paths = data.get('commands', list())
        self._tests = Variable('tests', data.get('tests', list())).solve(**self._tokens)
        self._author = data.get('author', '')
        self._author_email = data.get('authorEmail', '')
        self._dccs = data.get('dccs', dict())


class Variable(object):
    def __init__(self, key, values):
        self._key = key
        self._values = values
        self._original_values = values
        env_var = os.getenv(key)
        if env_var:
            self._values.extend([i for i in env_var.split(os.pathsep)])

    def __str__(self):
        if len(self._values) > 1:
            return os.pathsep.join(self._values)
        return self._values[0]

    @property
    def values(self):
        return self._values

    def split(self, sep):
        return str(self).split(sep)

    def dependencies(self):
        results = set()
        for i in self._values:
            results.union(set(re.findall(consts.DEPENDENT_FILTER, i)))

        return results

    def solve(self, **tokens):
        self_path = tokens['selftoken']
        app = env.application().lower()
        app_version = str(env.application_version())
        py_version_name = 'py3' if env.is_python3() else 'py2'
        project = os.environ.get('TPDCC_PROJECT', '') or 'undefined'
        result = [i.replace(
            consts.PACKAGE_FOLDER_TOKEN, self_path).replace(
            consts.APP_NAME_TOKEN, app).replace(
            consts.PROJECT_NAME_TOKEN, project).replace(
            consts.APP_VERSION_TOKEN, app_version).replace(
            consts.PY_VERSION_NAME_TOKEN, py_version_name) for i in self._values]
        self._values = result

        return result
