from __future__ import annotations

import os
import re
import sys
import timeit
import inspect
import logging
import pathlib
import operator
import platform
from typing import Type, Any
from types import ModuleType
from distutils import version
try:
    from inspect import getfullargspec
except ImportError:
    # noinspection PyProtectedMember,SpellCheckingInspection
    from inspect import getargspec as getfullargspec

from .. import dcc
from . import helpers, folder, modules


class Plugin:

    ID: str = ''
    DCC_NAMES: list[str] = []

    def __init__(self, factory: PluginFactory | None = None):
        """
        Base plugin class.

        This class serves as the base class for all plugins. It defines two class attributes:
        - ID: A string representing the unique identifier for the plugin.
        - DCC_NAMES: A list of strings representing the names of supported Digital Content Creation (DCC) software.

        The constructor initializes the plugin instance with an optional reference to a PluginFactory
        instance. It also initializes an instance of PluginStats associated with the plugin.

        :param factory: An optional reference to a PluginFactory instance. Default is None.
        """

        self._factory = factory
        self._stats = PluginStats(self)

    @property
    def stats(self) -> PluginStats:
        """
        Getter method that returns stats associated with this plugin.

        :return: plugin stats.
        """

        return self._stats


class PluginStats:
    def __init__(self, plugin: Any, id_attr: str = 'ID'):
        """
        Plugin statistics class.

        This class represents the statistics for a plugin's execution. It initializes with the plugin instance
        and an optional attribute name used to retrieve the plugin ID. It tracks the start time, end time, and
        execution time of the plugin.

        :param plugin: The plugin instance associated with the statistics.
        :param id_attr: The attribute name used to retrieve the plugin ID. Default is 'ID'.
        """

        self._plugin = plugin
        self._id = getattr(self._plugin, id_attr)
        self._start_time = 0.0
        self._end_time = 0.0
        self._execution_time = 0.0

        self._info: dict[str, Any] = {}
        self._init()

    @property
    def info(self) -> dict[str, Any]:
        """
        Getter method that returns dictionary with plugin statistics.

        :return: plugin statistics.
        """

        return self._info

    def start(self):
        """
        Sets the start time for metrics.
        """

        self._start_time = timeit.default_timer()

    def finish(self, traceback: str | None = None):
        """
        Called when the plugin has finish executing.

        :param traceback:
        :return:
        """

        self._end_time = timeit.default_timer()
        self._execution_time = self._end_time - self._start_time
        self._info['executionTime'] = self._execution_time
        self._info['lastUsed'] = self._end_time
        if traceback:
            self._info['traceback'] = traceback

    def _init(self):
        """
        Internal function that initializes some basic info about the plugin and the use environment
        """

        try:
            file_path = inspect.getfile(self._plugin.__class__)
        except TypeError:
            file_path = '__main__'
        self._info.update({
            'name': self._plugin.__class__.__name__,
            'module': self._plugin.__class__.__module__,
            'filepath': file_path,
            'id': self._id,
            'application': dcc.current_dcc()})
        machine_dict = {
            'pythonVersion': sys.version,
            'node': platform.node(),
            'OSRelease': platform.release(),
            'OSVersion': platform.platform(),
            'processor': platform.processor(),
            'machineType': platform.machine(),
            'env': os.environ,
            'syspath': sys.path,
            'executable': sys.executable,
        }
        self._info.update(machine_dict)


