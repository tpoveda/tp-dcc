from __future__ import annotations

import os
import re
import sys
import timeit
import inspect
import logging
import pathlib
import operator
from types import ModuleType
from typing import Type, Any
from distutils import version
from inspect import getfullargspec

from .. import dcc
from ..python import helpers, modules, osplatform, folder as folder_utils


class Plugin:
    """
    Base plugin class.
    """

    ID: str = ""
    DCCS: list[str] = []

    def __init__(self, factory=None):
        self._factory = factory
        self._stats = PluginStats(self)

    @property
    def stats(self) -> PluginStats:
        """
        Getter method that returns the stats object for this plugin.

        :return: plugin stats.
        """

        return self._stats


class PluginStats:
    """
    Class that handles the statistics of a plugin.
    """

    def __init__(self, plugin, id_attr="ID"):
        self._plugin = plugin
        self._id = getattr(self._plugin, id_attr)
        self._start_time = 0.0
        self._end_time = 0.0
        self._execution_time = 0.0

        self._info = {}
        self._init()

    @property
    def info(self):
        return self._info

    def start(self):
        """
        Sets the start time for metrics.
        """

        self._start_time = timeit.default_timer()

    def finish(self, traceback=None):
        """
        Called when the plugin has finish executing.
        """

        self._end_time = timeit.default_timer()
        self._execution_time = self._end_time - self._start_time
        self._info["executionTime"] = self._execution_time
        self._info["lastUsed"] = self._end_time
        if traceback:
            self._info["traceback"] = traceback

    def _init(self):
        """
        Internal function that initializes some basic info about the plugin and the use environment
        """

        try:
            file_path = inspect.getfile(self._plugin.__class__)
        except TypeError:
            file_path = "__main__"
        self._info.update(
            {
                "name": self._plugin.__class__.__name__,
                "module": self._plugin.__class__.__module__,
                "filepath": file_path,
                "id": self._id,
                "application": dcc.current_dcc(),
            }
        )
        self._info.update(osplatform.machine_info())


