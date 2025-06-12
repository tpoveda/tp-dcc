from __future__ import annotations

import os
import json
import logging
import inspect
from types import ModuleType
from typing import cast, Any
from collections.abc import Callable, Sequence

try:
    from packaging.version import Version
except ImportError:
    from distutils.version import LooseVersion as Version  # type: ignore

import yaml

from tp.libs.python import modules

from .dictplugin import DictPlugin
from .plugin import Plugin, PluginDependencyError


class PluginLoadError(Exception):
    """Exception raised when a plugin fails to load."""

    pass


class PluginsManager:
    """Class that allows to discover/register a collection of plugins based on
    specific interface classes.

    This manager handles the discoverability of plugins based on the interface
    classes and the registration of the plugins that are found.

    Plugins are classes that inherit from the base `Plugin` class.

    When a plugin is registered, the manager will store it in a dictionary with
    the plugin's id as key and the plugin class as value.

    The manager also exposes the `load_plugin` method that allows to load
    already registered plugins,this will create an instance of the plugin and
    will register it.

    In order to access plugin, you can use the `get_plugin` method that will
    return:
        - The plugin instance if it was already loaded.
        - The plugin class if it was not loaded yet.
    """

    def __init__(
        self,
        interfaces: list[type[Plugin] | type[Any]] | None = None,
        variable_name: str | None = None,
        version_name: str | None = None,
        name: str | None = None,
        log_errors: bool = True,
    ):
        """Constructor.

        Args:
            interfaces: list of base classes that the plugins handled by this
                manager instance will inherit from
            variable_name: Class variable name that will become the UUID of the
                class when caching out the plugin class in the manager.
            version_name: Class variable name that will become the version of
                the class when caching out the plugin class in the manager.
            name: optional name for the manager instance
            log_errors: whether to log errors or not when registering plugins.
        """

        self._interfaces = interfaces or [Plugin]
        self._variable_name = variable_name or "id"
        self._version_name = version_name or "version"
        self._name = ".".join(
            (
                self.__class__.__module__,
                f"{name}PluginsManager" if name else self.__class__.__name__,
            )
        )
        self._log_errors = log_errors
        self._plugins: dict[str, dict[str, type[Plugin]]] = {}
        self._loaded_plugins: dict[str, dict[str, Plugin]] = {}
        self._base_paths: list[str] = []
        self._load_callbacks: list[Callable[[Plugin], None]] = []
        self._logger = logging.getLogger(f"tp.{self._name}")

    @property
    def paths(self) -> list[str]:
        """Returns the list of registered paths.

        Returns:
            list of registered paths.
        """

        return self._base_paths

    @property
    def plugin_ids(self) -> list[str]:
        """Returns the list of registered plugin ids.

        Returns:
            list of registered plugin ids.
        """

        return [name for name in self._plugins.keys()]

    @property
    def loaded_plugin_ids(self) -> list[str]:
        """Returns the list of loaded plugin ids.

        Returns:
            list of loaded plugin ids.
        """

        return [name for name in self._loaded_plugins.keys()]

    @property
    def plugin_classes(self) -> list[type[Plugin]]:
        """Returns the list of registered plugin classes.

        Returns:
            list of registered plugin classes.
        """

        return [
            self._plugins[name][max(self._plugins[name].keys())]
            for name in self._plugins
        ]

    @property
    def loaded_plugins(self) -> list[Plugin]:
        """Returns the list of loaded plugin instances.

        Returns:
            list of loaded plugin instances.
        """

        return [
            self._loaded_plugins[name][max(self._loaded_plugins[name].keys())]
            for name in self._loaded_plugins
        ]

    @property
    def name(self) -> str:
        """Getter that returns the name of the manager instance.

        Returns:
            name of the manager instance
        """

        return self._name

    def register_paths(self, paths: Sequence[str | None]):
        """Loops recursively through the given paths discovering and
        registering all the plugins found.

        Args:
            paths: list of absolute paths to search for plugins in them
                recursively.
        """

        valid_paths = [path for path in paths if path and path not in self._base_paths]
        visited: set[str] = set()
        self._base_paths.extend(valid_paths)
        for path in paths:
            if not path:
                continue
            real_path = os.path.realpath(path)
            if real_path in visited:
                continue
            visited.add(real_path)
            if os.path.isdir(real_path):
                self.register_by_package(real_path)
            elif os.path.isfile(real_path):
                self.register_path(real_path)
            else:
                # Handle edge cases: broken symlinks, special files, etc.
                self._logger.warning(f"Skipping unsupported path: {real_path}")

    def register_path(self, path: str) -> ModuleType | None:
        """Registers a plugin based on the given path.

        Args:
            path: absolute path to the plugin file to register.

        Returns:
            ModuleType: module that was registered if successful; None
                otherwise.
        """

        imported_module: ModuleType | None = None

        if os.path.isfile(path) and modules.is_valid_module_path(path):
            self._logger.debug(f'Loading plugin from file path: "{path}"')
            dotted_path = modules.convert_to_dotted_path(path)
            if dotted_path:
                if self._log_errors:
                    imported_module = modules.import_module(dotted_path)
                else:
                    imported_module = modules.safe_import_module(dotted_path)
        elif modules.is_dotted_path(path):
            self._logger.debug(f'Loading plugin from dotted path: "{path}"')
            if self._log_errors:
                imported_module = modules.import_module(path)
            else:
                imported_module = modules.safe_import_module(path)

        if imported_module is not None:
            self.register_by_module(imported_module)

        return imported_module

    def register_by_environment_variable(self, env_variable: str):
        """Registers all the plugins found in the paths defined by the given
        environment variable.

        Args:
            env_variable: name of the environment variable that contains the
                paths to register.
        """

        paths = os.environ.get(env_variable, "").split(os.pathsep)
        if not paths:
            return
        self._logger.debug(
            f'Loading plugins from environment variable: "{env_variable}", {paths}'
        )
        self.register_paths(paths)

    def register_by_package(self, package_path: str):
        """Loops through all the Python modules found in the given package
        path and registers all plugin classes that inherit from the manager
        plugin interfaces.

        Args:
            package_path: absolute path to the package to register.
        """

        for module_path in modules.iterate_package_modules(package_path):
            if not module_path or module_path.endswith(".pyc"):
                continue

            self.register_path(module_path)

    def register_by_module(self, module: ModuleType):
        """Loops through all the class members defined within the given Python
        module and registers all plugin classes that inherit from the manager
        plugin interfaces.

        Args:
            module: Python module to register.
        """

        if not inspect.ismodule(module):
            return

        for _, cls in modules.iterate_module_members(module, predicate=inspect.isclass):
            self.register_plugin(cast(type[Plugin], cls))

    def register_plugin(self, plugin_class: type[Plugin]):
        """Registers the given plugin class if it inherits from the manager
        plugin interfaces and also defines a unique ID using the class
        variable name defined in the manager instance.

        Args:
            plugin_class: plugin class to register.
        """

        is_interface_subclass: bool = False
        for interface in self._interfaces:
            if issubclass(plugin_class, interface):
                is_interface_subclass = True
                break
        if not is_interface_subclass:
            return

        name = getattr(plugin_class, self._variable_name, plugin_class.__name__)
        try:
            version_str = getattr(plugin_class.metadata, "version", "0.1.0")
        except AttributeError:
            version_str = (
                getattr(plugin_class, "version")
                if hasattr(plugin_class, "version")
                else "0.1.0"
            )
        version_str = str(version_str)

        if not name:
            if plugin_class not in self._interfaces:
                self._logger.warning(f"Plugin without valid ID: {plugin_class}")
            return

        # Make sure the version follows a valid version format.
        try:
            version = Version(version_str)  # noqa: F841
        except ValueError:
            self._logger.warning(
                f"Plugin '{name}' has an invalid version '{version_str}'."
            )
            return

        if name not in self._plugins:
            self._plugins[name] = {}

        existing_versions = self._plugins[name]
        if version_str in existing_versions:
            self._logger.warning(
                f"Plugin '{name}' version {version_str} is already registered."
                f" Overwriting."
            )

        self._logger.debug(f'Registering plugin: "{name}" version {version_str}')
        self._plugins[name][version_str] = plugin_class

    def get_plugin(
        self, name: str, version: str | None = None
    ) -> type[Plugin] | Plugin | None:
        """Returns the plugin class or instance (if the plugin was loaded)
        associated with the given name.

        Args:
            name: name of the plugin to return.
            version: optional version of the plugin to return. If not
                provided, the latest version will be returned.

        Returns:
            plugin class or instance associated with the given name. None if
            a plugin with the given name is not registered.
        """

        if name not in self._plugins:
            return None

        versions = self._plugins[name]

        if version:
            try:
                return versions.get(version)
            except ValueError:
                self._logger.warning(f"Invalid version requested: {version}")
                return None

        latest_version = max(versions.keys())

        return versions[latest_version]

    def loaded_plugin(self, name: str, version: str | None = None) -> Plugin | None:
        """Returns the loaded plugin instance associated with the given name.

        Args:
            name: name of the plugin to return.
            version: optional version of the plugin to return. If not
                provided, the latest version will be returned.

        Returns:
            plugin instance associated with the given name. None if a plugin
            with the given name is not loaded.
        """

        if name not in self._loaded_plugins:
            return None

        versions = self._loaded_plugins[name]

        if version:
            try:
                return versions.get(version)
            except ValueError:
                self._logger.warning(f"Invalid version requested: {version}")
                return None

        latest_version = max(versions.keys())

        return versions[latest_version]

    def get_plugin_versions(
        self, name: str, as_version_objects: bool = False
    ) -> list[str | Version]:
        """Returns a list of all available versions for a given plugin ID.

        Args:
            name: Plugin ID.
            as_version_objects: Whether to return the versions as `Version`
                objects or as strings.

        Returns:
            List of available versions as strings, sorted from oldest to
            newest.
        """

        if name not in self._plugins:
            self._logger.warning(f"Plugin '{name}' is not registered.")
            return []

        # Convert version strings to Version objects for proper sorting
        versions = sorted(self._plugins[name].keys(), key=lambda v: Version(str(v)))

        return [Version(v) if as_version_objects else str(v) for v in versions]

    def find_plugins_by_metadata(self, **filters) -> list[type[Plugin]]:
        """Finds plugins based on the given metadata filters.

        Args:
            **filters: metadata filters to use to find the plugins.

        Returns:
            list of plugins that match the given metadata filters
        """

        result: list[type[Plugin]] = []
        for _, plugins in self._plugins.items():
            for version, plugin in plugins.items():
                if all(
                    getattr(plugin.metadata, k, None) == v for k, v in filters.items()
                ):
                    result.append(plugin)

        return result

    def load_plugin(
        self, name: str, version: str | None = None, **kwargs
    ) -> Plugin | None:
        """Loads the plugin associated with the given name if it is registered.

        Args:
            name: name of the plugin to load.
            version: optional version of the plugin to load. If not provided,
                the latest version will be loaded.
            **kwargs: optional keyword arguments to pass to the plugin
                constructor.

        Returns:
            plugin instance if the plugin was loaded successfully; None
                otherwise.
        """

        plugin_class = self.get_plugin(name, version)
        if not plugin_class:
            raise PluginLoadError(
                f"Plugin '{name}' version '{version}' not registered."
            )

        try:
            plugin_version = Version(plugin_class.metadata.version)
        except AttributeError:
            plugin_version = Version("0.1.0")

        if name not in self._loaded_plugins:
            self._loaded_plugins[name] = {}

        # If the requested version is already loaded, return it.
        if plugin_version in self._loaded_plugins[name]:
            return self._loaded_plugins[name][str(plugin_version)]

        try:
            dependencies = plugin_class.dependencies
        except AttributeError:
            dependencies = []
        for dep in dependencies:
            if dep not in self._loaded_plugins:
                self.load_plugin(dep)

        # Load dependencies first
        for dependency_name in dependencies:
            if dependency_name not in self._loaded_plugins:
                if dependency_name not in self._plugins:
                    raise PluginDependencyError(
                        f"Plugin '{name}' depends on unregistered plugin "
                        f"'{dependency_name}'."
                    )
                self.load_plugin(dependency_name, **kwargs)

        self._logger.debug(f"Loading plugin: {name}")

        spec = inspect.getfullargspec(plugin_class.__init__)  # type: ignore
        args = spec.args
        keywords = spec.kwonlyargs
        if (args and "manager" in args) or (keywords and "manager" in keywords):
            kwargs["manager"] = self
        try:
            new_plugin = plugin_class(**kwargs)  # type: ignore
            if hasattr(new_plugin, "initialize") and callable(new_plugin.initialize):
                new_plugin.initialize()
        except Exception as err:
            self._logger.error(
                f"Failed to load plugin: {name}, arguments: {kwargs}",
                exc_info=True,
            )
            raise PluginLoadError(f"Failed loading plugin {name}") from err

        self._loaded_plugins[name][str(plugin_version)] = new_plugin

        for callback in self._load_callbacks:
            callback(new_plugin)

        return new_plugin

    def load_all_plugins(self, **kwargs):
        """Loops through all the registered plugins and loads them.

        Args:
            kwargs: optional keyword arguments to pass to the plugin
                constructor.
        """

        for name in self._plugins:
            self.load_plugin(name, **kwargs)

    def reload_plugin(self, name: str, **kwargs) -> Plugin | None:
        """Reloads the plugin associated with the given name if it was loaded.

        Args:
            name: name of the plugin to reload.
            **kwargs: optional keyword arguments to pass to the plugin
                constructor.

        Returns:
            plugin instance if the plugin was reloaded successfully; None
                otherwise.
        """

        self.unload_plugin(name)
        return self.load_plugin(name, **kwargs)

    def unload_plugin(self, name: str) -> bool:
        """Unloads the plugin associated with the given name if it was loaded.
        Note that the plugin is not removed from the registered plugins.

        Args:
            name: name of the plugin to unload.
        """

        if name not in self._loaded_plugins:
            return False

        plugin = self._loaded_plugins.pop(name)
        try:
            if hasattr(plugin, "shutdown") and callable(plugin.shutdown):
                plugin.shutdown()
        except Exception as err:
            self._logger.error(
                f"Error shutting down plugin: {name} > {err}", exc_info=True
            )

        return True

    def unload_all_plugins(self):
        """Unloads all the loaded plugins."""

        self._loaded_plugins.clear()

    def on_plugin_loaded(self, callback: Callable[[Plugin], None]):
        """Registers a callback to be called when a plugin is loaded by the
            manager.

        Args:
            callback: callback to register.
        """

        self._load_callbacks.append(callback)