class PluginFactory:
    """
    Factory class responsible for loading and managing plugins.

    Attributes
    ----------
    REGEX_FOLDER_VALIDATOR : re.Pattern
        Regex validator for plugin folder directories.
    REGEX_FILE_VALIDATOR : re.Pattern
        Regex validator for plugin file names.
    """

    class PluginLoadingMechanism:
        """
        Defines the different mechanisms for loading plugins from a registered path.

        Attributes
        ----------
        GUESS : int
            Default mechanism. Attempts to use the IMPORTABLE method first, and if the module
            is not accessible from within sys modules, it will fall back to LOAD_SOURCE.
        LOAD_SOURCE : int
            Mechanism for loading plugin code outside the interpreter sys path. The plugin file
            is loaded instead of imported, allowing flexibility in structure but disallowing
            relative imports within the plugins.
        IMPORTABLE : int
            Mechanism for loading plugin code that resides within already importable locations.
            Necessary for plugins with relative imports, ensuring that class names resolve correctly.
        """

        # Default mechanism. It will attempt to use the IMPORTABLE method first, and if the module is not
        # accessible from within sys modules it will fall back to LOAD_SOURCE.
        GUESS = 0

        # Mechanism to use when your plugin code is outside the interpreter sys path. The plugin file
        # be loaded instead of imported. Gives flexibility in terms of structure, but you cannot use
        # relative import paths within the plugins loaded with this mechanism. All loaded plugins using
        # this module are imported into a namespace defined through an uuid.
        LOAD_SOURCE = 1

        # Mechanism to use when your plugin code resides within already importable locations. Mandatory
        # to use when your plugin contains relative imports. Because this is importing modules which
        # are available on the sys.path, the class names will resolve nicely too
        IMPORTABLE = 2

    # Regex validator for plugin folder directories
    REGEX_FOLDER_VALIDATOR = re.compile('^((?!__pycache__).)*$')

    # Regex validator for plugin file names
    REGEX_FILE_VALIDATOR = re.compile(r'([a-zA-Z].*)(\.py$|\.pyc$)')

    def __init__(
            self, interface: Type[Plugin] = Plugin, paths: list[str] | None = None, package_name: str | None = None,
            plugin_id: str | None = None, version_id: str | None = None, env_var: str | None = None,
            name=None):
        """
        Initializes the PluginFactory with the specified parameters.

        :param interface: The base interface that plugins should implement. Defaults to Plugin.
        :param paths: A list of paths to search for plugins. Defaults to None.
        :param package_name: The package name to use when loading plugins. Defaults to None.
        :param plugin_id: A unique identifier for the plugin. Defaults to None.
        :param version_id: The version identifier for the plugin. Defaults to None.
        :param env_var: The environment variable to use for configuring the plugin paths. Defaults to None.
        :param name: An optional name for the PluginFactory instance. Defaults to None.
        """

        self._interfaces = helpers.force_list(interface)
        self._plugin_identifier = plugin_id or '__name__'
        self._version_identifier = version_id
        module_path = self.__class__.__module__
        if name:
            self._name = '.'.join([module_path, f'{name}PluginFactory'])
        else:
            self._name = '.'.join([module_path, self.__class__.__name__])
        self._logger = logging.getLogger(self._name)
        self._logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        # noinspection SpellCheckingInspection
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

        self._plugins: dict[str, list[Any]] = {}
        self._registered_paths: dict[str, dict[str, int]] = {}
        self._loaded_plugins: dict[str, list[Type]] = {}

        self.register_paths(paths, package_name=package_name)
        if env_var:
            self.register_paths_from_env_var(env_var, package_name=package_name)

    def __repr__(self) -> str:
        """
        Return a string representation of the object.

        This method returns a string representing the object in a human-readable format. It includes the class name,
        plugin identifier, and the count of plugins associated with the factory.

        :returns: A string representation of the object.
        """

        return '[{} - Identifier: {}, Plugin Count: {}]'.format(
            self.__class__.__name__, self._plugin_identifier, len(self._plugins))

    @classmethod
    def get_regex_folder_validator(cls) -> re.Pattern:
        """
        Returns regex validator for plugin folder directories.

        :return: regex folders pattern.
        """

        dcc_name = dcc.current_dcc()
        all_dccs = dcc.ALL
        dcc_exclude = ''
        for _dcc in all_dccs:
            if _dcc == dcc_name:
                continue
            dcc_exclude += '(?!{})'.format(_dcc)

        return re.compile('^((?!__pycache__)' + dcc_exclude + '(?!plugins)(?!vendors)(?!art)(?!src).)*$')

    @classmethod
    def get_regex_file_validator(cls):
        """
        Returns regex validator for plugin files

        :return: regex files pattern.
        """

        return re.compile(r'([a-zA-Z_].*)(\.py$)')

    @property
    def loaded_plugins(self) -> dict[str, list[Any]]:
        """
        Getter method that returns all loaded plugins.

        :return: loaded plugins for each one of the packages.
        """

        return self._loaded_plugins

    def register_path(
            self, path_to_register: str, package_name: str | None = None,
            mechanism: int = PluginLoadingMechanism.GUESS) -> tuple[int, list[Type]]:
        """
        Registers a search path within the factory. The factory will immediately being searching recursively withing
        this location for any plugin.

        :param path_to_register: absolute path to register into the factory
        :param package_name: package name current registered plugins will belong to. Default to tDcc.
        :param mechanism: plugin load mechanism to use
        :return: total amount of registered plugins
        """

        plugins_found: list[Type] = []

        if not path_to_register or not os.path.exists(path_to_register):
            return 0, []

        package_name = package_name or 'tp-dcc'

        # Regardless of what is found in the given path, we store it
        self._registered_paths.setdefault(package_name, {}).setdefault(path_to_register, 0)
        self._registered_paths[package_name][path_to_register] = mechanism

        current_plugins_count = len(self._plugins)

        file_paths = list()
        if os.path.isdir(path_to_register):
            for root, _, files in folder.walk_level(path_to_register):
                if not self.get_regex_folder_validator().match(root):
                    continue
                for file_name in files:
                    # Skip files that do not match PluginFactory regex validator.
                    if not self.get_regex_file_validator().match(file_name):
                        continue
                    if file_name.startswith('test') or file_name in ['setup.py']:
                        continue
                    file_paths.append(pathlib.Path(root, file_name).as_posix())
        elif os.path.isfile(path_to_register):
            file_paths.append(path_to_register)

        # Loop through all the found files searching for plugins definitions
        for file_path in file_paths:
            module_to_inspect = None
            if mechanism in (self.PluginLoadingMechanism.IMPORTABLE, self.PluginLoadingMechanism.GUESS):
                module_to_inspect = self._mechanism_import(file_path)
                # if module_to_inspect:
                #     logger.debug('Module Import : {}'.format(file_path))
            if not module_to_inspect:
                if mechanism in (self.PluginLoadingMechanism.LOAD_SOURCE, self.PluginLoadingMechanism.GUESS):
                    module_to_inspect = self._mechanism_load(file_path)
                    # if module_to_inspect:
                    #     logger.debug('Direct Load : {}'.format(file_path))
            if not module_to_inspect:
                continue

            # noinspection PyBroadException
            try:
                for interface in self._interfaces:
                    for item_name in dir(module_to_inspect):
                        item = getattr(module_to_inspect, item_name)
                        if inspect.isclass(item):
                            if item == interface:
                                continue
                            if issubclass(item, interface):
                                item.ROOT = path_to_register
                                item.PATH = file_path
                                item.MODULE = module_to_inspect
                                self._plugins.setdefault(package_name, list())
                                self._plugins[package_name].append(item)
                                plugins_found.append(item)
            except Exception:
                self._logger.debug('', exc_info=True)

        return len(self._plugins) - current_plugins_count, plugins_found

    def register_paths(
            self, paths_to_register: list[str], package_name: str | None = None,
            mechanism: int = PluginLoadingMechanism.GUESS) -> list[Type]:
        """
        Registers given paths within the factory. The factory will immediately being searching recursively withing
        this location for any plugin.

        :param paths_to_register: absolute paths to register into the factory.
        :param package_name: package name current registered plugins will belong to.
        :param mechanism: plugin load mechanism to use.
        :return: found plugins.
        """

        paths_to_register = helpers.force_list(paths_to_register)

        total_plugins = 0
        visited: set[str] = set()
        plugins_found: list[Type] = []
        for path_to_register in paths_to_register:
            if not path_to_register:
                continue
            base_name = pathlib.Path(
                os.path.splitext(
                    path_to_register)[0] if os.path.isfile(path_to_register) else path_to_register).as_posix()
            if base_name in visited:
                continue
            visited.add(base_name)
            plugins_count, found = self.register_path(path_to_register, mechanism=mechanism, package_name=package_name)
            total_plugins += plugins_count
            plugins_found.extend(found)

        plugins_found = helpers.remove_dupes(plugins_found)

        return plugins_found

    def register_paths_from_env_var(
            self, env_var: str, package_name: str | None = None,
            mechanism: int = PluginLoadingMechanism.GUESS) -> list[Type]:
        """
        Registers plugin paths from an environment variable.

        This method reads the specified environment variable to obtain plugin paths and registers them.
        Optionally, a package name can be provided, and a loading mechanism can be specified.

        :param env_var: The name of the environment variable that contains the plugin paths.
        :param package_name: The package name to use when loading plugins. Defaults to None.
        :param mechanism: The mechanism to use for loading plugins. Defaults to PluginLoadingMechanism.GUESS.
        :return: A list of registered plugin types.
        """

        paths = os.environ.get(env_var, '').split(os.pathsep)
        if not paths:
            return []

        return self.register_paths(paths, package_name=package_name, mechanism=mechanism)

    def register_plugin_from_class(self, plugin_class: Type[Plugin], package_name: str | None = None) -> bool:
        """
        Registers a single plugin from the given class.

        This method registers a plugin by directly providing the plugin class.
        Optionally, a package name can be specified for the plugin.

        :param plugin_class: The plugin class to register.
        :param package_name: The package name to associate with the plugin. Defaults to None.
        :return: True if the plugin was successfully registered, False otherwise.
        """

        for interface in self._interfaces:
            if not inspect.isclass(plugin_class) or not issubclass(plugin_class, interface):
                return False

        if not package_name:
            class_id = self._get_identifier(plugin_class)
            split_id = class_id.replace('.', '-').split('-')[0]
            package_name = split_id if split_id != class_id else 'tp-dcc'

        self._plugins.setdefault(package_name, list()).append(plugin_class)

        return True

    def register_by_package(self, package_path: str):
        """
        Registers all plugins from the specified package path.

        This function traverses the specified package path and registers all the plugins found within it.

        :param package_path: The filesystem path of the package to register plugins from.
        ..note:: this is a costly operation because it requires a recursive search by importing all submodules and
            searching them.
        """

        for sub_module in modules.iterate_modules(package_path):
            file_name = os.path.splitext(os.path.basename(sub_module))[0]
            if file_name.startswith('__') or sub_module.endswith('.pyc'):
                continue
            module_path = os.path.normpath(sub_module)
            module_dotted_path = modules.convert_to_dotted_path(module_path)
            if not module_dotted_path:
                self._logger.warning(
                    'Skipping module due to invalid path: {} -> {}'.format(sub_module, module_dotted_path))
                continue
            sub_module_obj = None
            try:
                sub_module_obj = modules.import_module(module_dotted_path, skip_errors=True)
            except ValueError:
                self._logger.error('Failed to load plugin module: {}'.format(sub_module))
            except ImportError:
                self._logger.error('Failed to import plugin module: {}'.format(sub_module), exc_info=True)
                continue
            if not sub_module_obj:
                self._logger.debug('Failed to load/import plugin module: {}'.format(sub_module))
                continue
            for member in modules.iterate_module_members(sub_module_obj, predicate=inspect.isclass):
                self.register_plugin_from_class(member[1])

    def paths(self, package_name: str | None = None) -> list[str]:
        """
        Returns a list of paths associated with the specified package name.

        This function retrieves all the paths that are associated with the given package name. If no package name is
        provided, it returns the paths for the default package.

        :param package_name: The name of the package to retrieve paths for. Defaults to None.
        :return: A list of paths associated with the specified package name.
        """

        package_name = package_name or 'tp-dcc'
        return list(self._registered_paths.get(package_name, {}).keys())

    def identifiers(self, package_name: str | None = None) -> list[str]:
        """
        Returns a list of identifiers associated with the specified package name.

        This function retrieves all the identifiers (names of plugins) that are associated with the given package name.
        If no package name is provided, it returns the identifiers for the default package.

        :param package_name: The name of the package to retrieve identifiers for. Defaults to None.
        :return: A list of identifiers associated with the specified package name.
        """

        package_name = package_name or 'tp-dcc'
        return [self._get_identifier(plugin) for plugin in self._plugins.get(package_name, [])]

    def versions(self, identifier: str, package_name: str | None = None) -> list[str]:
        """
        Returns a list of versions associated with the specified identifier and package name.

        This function retrieves all the versions of a plugin that are associated with the given identifier.
        If a package name is provided, it retrieves the versions for that specific package.

        :param identifier: The identifier of the plugin to retrieve versions for.
        :param package_name: The name of the package to retrieve versions from. Defaults to None.
        :return: A list of versions associated with the specified identifier and package name.
        """

        package_name = package_name or 'tp-dcc'

        if not self._version_identifier:
            return []

        return sorted(
            self._get_version(plugin) for plugin in self._plugins.get(
                package_name, []) if self._get_identifier(plugin) == identifier
        )

    def plugins(self, package_name: str | None = None) -> list[Type]:
        """
        Returns a list of plugin types associated with the specified package name.

        This function retrieves all the plugin types that are associated with the given package name.
        If no package name is provided, it returns the plugin types for the default package.

        :param package_name: The name of the package to retrieve plugins for. Defaults to None.
        :return: A list of plugin types associated with the specified package name.
        """

        package_name = package_name or 'tp-dcc'

        ordered_plugins: list[Type] = []
        plugins = [self.plugin_from_id(
            identifier, package_name=package_name) for identifier in self.identifiers(package_name=package_name)]
        plugins_to_order = [plugin for plugin in plugins if hasattr(plugin, 'ORDER')]
        plugins_ordered = sorted(plugins_to_order, key=operator.attrgetter("ORDER"))
        ordered_plugins.extend(plugins_ordered)
        for plugin in plugins:
            if plugin in ordered_plugins:
                continue
            ordered_plugins.append(plugin)

        return ordered_plugins

    def plugin_from_id(
            self, plugin_id: str, package_name: str | None = None,
            plugin_version: str | None = None) -> type[Any] | None:
        """
        Retrieves a plugin type based on its identifier, package name, and version.

        This function searches for a plugin by its identifier, optionally within a specified package and version.
        If no package name or version is provided, it searches within the default package and the latest version.

        :param plugin_id: The identifier of the plugin to retrieve.
        :param package_name: The name of the package to search for the plugin. Defaults to None.
        :param plugin_version: The version of the plugin to retrieve. Defaults to None.
        :return: The plugin type if found, otherwise None.
        """

        package_name = package_name or 'tp-dcc'

        if package_name and package_name not in self._plugins:
            self._logger.error('Impossible to retrieve plugin from id: {} package: "{}" not registered!'.format(
                plugin_id, package_name))
            return None

        if package_name:
            matching_plugins = [plugin for plugin in self._plugins.get(
                package_name, []) if self._get_identifier(plugin) == plugin_id]
        else:
            matching_plugins = []
            for plugins in list(self._plugins.values()):
                for plugin in plugins:
                    if self._get_identifier(plugin) == plugin_id:
                        matching_plugins.append(plugin)

        if not matching_plugins:
            # self._logger.warning('No plugin with id "{}" found in package "{}"'.format(plugin_id, package_name))
            return None

        if not self._version_identifier:
            return matching_plugins[0]

        if dcc:
            _matching_plugins = []
            for plugin_cls in matching_plugins:
                if hasattr(plugin_cls, 'DCCS') and dcc not in plugin_cls.DCC_NAMES:
                    continue
                _matching_plugins.append(plugin_cls)
            matching_plugins = _matching_plugins
        if not matching_plugins:
            self._logger.warning(
                'No plugin with id "{}" found in package "{}" for DCC: {}'.format(plugin_id, package_name, dcc))
            return None

        versions = {
            self._get_version(plugin): plugin for plugin in matching_plugins
        }
        ordered_versions = [version.LooseVersion(str(v)) for v in list(versions.keys())]

        # If not version given, we return the plugin with the highest value
        if not plugin_version:
            return versions[str(ordered_versions[0])]

        plugin_version = version.LooseVersion(str(plugin_version))
        if plugin_version not in ordered_versions:
            self._logger.warning('No Plugin with id "{}" and version "{}" found in package "{}"'.format(
                plugin_id, plugin_version, package_name))
            return None

        return versions[str(plugin_version)]

    def get_loaded_plugin_from_id(
            self, plugin_id: str, package_name: str | None = None, plugin_version: str | None = None,
            dcc_name: str | None = None) -> Plugin | None:
        """
        Retrieves a loaded plugin instance based on its identifier, package name, version, and DCC
        (Digital Content Creation) name.

        This function searches for a loaded plugin by its identifier, optionally within a specified package, version,
        and DCC name.
        If no package name, version, or DCC name is provided, it searches within the default package, the latest
        version, and the default DCC.

        :param plugin_id: The identifier of the plugin to retrieve.
        :param package_name: The name of the package to search for the plugin. Defaults to None.
        :param plugin_version: The version of the plugin to retrieve. Defaults to None.
        :param dcc_name: The name of the Digital Content Creation software to retrieve the plugin for. Defaults to None.
        :return: The loaded plugin instance if found, otherwise None.
        """

        package_name = package_name or 'tp-dcc'

        if package_name and package_name not in self._loaded_plugins:
            self._logger.debug(
                f'Impossible to retrieve loaded plugin from id: {plugin_id} package: "{package_name}" not registered!')
            return None

        if package_name:
            matching_plugins = [plugin for plugin in self._loaded_plugins.get(
                package_name, []) if self._get_identifier(plugin) == plugin_id]
        else:
            matching_plugins = []
            for plugins in list(self._loaded_plugins.values()):
                for plugin in plugins:
                    if self._get_identifier(plugin) == plugin_id:
                        matching_plugins.append(plugin)

        if not matching_plugins:
            self._logger.warning('No loaded plugin with id "{}" found in package "{}"'.format(plugin_id, package_name))
            return None

        if dcc_name:
            matching_plugins = [plugin_cls for plugin_cls in matching_plugins if dcc_name in plugin_cls.DCC_NAMES]
        if not matching_plugins:
            self._logger.warning(
                f'No loaded plugin with id "{plugin_id}" found in package "{package_name}" for DCC: {dcc_name}')
            return None

        if not self._version_identifier:
            return matching_plugins[0]

        versions = {self._get_version(plugin): plugin for plugin in matching_plugins}
        ordered_versions = [version.LooseVersion(str(v)) for v in list(versions.keys())]

        # If not version given, we return the plugin with the highest value
        if not plugin_version:
            return versions[str(ordered_versions[0])]

        plugin_version = version.LooseVersion(plugin_version)
        if plugin_version not in ordered_versions:
            self._logger.warning('No Plugin with id "{}" and version "{}" found in package "{}"'.format(
                plugin_id, plugin_version, package_name))
            return None

        return versions[str(plugin_version)]

    def load_plugin(self, plugin_id: str, package_name: str | None = None, **kwargs) -> Plugin | None:
        """
        Loads a plugin based on its identifier and package name, with additional optional keyword arguments.

        This function loads a plugin by its identifier, optionally within a specified package, and allows for
        additional configuration through keyword arguments.

        :param plugin_id: The identifier of the plugin to load.
        :param package_name: The name of the package to load the plugin from. Defaults to None.
        :param kwargs: Additional keyword arguments for plugin configuration.
        :return: The loaded plugin instance.
        """

        package_name = package_name or 'tp-dcc'

        plugin_class = self.plugin_from_id(plugin_id, package_name=package_name)
        if not plugin_class:
            return None

        self._logger.debug('Loading plugin: {}'.format(plugin_id))
        spec = getfullargspec(plugin_class.__init__)
        try:
            keywords = spec.kwonlyargs
        except AttributeError:
            keywords = spec.keywords
        args = spec.args
        if (args and 'factory' in args) or (keywords and 'factory' in keywords):
            kwargs['factory'] = self
        # noinspection PyBroadException
        try:
            plugin_instance = plugin_class(**kwargs)
        except Exception:
            self._logger.error("Failed to load plugin: {}".format(plugin_id), exc_info=True)
            return None

        self._loaded_plugins.setdefault(package_name, list())
        plugin_instance.is_loaded = True
        self._loaded_plugins[package_name].append(plugin_instance)

        return plugin_instance

    def load_all_plugins(self, package_name: str | None = None, **kwargs):
        """
        Loads all plugins from the specified package name, with additional optional keyword arguments.

        This function loads all plugins within a specified package and allows for additional configuration
        through keyword arguments.

        :param package_name: The name of the package to load plugins from. Defaults to None.
        :param kwargs: Additional keyword arguments for plugin configuration.
        """

        package_name = package_name or 'tp-dcc'

        for pkg_name, plugin_classes in self._plugins.items():
            if package_name and pkg_name != package_name:
                continue
            for plugin_class in plugin_classes:
                plugin_id = self._get_identifier(plugin_class)
                self.load_plugin(plugin_id, package_name=package_name, **kwargs)

    def unload_all_plugins(self, package_name: str | None = None):
        """
        Unloads all plugins from the specified package name.

        This function unloads all plugins within a specified package. If no package name is provided,
        it unloads all plugins from the default package.

        :param package_name: The name of the package to unload plugins from. Defaults to None.
        """

        package_name = package_name or 'tp-dcc'
        if package_name not in self._loaded_plugins:
            return
        self._loaded_plugins[package_name].clear()

    def unregister_path(self, path: str, package_name: str | None = None):
        """
        Unregisters a path from the specified package name.

        This function removes a previously registered path from a specified package. If no package name is provided,
        it removes the path from the default package.

        :param path: The path to unregister.
        :param package_name: The name of the package to unregister the path from. Defaults to None.
        """

        registered_paths = self._registered_paths.copy()

        self._plugins = list()
        self._registered_paths = dict()

        for pkg_name, registered_paths_dict in registered_paths.items():
            for original_path, mechanism in registered_paths_dict.items():
                if package_name == pkg_name and pathlib.Path(original_path) == pathlib.Path(path):
                    continue
                self.register_path(original_path, package_name=pkg_name, mechanism=mechanism)

    def reload(self):
        """
        Clears all registered plugins and performs a search over all registered paths.
        """

        registered_paths = self._registered_paths.copy()

        self.clear()

        for package_name, registered_paths_dict in registered_paths.items():
            for original_path, mechanism in registered_paths_dict.items():
                self.register_path(original_path, package_name=package_name, mechanism=mechanism)

    def clear(self):
        """
        Clears all the plugins and registered paths.
        """

        self._plugins.clear()
        self._registered_paths.clear()
        self._loaded_plugins.clear()

    @staticmethod
    def _mechanism_import(file_path: str):
        """
        Imports a module using a specific mechanism based on the provided file path.

        This internal function handles the import of a module from the given file path using a specific
        mechanism defined within the class.

        :param file_path: The filesystem path of the module to import.
        """

        module_name = modules.convert_to_dotted_path(file_path)
        if module_name:
            try:
                return sys.modules[module_name]
            except KeyError:
                return modules.import_module(module_name, skip_errors=True)

        return None

    @staticmethod
    def _mechanism_load(file_path: str) -> ModuleType | None:
        """
        Loads a module from the specified file path using a specific loading mechanism.

        This internal function handles the loading of a module from the given file path using a specific
        mechanism defined within the class.

        :param file_path: The filesystem path of the module to load.
        :return: The loaded module, or None if the module could not be loaded.
        """

        return modules.load_module_from_source(file_path)

    def _get_identifier(self, plugin: Type) -> str:
        """
        Retrieves the identifier for the given plugin type.

        This internal function extracts and returns the unique identifier associated with the specified plugin type.

        :param plugin: The plugin type to retrieve the identifier for.
        :return: The identifier of the plugin.
        """

        identifier = getattr(plugin, self._plugin_identifier)

        predicate = inspect.isfunction
        if predicate(identifier):
            return identifier()

        return identifier

    def _get_version(self, plugin: Type) -> str:
        """
        Retrieves the version for the given plugin type.

        This internal function extracts and returns the version associated with the specified plugin type.

        :param plugin: The plugin type to retrieve the version for.
        :return: The version of the plugin.
        """

        identifier = getattr(plugin, self._version_identifier)

        predicate = inspect.isfunction
        if predicate(identifier):
            return str(identifier())

        return str(identifier)
