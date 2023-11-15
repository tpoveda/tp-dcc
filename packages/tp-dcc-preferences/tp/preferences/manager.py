#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Preferences manager class implementation
"""

from __future__ import annotations

import os
import copy
import timeit
import shutil
from typing import Any
from collections import OrderedDict

from tp.bootstrap import api
from tp.core import consts, log
from tp.common import plugin
from tp.common.python import strings, path, folder, yamlio, helpers

from tp.preferences import errors, preference as core_preference

logger = log.tpLogger

_PREFERENCE: PreferencesManager | None = None


class PreferenceObject(dict):
    """
    Class used to encapsulate all the data found withing preferences (.pref) files.
    """

    def __init__(self, root, relative_path=None, **kwargs):
        relative_path = relative_path or ''
        path_extension = path.get_extension(relative_path)
        if not path_extension:
            relative_path = os.path.extsep.join((relative_path, 'yaml'))
        kwargs['relative_path'] = relative_path
        kwargs['root'] = root
        super(PreferenceObject, self).__init__(**kwargs)

    def __repr__(self):
        return "<{}> root: {}, path: {}".format(self.__class__.__name__, self.root, self.relative_path)

    def __cmp__(self, other):
        return self.name == other and self.version == other.version

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return super(PreferenceObject, self).__getattribute__(item)

    def __setattr__(self, key, value):
        self[key] = value

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def is_valid(self):
        """
        Returns whether this preference object is valid.

        :return: True if the preference file exists and is valid; False otherwise.
        :rtype: bool
        """

        return False if self.root is None or not path.exists(self.get_path()) else True

    def get_root_path(self):
        """
        Returns the root path stored within preference data.

        :return: root path.
        :rtype: str
        """

        return self.root if self.root else ''

    def get_path(self):
        """
        Returns the path where the preference file is located.

        :return: absolute preference file path.
        :rtype: str
        """

        return path.join_path(self.root, self['relative_path'])

    def save(self, indent=False, sort=False):
        """
        Saves the data into the settings file within disk.

        :param indent:
        :return:
        """

        root = self.root
        if not root:
            return ''

        full_path = self.get_path()
        folder.ensure_folder_exists(path.dirname(full_path))
        output = copy.deepcopy(dict(self))

        del output['root']
        del output['relative_path']
        extension = path.get_extension(full_path)
        if not extension:
            full_path = strings.append_extension(full_path, '.yaml')
        if not indent:
            yamlio.write_to_file(output, full_path, sort_keys=sort)
        else:
            yamlio.write_to_file(output, full_path, indent=2, sort_keys=sort)

        return self.get_path()


class PreferencesManager(object):
    """
    Preferences manager is a class that is responsible for the discovery of preferences folders/files.
    """

    DEFAULT_USER_PREFERENCE_NAME = 'user_preferences'
    _CACHE = dict()

    def __init__(self):
        super(PreferencesManager, self).__init__()

        self._roots = OrderedDict()
        self._extension = consts.PREFERENCE_EXTENSION
        self._plugin_factory = plugin.PluginFactory(interface=core_preference.PreferenceInterface, plugin_id='ID')
        self._resolve_interfaces()
        self._resolve_root_locations()

    # =================================================================================================================
    # CLASS METHODS
    # =================================================================================================================

    @classmethod
    def default_preference_path(cls):
        """
        Returns tpDcc preferences path.

        :return: preferences absolute path. eg. ~/tp/dcc/preferences
        :rtype: str
        """

        return path.clean_path(cls().root('user_preferences'))

    @classmethod
    def prefs_path(cls):
        """
        Returns preferences path.

        :return: preferences absolute path. eg. ~/tp/dcc/preferences/prefs
        :rtype: str
        """

        return path.join_path(cls.default_preference_path(), 'prefs')

    @classmethod
    def asset_path(cls):
        """
        Returns path where tpDcc related assets are located.

        :return: assets absolute path. eg. ~/tp/dcc/preferences/assets
        :rtype: str
        """

        return path.join_path(cls.default_preference_path(), 'assets')

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def root(self, name):
        """
        Returns the path of the root location with given name.

        :param str name: root name.
        :return: resolved root absolute path.
        :rtype: str
        """

        if name not in self._roots:
            raise errors.RootDoesNotExistsError('Root with name "{}" does not exist!'.format(name))
        return self._resolve_root(self._roots[name])

    def root_name_from_path(self, full_path):
        """
        Returns root name based on given path.

        :param str full_path: root path.
        :return: root name.
        :rtype: str
        """

        full_path = os.path.normpath(full_path)
        for name, root in self._roots.items():
            if os.path.normpath(root).startswith(full_path):
                return name

    def add_root(self, full_path, name):
        """
        Adds a new root path into preferences manager.

        :param str full_path: root absolute path.
        :param str name: name of the root.
        :return: True if the root was added successfully; False otherwise.
        :rtype: bool
        """

        # logger.debug('Adding root: {} | {}'.format(name, full_path))
        if name in self._roots:
            raise errors.RootAlreadyExistsError('Root already exists: {}'.format(name))
        root = self._resolve_root(full_path)
        if not path.exists(root):
            raise errors.RootDoesNotExistsError('Root path does not exists: {}'.format(root))
        self._roots[name] = full_path

        return True

    def delete_root(self, name):
        """
        Deletes the root location with given name (all files and folders within it will be removed).

        :param str name: root name to delete.
        :return: True if the root deletion operation was successful; False otherwise.
        :rtype: bool
        """

        root_path = self.root(name)
        try:
            shutil.rmtree(root_path)
        except OSError:
            logger.error('Failed to remove preference root folder: {}'.format(root_path))
            return False

        return True

    def package_preference_root_location(self, package_name):
        """
        Returns the absolute path of the installed package preference root folder.

        :param str package_name: name of the package to retrieve preference root location of.
        :return: package preference root location.
        :rtype: str
        """

        package_manager = api.current_package_manager()
        package = package_manager.resolver.package_by_name(package_name)
        if not package:
            msg = 'Requested package "{}" does not exist within the current environment'.format(package_name)
            logger.error(msg)
            raise ValueError(msg)
        preferences_path = path.join_path(package.root, consts.PREFERENCES_FOLDER)
        if not path.exists(preferences_path):
            msg = 'Default preferences location does not exist at: "{}"'.format(preferences_path)
            logger.error(msg)
            raise ValueError(msg)

        return preferences_path

    def package_preference_location(self, package_name):
        """
        Returns the installed package preference path by the given package name.

        :param str package_name: name of the package we want to return preference path of.
        :return: preference path absolute path.
        :rtype: str
        """

        return path.join_path(self.package_preference_root_location(package_name), 'prefs')

    def default_preference_settings(self, package_name, relative_path):
        """
        Returns the default preferences for the given package.

        :param str package_name: name of the package we want to retrieve default preference settings of.
        :param str relative_path: relative path from preferences folder under the package root.
        :return: PreferenceObject for the preferences file or None.
        :rtype: PreferenceObject
        """

        package_preferences = self.package_preference_location(package_name)
        preference_object = self.preference_object_from_root_path(relative_path, package_preferences)
        if not preference_object.is_valid():
            msg = 'Default preference file for package "{}" is not valid: {}'.format(
                package_preferences, preference_object)
            logger.error(msg)
            raise ValueError(msg)

        return preference_object

    def preference_object_from_root_path(self, relative_path, root_path):
        """
        Returns the PreferenceObject of the given preference root and relative paths.

        :param str relative_path: relative path to the preferences file we want to get PreferenceObject of.
        :param str root_path: root path where the preferences file is located.
        :return: preference object
        :rtype: PreferenceObject
        """

        full_path = path.join_path(root_path, relative_path)

        if not path.exists(full_path):
            return self._open(root_path, relative_path)

        return PreferenceObject('', relative_path)

    def find_setting(
            self, relative_path: str, root: str | None, name: str | None = None, default: Any = None,
            extension: str | None = None):
        """
        Searches the roots for the relative path and returns the PreferencesObject or if name is provided the value of
        key withing the preference data.

        :param str relative_path: relative path to the preference file we are looking for.
        :param str root: the root name to search. If None, all roots will be searched until the relative path is found.
        :param str or None name: optional name of a specific option within the preferences to return value of.
        :param Any default: optional value to return if not setting with name was found.
        :param str or None extension: optional extension of the setting file we are looking for.
        :return: preference data or value found.
        :rtype: PreferenceObject or object
        """

        relative_path = path.clean_path(relative_path)
        relative_path = strings.append_extension(relative_path, extension or self._extension)

        # logger.debug('Finding setting\n\tRelative Path: {}\n\tRoot Path: {}'.format(relative_path, root))

        preference_object = None
        try:
            if root is not None:
                root_path = self._roots.get(root)
                if root_path is not None:
                    resolved_root = self._resolve_root(root_path)
                    full_path = path.clean_path(os.path.normpath(path.join_path(resolved_root, relative_path)))
                    if not path.exists(full_path):
                        return PreferenceObject(root_path, relative_path=relative_path)
                    preference_object = self._open(resolved_root, relative_path)
            else:
                # logger.debug('Root not defined. Finding in registered roots ...')
                # for k, v in reversed(self._roots.items()):
                # 	logger.debug('{}: {}'.format(k, v))
                for _, root_path in reversed(self._roots.items()):
                    resolved_root = self._resolve_root(root_path)
                    full_path = path.clean_path(os.path.normpath(path.join_path(resolved_root, relative_path)))
                    if not path.exists(full_path):
                        continue
                    preference_object = self._open(resolved_root, relative_path)
                    break
        except ValueError:
            logger.error('Failed to load: {} because preferences data is nos valid', exc_info=True)
            raise

        if not preference_object:
            preference_object = PreferenceObject('', relative_path=relative_path)

        if name is not None:
            settings = preference_object.get('settings', dict())
            if name not in settings:
                if default is not None:
                    return default
                raise core_preference.PreferenceSettingNameDoesNotExistError(
                    'Failed to find setting: {} in preference file: {}'.format(name, preference_object))
            return settings[name]

        return preference_object

    def setting_from_root_path(self, relative_path, root_path, extension=None):
        """
        Returns setting from given root path.

        :param str relative_path: relative path to the preference file we are looking for.
        :param str root_path: root path.
        :param str extension: optional extension of the setting file we are looking for.
        :return: preference data or value found.
        :rtype: PreferenceObject or object
        """

        full_path = path.join_path(root_path, strings.append_extension(relative_path, extension or self._extension))
        if path.exists(full_path):
            return self._open(root_path, relative_path)

        return PreferenceObject('', relative_path=relative_path)

    def create_setting(self, relative_path, root, data):
        """
        Creates new setting instance with given data.

        :param str relative_path: relative path to the preference file we are looking for.
        :param str root: the root name to search. If None, all roots will be searched until the relative path is found.
        :param dict data: setting data.
        :return: preference data or value found.
        :rtype: PreferenceObject or object
        """

        setting = self.find_setting(relative_path=relative_path, root=root)
        setting.update(data)

        return setting

    def has_interface(self, interface_id, package_name=None):
        """
        Returns whether an interface with the given name exists.

        :param str interface_id: ID variable on the interface class.
        :param str package_name: optional package name.
        :return: True if exists in the registry; False otherwise.
        :rtype: bool
        """

        return self._plugin_factory.get_plugin_from_id(interface_id, package_name=package_name) is not None

    def interface_class(self, interface_id, package_name=None):
        """
        Returns the interface object.

        :param str interface_id: ID variable on the interface class.
        :param str package_name: optional package name.
        :return: interface class ID.
        :rtype: PreferenceInterface
        """

        return self._plugin_factory.get_plugin_from_id(interface_id, package_name=package_name)

    def interface(self, interface_id, package_name=None, dcc=None):
        """
        Returns the preference interface object with given name.

        :param str interface_id: ID of the preference interface to retrieve.
        :param str package_name: optional package name.
        :param str dcc: specific DCC name whose settings we are looking for.
        :return: Preference or None

        ..note:: an interface is a class used to interact with preferences data structures through code.
        """

        package_name = package_name or 'tp-dcc'

        preference_interface_instance = self._plugin_factory.get_loaded_plugin_from_id(
            interface_id, package_name=package_name)

        if not preference_interface_instance:
            preference_interface_class = self._plugin_factory.get_plugin_from_id(interface_id, package_name=package_name)
            if not preference_interface_class:
                logger.error('Missing interface by name: {}'.format(interface_id))
                return None
            if dcc and dcc not in preference_interface_class.DCCS:
                return None
            return preference_interface_class(self)

        return preference_interface_instance

    def interfaces(self, package_name=None):
        """
        Returns all currently available interface names.

        :param str package_name: optional package name.
        :return: list of interfaces.
        :rtype: list[str]
        """

        return self._plugin_factory.plugins(package_name=package_name).keys()

    def copy_original_to_root(self, root, force=False, update=False, full_merge=False):
        """
        Function that copies all the preference files and folders from each tpDcc Tools package into the default
        preference location.

        :param str root: the root name location which should be part of this instance.
        :param bool force: whether to override already files and folders in the default location.
        :param bool update:
        :param bool full_merge:
        :return: True if the copy operation was completed successfully; False otherwise.
        :rtype: bool
        """

        default_location = self.root(root)
        for preferences_path in self._iterate_package_preference_roots():
            preference_root = path.join_path(preferences_path, 'prefs')
            start_time = timeit.default_timer()
            for root, dirs, files in os.walk(preference_root):
                for file_name in files:
                    preference_file = path.join_path(root, file_name)
                    if not preference_file.endswith(consts.PREFERENCE_EXTENSION):
                        continue
                    relative_path = path.relative_to(preferences_path, preference_file)
                    destination = path.join_path(default_location, relative_path)
                    if force or not path.exists(destination):
                        folder.ensure_folder_exists(path.dirname(destination))
                        logger.debug(
                            'Transferring preference {} to destination: {}'.format(preference_file, destination))
                        shutil.copy2(preference_file, destination)
                    elif update:
                        # TODO: this can be slow when checking lot of pref files, add env var to disable this functionality.
                        orig_dict = yamlio.read_file(preference_file)
                        destination_dict = yamlio.read_file(destination) or dict()
                        if orig_dict:
                            updated_dict = copy.deepcopy(destination_dict)
                            if full_merge:
                                result = helpers.merge_dictionaries(updated_dict, orig_dict, update=True)
                            else:
                                result = helpers.update_dictionaries(orig_dict, updated_dict)[0]
                            if result != destination_dict:
                                logger.info('Updating Preference file: {}'.format(preference_file))
                                yamlio.write_to_file(updated_dict, destination)
            logger.debug('Finished copying package preferences to: {} ({})'.format(root, timeit.default_timer() - start_time))

    def set_root_location(self, root, destination):
        """
        Sets the root location, withoyt moving any of the files.

        :param str root: root name location which should be part of this instance.
        :param str destination: absolute file path to the destination folder.
        """

        orig = self._roots[root]
        del self._roots[root]
        try:
            self.add_root(destination, root)
        except Exception as exc:
            self._roots[root] = orig
            raise exc

    def move_root_location(self, root, destination):
        """
        Physically moves the give root location to the given directory.

        :param str root: root name location which should be part of this instance.
        :param str destination: aboslute file path to the destination folder.
        :return: tuple with the root that was copied and the original root location.
        """

        root_path = self.root(root)
        destination_root = destination
        if os.path.exists(destination_root):
            raise errors.RootDestinationAlreadyExistsError(destination_root)
        shutil.copytree(root_path, destination_root)
        self.set_root_location(root, destination)
        try:
            logger.debug('Removing Root preferences path: {}'.format(root_path))
            shutil.rmtree(root_path)
            logger.debug('Removed Root preferences path: {}'.format(root_path))
        except OSError:
            logger.error('Failed to remove the preference root: {}'.format(root_path))
            raise

    def resolve_package_interfaces(self, package):
        """
        Resolve given package interface.

        :param str package: package to resolve.
        """

        self._resolve_interfaces(package)

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _iterate_package_preference_roots(self, package=None):
        """
        Generator function that returns the preferences root folder located directly under each package root directory
        within packages folder.

        :return: generator function.
        :rtype: generator(str)
        """

        package_manager = api.current_package_manager()
        if not package_manager:
            logger.warning('Package manager not set')
            return

        for pkg in package_manager.resolver.cache.values():
            if package is not None and pkg != package:
                continue
            package_preferences_path = path.join_path(pkg.root, consts.PREFERENCES_FOLDER)
            if not path.is_dir(package_preferences_path):
                continue
            yield package_preferences_path

    def _iterate_package_preferences_path(self, package=None):
        """
        Generator function which iterates over each installed package and returns the sub directory of the preferences.

        :return: generator function.
        :rtype: generator(str)
        """

        for preference_root in self._iterate_package_preference_roots(package):
            pref_path = os.path.join(preference_root, 'prefs')
            if not os.path.exists(pref_path):
                continue
            yield pref_path

    def _resolve_interfaces(self, package=None):
        """
        Internal function that resolves all the preference interfaces found in the tp/dcc/preferences folder within each
        one of the available root package directories.
        """

        for preference_path in self._iterate_package_preference_roots(package=package):
            interface_path = path.join_path(preference_path, consts.INTERFACE_FOLDER)
            if not path.is_dir(interface_path):
                continue
            try:
                self._plugin_factory.register_path(interface_path)
            except Exception:
                logger.error('Was not possible to resolve interface: "{}"'.format(interface_path), exc_info=True)

    def _resolve_root_locations(self):
        """
        Internal function that resolves all interface classes.
        """

        core_interface = self.interface('core')
        roots_path = core_interface.root_config_path() if core_interface else ''
        if not path.is_file(roots_path):
            logger.error('Missing Preferences configuration file: {}'.format(roots_path))
            return
        roots = yamlio.read_file(roots_path)
        for root_name, root_path in roots.items():
            if root_name == self.DEFAULT_USER_PREFERENCE_NAME:
                folder.ensure_folder_exists(self._resolve_root(root_path))
            self.add_root(root_path, root_name)

    def _resolve_root(self, root_path):
        """
        Internal function that resolves the given root path.

        :param str root_path: root path to resolve.
        :return: resolved root path.
        :rtype: str
        """

        return path.clean_path(os.path.expandvars(os.path.expanduser(root_path)))

    def _open(self, root, relative_path, extension=None):
        """
        Internal function that reads the contents of the preferences file.

        :param str root: root path where the preferences file is located.
        :param str relative_path: relative path of the preferences file.
        :param str or None extension: optional extension for the setting to open.
        :return: preference data stored within a PreferenceObject
        :rtype: PreferenceObject
        """

        relative_path = path.clean_path(relative_path)
        relative_path = strings.append_extension(relative_path, extension or self._extension)
        full_path = path.join_path(root, relative_path)
        if not path.exists(full_path):
            raise core_preference.InvalidPreferencePathError(full_path)
        if full_path in self._CACHE:
            return self._CACHE[full_path]
        data = yamlio.read_file(full_path, maintain_order=True) or dict()
        preference_object = PreferenceObject(root, relative_path=relative_path, **data)
        self._CACHE[full_path] = preference_object

        return preference_object


def preference() -> PreferencesManager:
    """
    Returns global preferences manager
    """

    global _PREFERENCE
    if _PREFERENCE is None or not api.current_package_manager():
        _PREFERENCE = PreferencesManager()

    return _PREFERENCE
