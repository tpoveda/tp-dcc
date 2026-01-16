"""Meta Registry for managing metaclass registration.

This module provides the MetaRegistry class which is responsible for
registering, storing, and retrieving metaclasses for the meta system.
"""

from __future__ import annotations

import inspect
import os
from collections.abc import Iterable
from types import ModuleType
from typing import TYPE_CHECKING

from loguru import logger

from tp.libs.python import modules
from tp.libs.python.decorators import Singleton

if TYPE_CHECKING:
    from .base import MetaBase


class MetaRegistry(metaclass=Singleton):
    """Manages the registration and storage of metaclasses for a specified type
    system.

    The `MetaRegistry` class is responsible for facilitating the registration
    and retrieval of metaclasses.

    It stores registered metaclasses in a centralized cache, provides methods
    to register metaclasses from various sources (e.g., individual classes,
    modules, packages, environment variables), and ensures unique
    registration of metaclasses.

    The class also includes functionality to verify and retrieve registered
    metaclasses by their name.

    Attributes:
        META_ENV_VAR: Name of the environment variable that holds paths for
            metaclasses registration.
        _CACHE: Internal storage cache mapping registry names to
            MetaBase-derived classes.
    """

    META_ENV_VAR = "TP_DCC_META_PATHS"
    _CACHE: dict[str, type[MetaBase]] = {}

    def __init__(self):
        super().__init__()

        try:
            self.reload()
        except ValueError:
            logger.error("Failed to registry meta classes", exc_info=True)

    @staticmethod
    def registry_name_for_class(class_type: type[MetaBase]) -> str:
        """Get the registry name for the given class.

        This static method retrieves the registry name associated with the
        given class type.

        If the class has an `ID` attribute, its value is returned; otherwise,
        the class's name is returned as the default identifier.

        Args:
            class_type: The class type for which the registry name is to be
            determined.

        Returns:
            The registry name for the provided class type.
        """

        if hasattr(class_type, "ID") and class_type.ID:
            return class_type.ID

        return class_type.__name__

    @classmethod
    def is_in_registry(cls, type_name: str) -> bool:
        """Determine whether a given type name is already registered in the class
        cache.

        This method checks if the specified type name exists in the `_CACHE`
        dictionary, indicating that the type has been registered.

        It provides a mechanism to verify the presence of a type in the
        registry maintained by the class.

        Args:
            type_name: The name of the type to check for in the class registry.

        Returns:
            True if the type name is in the registry, False otherwise.
        """

        return type_name in cls._CACHE

    @classmethod
    def get_type(cls, type_name: str) -> type[MetaBase] | None:
        """Retrieve the cached type associated with the given type name.

        This method searches the internal cache to find a type matching the
        provided type name.

        Args:
            type_name: The name of the type to retrieve from the cache.

        Returns:
            The cached type associated with the provided type name if it
                exists; `None` otherwise.
        """

        return cls._CACHE.get(type_name)

    @classmethod
    def types(cls) -> dict[str, type[MetaBase]]:
        """Return a copy of all registered types.

        Returns:
            A dictionary mapping registry names to their corresponding
                MetaBase subclasses.
        """

        return cls._CACHE.copy()

    @classmethod
    def clear_cache(cls):
        """Clear all registered metaclasses from the cache.

        This method removes all entries from the internal cache, effectively
        unregistering all previously registered metaclasses.
        """

        cls._CACHE.clear()

    @classmethod
    def unregister_meta_class(cls, class_obj: type[MetaBase]) -> bool:
        """Unregister a Meta class from the internal cache.

        Args:
            class_obj: The class object to be unregistered.

        Returns:
            True if the class was successfully unregistered; False if it
                was not found in the cache.
        """

        registry_name = cls.registry_name_for_class(class_obj)
        if registry_name in cls._CACHE:
            del cls._CACHE[registry_name]
            logger.debug(f"Unregistered MetaClass -> {registry_name}")
            return True
        return False

    @classmethod
    def register_meta_class(cls, class_obj: type[MetaBase]):
        """Register a Meta class to the internal cache of the system.

        This method verifies if the provided class object is a subclass or an
        instance of the base `MetaBase` class. If the verification passes and
        the class has not been previously registered, it is added to the cache.

        The registration process ensures that Meta classes remain organized and
        accessible throughout their use in the system.

        Args:
            class_obj: The class object to be registered. This object must
                either be a subclass or an instance of `MetaBase`.
        """

        # Import here to avoid circular imports
        from .base import MetaBase

        if issubclass(class_obj, MetaBase) or isinstance(class_obj, MetaBase):
            registry_name = cls.registry_name_for_class(class_obj)
            if registry_name in cls._CACHE:
                return
            logger.debug(
                f"Registering MetaClass -> {registry_name} | {class_obj}"
            )
            cls._CACHE[registry_name] = class_obj

    @classmethod
    def register_by_package(cls, package_path: str):
        """Register metaclasses by iterating through a package's modules.

        The method dynamically loads and iterates through the modules within
        a given package path. It verifies each module for validity and skips
        special files or duplicates.

        Once the valid modules are identified, the method identifies the
        classes defined in those modules and registers them as meta classes.

        Args:
            package_path: The path of the package whose modules are to be
                processed and whose classes are to be registered.
        """

        visited_packages = set()
        for sub_module in modules.iterate_modules(package_path):
            file_name = os.path.splitext(os.path.basename(sub_module))[0]
            if file_name in visited_packages or not modules.valid_module_path(
                sub_module
            ):
                continue

            if file_name.startswith("__") or file_name in visited_packages:
                continue
            visited_packages.add(file_name)
            sub_module_obj = modules.import_module(
                modules.convert_to_dotted_path(os.path.normpath(sub_module))
            )
            for member in modules.iterate_module_members(
                sub_module_obj, predicate=inspect.isclass
            ):
                cls.register_meta_class(member[1])

    @classmethod
    def register_by_module(cls, module: ModuleType):
        """Register all classes from the given module within the metaclass
        registry if they meet the required predicate.

        This method examines the contents of the provided module, identifies
        class definitions, and registers them with the metaclass registry if
        the predicate condition is satisfied.

        Notes:
            It ignores any non-modules passed to it and ensures that only
            actual classes from the module are processed.

        Args:
            module: The module to iterate over for identifying classes and
                registering them.
        """

        if not inspect.ismodule(module):
            return

        for member in modules.iterate_module_members(
            module, predicate=inspect.isclass
        ):
            cls.register_meta_class(member[1])

    @classmethod
    def register_meta_classes(cls, paths: Iterable[str]):
        """Register metaclasses from the given paths. Each entry in the
        paths can either be a directory or a file.

        Directories are processed to register metaclasses by their package,
        and files are processed to register metaclasses by their module.

        Notes:
            Invalid paths, such as non-existent directories or files that do
            not represent valid modules, are ignored.

        Args:
            paths: A collection of directory or file paths. Directories are
                recursively processed to register metaclasses by packages,
                while files are processed to register meta-classes by modules.
        """

        for path in paths:
            if not path:
                continue
            if os.path.isdir(path):
                cls.register_by_package(path)
                continue
            elif os.path.isfile(path):
                if not modules.valid_module_path(path):
                    continue
                imported_module = modules.import_module(
                    modules.convert_to_dotted_path(os.path.normpath(path))
                )
                if imported_module:
                    cls.register_by_module(imported_module)
                    continue

    @classmethod
    def register_by_env(cls, env_name: str):
        """Register metaclasses by fetching environment variable values and
        splitting them into paths.

        Args:
            env_name: The name of the environment variable to fetch.

        Raises:
            ValueError: If the specified environment variable does not exist
                or has no value.
        """

        environment_paths = os.getenv(env_name)
        if environment_paths is None:
            raise ValueError(
                f'No environment variable with name "{env_name}" exists!'
            )

        environment_paths = environment_paths.split(os.pathsep)

        cls.register_meta_classes(environment_paths)

    def reload(self):
        """Reload the registry data by re-registering using an environment
        variable.

        This method ensures that the registry information is updated
        dynamically based on the specified environment variable.

        It relies on a meta-environment variable for the re-registration
        process.

        Raises:
            KeyError: If the environment variable specified by
                MetaRegistry.META_ENV_VAR is not set or cannot be accessed.
        """

        self.register_by_env(MetaRegistry.META_ENV_VAR)