class PluginFactory:
    class PluginLoadingMechanism:
        """
        Class that contains variables used to define how the plugins on a registered path should be loaded.
        """

        # Default mechanism. It will attempt to use the IMPORTABLE method first, and if the module is not
        # accessible from within sys modules it will fall back to LOAD_SOURCE.
        GUESS = 0

        # Mechanism to use when your plugin code is outside the interpreter sys path. The plugin file
        # be loaded instead of imported. Gives flexibility in terms of structure you cannot use
        # relative import paths within the plugins loaded with this mechanism. All loaded plugins using
        # this module are imported into a namespace defined through an uuid.
        LOAD_SOURCE = 1

        # Mechanism to use when your plugin code resides within already importable locations. Mandatory
        # to use when your plugin contains relative imports. Because this is importing modules which
        # are available on the sys.path, the class names will resolve nicely too
        IMPORTABLE = 2

    # Regex validator for plugin folder directories
    REGEX_FOLDER_VALIDATOR = re.compile("^((?!__pycache__).)*$")

    # Regex validator for plugin file names
    REGEX_FILE_VALIDATOR = re.compile(r"([a-zA-Z].*)(\.py$|\.pyc$)")

    def __init__(
        self,
        interface: Type = Plugin,
        paths: list[str] = None,
        package_name: str | None = None,
        plugin_id: str | None = None,
        version_id: str | None = None,
        env_var: str | None = None,
        name: str | None = None,
    ):
        """

        :param interface: Abstract class to use when searching for plugins within the registered paths.
        :param paths: list of absolute paths to search for plugins.
        :param plugin_id: str, plugin identifier to distinguish between different plugins. If not given, plugin
            class name will be used
        :param version_id: plugin version identifier. If given, allows plugins with the same identifier to be
            differentiated.
        :param env_var: optional environment variable name containing paths to register separated by OS separator.
        """

        self._interfaces = helpers.force_list(interface)
        self._plugin_identifier = plugin_id or "__name__"
        self._version_identifier = version_id
        module_path = self.__class__.__module__
        if name:
            self._name = ".".join([module_path, f"{name}PluginFactory"])
        else:
            self._name = ".".join([module_path, self.__class__.__name__])
        self._logger = logging.getLogger(self._name)

        self._plugins = {}
        self._registered_paths = {}
        self._loaded_plugins = {}

        self.register_paths(paths, package_name=package_name)
        if env_var:
            self.register_paths_from_env_var(env_var, package_name=package_name)

    def __repr__(self) -> str:
        """
        Returns a string representation of the plugin factory.

        :return: string representation.
        """

        return (
            f"[{self.__class__.__name__} - Identifier: "
            f"{self._plugin_identifier}, Plugin Count: {len(self._plugins)}]"
        )

    @classmethod
    def get_regex_folder_validator(cls) -> re.Pattern:
        """
        Returns regex validator for plugin folder directories.
        """

        dcc_name = dcc.current_dcc()
        all_dccs = dcc.ALL
        dcc_exclude = ""
        for _dcc in all_dccs:
            if _dcc == dcc_name:
                continue
            dcc_exclude += "(?!{})".format(_dcc)

        return re.compile(
            "^((?!__pycache__)"
            + dcc_exclude
            + "(?!plugins)(?!vendors)(?!art)(?!src).)*$"
        )

    @classmethod
    def get_regex_file_validator(cls):
        """
        Returns regex validator for plugin files
        """

        return re.compile(r"([a-zA-Z_].*)(\.py$)")

    @property
    def loaded_plugins(self):
        return self._loaded_plugins

    def register_path(
        self,
        path_to_register: str,
        package_name: str | None = None,
        mechanism: int = PluginLoadingMechanism.GUESS,
    ) -> tuple[int, list]:
        """
        Registers a search path within the factory. The factory will immediately being searching recursively withing
        this location for any plugin.

        :param path_to_register: absolute path to register into the factory
        :param package_name: package name current registered plugins will belong to. Default to tDcc.
        :param mechanism: plugin load mechanism to use
        :return: total amount of registered plugins
        """

        plugins_found = []

        if not path_to_register or not os.path.exists(path_to_register):
            return 0, []

        package_name = package_name or "tp-dcc"

        # Regardless of what is found in the given path, we store it
        self._registered_paths.setdefault(package_name, dict()).setdefault(
            path_to_register, dict()
        )
        self._registered_paths[package_name][path_to_register] = mechanism

        current_plugins_count = len(self._plugins)

        file_paths = list()
        if os.path.isdir(path_to_register):
            for root, _, files in folder_utils.walk_level(path_to_register):
                if not self.get_regex_folder_validator().match(root):
                    continue

                for file_name in files:
                    # Skip files that do not match PluginFactory regex validator.
                    if not self.get_regex_file_validator().match(file_name):
                        continue
                    if file_name.startswith("test") or file_name in ["setup.py"]:
                        continue

                    file_paths.append(pathlib.Path(root, file_name).as_posix())
        elif os.path.isfile(path_to_register):
            file_paths.append(path_to_register)

        # Loop through all the found files searching for plugins definitions
        for file_path in file_paths:
            module_to_inspect = None

            if mechanism in (
                self.PluginLoadingMechanism.IMPORTABLE,
                self.PluginLoadingMechanism.GUESS,
            ):
                module_to_inspect = self._mechanism_import(file_path)
                # if module_to_inspect:
                #     logger.debug('Module Import : {}'.format(file_path))

            if not module_to_inspect:
                if mechanism in (
                    self.PluginLoadingMechanism.LOAD_SOURCE,
                    self.PluginLoadingMechanism.GUESS,
                ):
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
                self._logger.debug("", exc_info=True)

        return len(self._plugins) - current_plugins_count, plugins_found

    def register_paths(
        self,
        paths_to_register: list[str],
        package_name: str | None = None,
        mechanism: int = PluginLoadingMechanism.GUESS,
    ) -> list[Type]:
        """
        Registers given paths within the factory. The factory will immediately being searching recursively withing
        this location for any plugin.

        :param paths_to_register: absolute paths to register into the factory
        :param package_name: package name current registered plugins will belong to. Default to tDcc.
        :param mechanism: plugin load mechanism to use
        :return: total amount of registered plugins.
        """

        paths_to_register = helpers.force_list(paths_to_register)

        total_plugins = 0
        visited = set()
        plugins_found = list()
        for path_to_register in paths_to_register:
            if not path_to_register:
                continue
            base_name = (
                pathlib.Path(
                    os.path.splitext(path_to_register)[0]
                    if os.path.isfile(path_to_register)
                    else path_to_register
                )
                .resolve()
                .as_posix()
            )
            if base_name in visited:
                continue
            visited.add(base_name)
            plugins_count, found = self.register_path(
                path_to_register, mechanism=mechanism, package_name=package_name
            )
            total_plugins += plugins_count
            plugins_found.extend(found)

        plugins_found = helpers.remove_dupes(plugins_found)

        return plugins_found

    def register_paths_from_env_var(
        self,
        env_var: str,
        package_name: str | None = None,
        mechanism: int = PluginLoadingMechanism.GUESS,
    ) -> list[Type]:
        """
        Registers paths contained in given environment variables. Paths must be separated with OS separator.

        :param env_var: environment variable we are going to retrieve paths from
        :param package_name: package name current registered plugins will belong to. Default to tDcc.
        :param mechanism: plugin load mechanism to use
        """

        paths = os.environ.get(env_var, "").split(os.pathsep)
        if not paths:
            return []

        return self.register_paths(
            paths, package_name=package_name, mechanism=mechanism
        )

    def register_plugin_from_class(
        self, plugin_class: Type, package_name: str | None = None
    ) -> bool:
        """
        Registers the given class type as a plugin for this factory. Note that the given type class must be inherited
        from the factory interface. Useful when you have direct access to the plugin classes without the need of
        searching disk locations (which is slow).

        :param plugin_class: class type to add to the factory
        :param package_name: package name current registered plugins will belong to. Default to tDcc.
        :return: True if the registration is successful; False otherwise.
        """

        for interface in self._interfaces:
            if not inspect.isclass(plugin_class) or not issubclass(
                plugin_class, interface
            ):
                return False

        if not package_name:
            class_id = self._get_identifier(plugin_class)
            split_id = class_id.replace(".", "-").split("-")[0]
            package_name = split_id if split_id != class_id else "tp-dcc"

        self._plugins.setdefault(package_name, list()).append(plugin_class)

        return True

    def register_by_package(self, package_path: str):
        """
        Registers all plugins located in the given package.

        :param package_path: package path.

        .note:: this is a costly operation because it requires a recursive search by importing all submodules and
            searching them.
        """

        for sub_module in modules.iterate_modules(package_path):
            file_name = os.path.splitext(os.path.basename(sub_module))[0]
            if file_name.startswith("__") or sub_module.endswith(".pyc"):
                continue
            module_path = os.path.normpath(sub_module)
            module_dotted_path = modules.convert_to_dotted_path(module_path)
            if not module_dotted_path:
                self._logger.warning(
                    f"Skipping module due to invalid path: {sub_module} -> {module_dotted_path}"
                )
                continue
            sub_module_obj = None
            try:
                sub_module_obj = modules.import_module(
                    module_dotted_path, skip_errors=True
                )
            except ValueError:
                self._logger.error(
                    "Failed to load plugin module: {}".format(sub_module)
                )
            except ImportError:
                self._logger.error(
                    "Failed to import plugin module: {}".format(sub_module),
                    exc_info=True,
                )
                continue
            if not sub_module_obj:
                self._logger.debug(
                    "Failed to load/import plugin module: {}".format(sub_module)
                )
                continue
            for member in modules.iterate_module_members(
                sub_module_obj, predicate=inspect.isclass
            ):
                self.register_plugin_from_class(member[1])

    def paths(self, package_name: str | None = None) -> list[str]:
        """
        Returns all registered paths in the factory.
        """

        package_name = package_name or "tp-dcc"
        return list(self._registered_paths.get(package_name, dict()).keys())

    def identifiers(self, package_name: str | None = None) -> set:
        """
        Returns a list of plugin class names within the factory. The list of class names is unique, so classes which
        share the same name will not appear twice.

        :param package_name: package name current registered plugins will belong to. Default to tDcc.
        """

        package_name = package_name or "tp-dcc"
        return {
            self._get_identifier(plugin)
            for plugin in self._plugins.get(package_name, list())
        }

    def versions(self, identifier: str, package_name: str | None = None) -> list[str]:
        """
        Returns a list of all the versions available for the plugins with the given identifier.

        :param identifier: plugin identifier to check
        :param package_name: package name current registered plugins will belong to. Default to tDcc.
        """

        package_name = package_name or "tp-dcc"

        if not self._version_identifier:
            return list()

        return sorted(
            self._get_version(plugin)
            for plugin in self._plugins.get(package_name, list())
            if self._get_identifier(plugin) == identifier
        )

    def plugins(self, package_name: str | None = None) -> list[Type]:
        """
        Returns a unique list of plugins. Where multiple versions are available the highest version will be given.

        :param package_name: package name current registered plugins will belong to.
        """

        package_name = package_name or "tp-dcc"

        ordered_plugins = list()
        plugins = [
            self.get_plugin_from_id(identifier, package_name=package_name)
            for identifier in self.identifiers(package_name=package_name)
        ]
        plugins_to_order = [plugin for plugin in plugins if hasattr(plugin, "ORDER")]
        plugins_ordered = sorted(plugins_to_order, key=operator.attrgetter("ORDER"))
        ordered_plugins.extend(plugins_ordered)
        for plugin in plugins:
            if plugin in ordered_plugins:
                continue
            ordered_plugins.append(plugin)

        return ordered_plugins

    def get_plugin_from_id(
        self,
        plugin_id: str,
        package_name: str | None = None,
        plugin_version: int | float | None = None,
    ) -> type[Any] | None:
        """
        Retrieves the plugin with given plugin identifier. If you require a specific version of a plugin (in a
        scenario where there are multiple plugins with the same identifier) this can also be specified.

        :param plugin_id: identifying value of the plugin you want to retrieve
        :param package_name: package name current registered plugins will belong to.
        :param plugin_version: version of the plugin you want. If factory has no versioning identifier specified this
            argument has no effect.
        :return: plugin found.
        """

        package_name = package_name or "tp-dcc"

        if package_name and package_name not in self._plugins:
            self._logger.error(
                'Impossible to retrieve plugin from id: {} package: "{}" not registered!'.format(
                    plugin_id, package_name
                )
            )
            return None

        if package_name:
            matching_plugins = [
                plugin
                for plugin in self._plugins.get(package_name, list())
                if self._get_identifier(plugin) == plugin_id
            ]
        else:
            matching_plugins = list()
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
                if hasattr(plugin_cls, "DCCS") and dcc not in plugin_cls.DCCS:
                    continue
                _matching_plugins.append(plugin_cls)
            matching_plugins = _matching_plugins
        if not matching_plugins:
            self._logger.warning(
                f'No plugin with id "{plugin_id}" found in package "{package_name}" for DCC: {dcc}'
            )
            return None

        versions = {self._get_version(plugin): plugin for plugin in matching_plugins}
        ordered_versions = [version.LooseVersion(str(v)) for v in list(versions.keys())]

        # If not version given, we return the plugin with the highest value
        if not plugin_version:
            return versions[str(ordered_versions[0])]

        plugin_version = version.LooseVersion(str(plugin_version))
        if plugin_version not in ordered_versions:
            self._logger.warning(
                'No Plugin with id "{}" and version "{}" found in package "{}"'.format(
                    plugin_id, plugin_version, package_name
                )
            )
            return None

        return versions[str(plugin_version)]

    # noinspection PyShadowingNames
    def get_loaded_plugin_from_id(
        self,
        plugin_id: str,
        package_name: str | None = None,
        plugin_version: str | None = None,
        dcc: str | None = None,
    ) -> Plugin | None:
        """
        Retrieves the plugin with given plugin identifier. If you require a specific version of a plugin (in a
        scenario where there are multiple plugins with the same identifier) this can also be specified.

        :param plugin_id: identifier value of the plugin you want to retrieve
        :param package_name: package name current registered plugins will belong to.
        :param plugin_version: version of the plugin you want. If factory has no versioning identifier
            specified this argument has no effect.
        :param dcc: optional DCC to retrieve plugin of.
        :return: plugin instance.
        """

        package_name = package_name or "tp-dcc"

        if package_name and package_name not in self._loaded_plugins:
            self._logger.debug(
                'Impossible to retrieve loaded plugin from id: {} package: "{}" not registered!'.format(
                    plugin_id, package_name
                )
            )
            return None

        if package_name:
            matching_plugins = [
                plugin
                for plugin in self._loaded_plugins.get(package_name, [])
                if self._get_identifier(plugin) == plugin_id
            ]
        else:
            matching_plugins = []
            for plugins in list(self._loaded_plugins.values()):
                for plugin in plugins:
                    if self._get_identifier(plugin) == plugin_id:
                        matching_plugins.append(plugin)

        if not matching_plugins:
            self._logger.warning(
                'No loaded plugin with id "{}" found in package "{}"'.format(
                    plugin_id, package_name
                )
            )
            return None

        if dcc:
            matching_plugins = [
                plugin_cls for plugin_cls in matching_plugins if dcc in plugin_cls.DCCS
            ]
        if not matching_plugins:
            self._logger.warning(
                'No loaded plugin with id "{}" found in package "{}" for DCC: {}'.format(
                    plugin_id, package_name, dcc
                )
            )
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
            self._logger.warning(
                'No Plugin with id "{}" and version "{}" found in package "{}"'.format(
                    plugin_id, plugin_version, package_name
                )
            )
            return None

        return versions[str(plugin_version)]

    def load_plugin(
        self, plugin_id: str, package_name: str | None = None, **kwargs
    ) -> Type | None:
        """
        Loads a given plugin by the given name.

        :param plugin_id: id of the plugin to load.
        :param package_name: optional package name plugin we want to load belongs to.
        :return: instance of the loaded plugin.
        """

        package_name = package_name or "tp-dcc"

        plugin_class = self.get_plugin_from_id(plugin_id, package_name=package_name)
        if not plugin_class:
            return None

        self._logger.debug("Loading plugin: {}".format(plugin_id))
        spec = getfullargspec(plugin_class.__init__)
        keywords = spec.kwonlyargs
        args = spec.args
        if (args and "factory" in args) or (keywords and "factory" in keywords):
            kwargs["factory"] = self
        # noinspection PyBroadException
        try:
            plugin_instance = plugin_class(**kwargs)
        except Exception:
            self._logger.error(
                "Failed to load plugin: {}".format(plugin_id), exc_info=True
            )
            return None

        self._loaded_plugins.setdefault(package_name, list())
        plugin_instance.is_loaded = True
        self._loaded_plugins[package_name].append(plugin_instance)

        return plugin_instance

    def load_all_plugins(self, package_name: str | None = None, **kwargs):
        """
        Loops over all registered plugin and loads them.

        :param package_name: package name current registered plugins will belong to. Default to tDcc.
        """

        package_name = package_name or "tp-dcc"

        for pkg_name, plugin_classes in self._plugins.items():
            if package_name and pkg_name != package_name:
                continue
            for plugin_class in plugin_classes:
                plugin_id = self._get_identifier(plugin_class)
                self.load_plugin(plugin_id, package_name=package_name, **kwargs)

    def unload_all_plugins(self, package_name: str | None = None):
        """
        Loops over all loaded plugins and unloads them.

        :param package_name: package name current registered plugins will belong to. Default to tDcc.
        """

        package_name = package_name or "tp-dcc"
        if package_name not in self._loaded_plugins:
            return
        self._loaded_plugins[package_name].clear()

    def unregister_path(self, path, package_name: str | None = None):
        """
        Unregister given path from the list of registered paths.

        :param path: Absolute path we want to unregister from registered factory paths
        :param package_name: package name current registered plugins will belong to. Default to tDcc.
        """

        registered_paths = self._registered_paths.copy()

        self._plugins = list()
        self._registered_paths = dict()

        for pkg_name, registered_paths_dict in registered_paths.items():
            for original_path, mechanism in registered_paths_dict.items():
                if (
                    package_name == pkg_name
                    and pathlib.Path(original_path).resolve()
                    == pathlib.Path(path).resolve()
                ):
                    continue
                self.register_path(
                    original_path, package_name=pkg_name, mechanism=mechanism
                )

    def reload(self):
        """
        Clears all registered plugins and performs a search over all registered paths.
        """

        registered_paths = self._registered_paths.copy()

        self.clear()

        for package_name, registered_paths_dict in registered_paths.items():
            for original_path, mechanism in registered_paths_dict.items():
                self.register_path(
                    original_path, package_name=package_name, mechanism=mechanism
                )

    def clear(self):
        """
        Clears all the plugins and registered paths.
        """

        self._plugins.clear()
        self._registered_paths.clear()
        self._loaded_plugins.clear()

    @staticmethod
    def _mechanism_import(file_path: str) -> ModuleType | None:
        """
        Internal function that will try to retrieve a module from a given path by looking current sys.path env var.

        :param file_path: str, absolute file path of a Python file
        :return: imported module.
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
        Internal function that will try to retrieve a module by directly loading its source code.

        :param file_path: absolute file path of a Python file
        :return: loaded module.
        """

        return modules.load_module_from_source(file_path)

    def _get_identifier(self, plugin: str | Type) -> str:
        """
        Internal function that uses plugin identifier to request the identifying name of the plugin.

        :param plugin: plugin to take name from
        """

        identifier = getattr(plugin, self._plugin_identifier)

        if inspect.isfunction(identifier):
            return identifier()

        return identifier

    def _get_version(self, plugin: str | Type) -> str:
        """
        Internal function that uses plugin version identifier to request the version number of the plugin.

        :param plugin: plugin to take version from
        """

        identifier = getattr(plugin, self._version_identifier)

        if inspect.isfunction(identifier):
            return str(identifier())

        return str(identifier)