class DictPluginsManager(PluginsManager):
    """Custom `PluginsManager` that allows to register plugins based on
    dictionary files such as YAML or JSON files containing dictionary data.
    """

    def register_path(self, path: str) -> ModuleType | None:
        """Overrides `register_path` to registers a `DictPlugin` based on the
        given path.

        Args:
            path: absolute path to the plugin file to register.

        Returns:
            ModuleType: module that was registered if successful; None
                otherwise.
        """

        if os.path.isfile(path) and path.endswith((".yaml", ".yml", ".json")):
            self.register_dictionary_file_plugin(path)

        return None

    def register_by_package(self, package_path: str):
        """Overrides `register_by_package` to register plugins based on
        dictionary files (YAML or JSON) found in the given package path.

        Args:
            package_path: absolute path to the package to register.
        """

        for root, dirs, files in os.walk(package_path):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    file_path = os.path.join(root, file)
                    self.register_path(file_path)

    def register_dictionary_file_plugin(self, path: str):
        """Registers a plugin defined as a dictionary file (JSON or YAML).

        Args:
            path: Path to the JSON/YAML file.
        """

        if not os.path.exists(path):
            self._logger.warning(f"File path does not exist: {path}")
            return

        if path.endswith(".json"):
            with open(path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    self._logger.error(
                        f"Failed to parse JSON plugin: {path}", exc_info=True
                    )
                    return
        elif path.endswith((".yaml", ".yml")):
            with open(path, "r") as f:
                try:
                    data = yaml.safe_load(f)
                except yaml.YAMLError:
                    self._logger.error(
                        f"Failed to parse YAML plugin: {path}", exc_info=True
                    )
                    return

        data["__base_path__"] = os.path.dirname(path)
        plugin_id = data.get("id")
        version = str(data.get("version", "0.1.0"))

        if not plugin_id:
            self._logger.warning(f"Dictionary file plugin at {path} has no 'id'")
            return

        # Dynamically create a plugin class from DictPlugin base.
        plugin_class = type(
            f"DictPlugin_{plugin_id}_{version.replace('.', '_')}",
            (DictPlugin,),
            {
                "__doc__": f"Plugin defined in {os.path.basename(path)}",
                "metadata": type("Meta", (), data),
            },
        )

        # Set required attributes for registration.
        setattr(plugin_class, self._variable_name, plugin_id)
        setattr(plugin_class, self._version_name, version)
        setattr(plugin_class, "data", data)

        self._logger.debug(
            f"Registering Dictionary file plugin: {plugin_id} (v{version})"
        )

        self.register_plugin(cast(type[Plugin], plugin_class))
