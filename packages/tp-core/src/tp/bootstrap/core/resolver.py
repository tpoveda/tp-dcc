from __future__ import annotations

import os
import typing
from pathlib import Path
from importlib import reload
from collections.abc import Callable
from typing import cast, TypedDict, Any

from loguru import logger

from .package import Package
from . import constants, errors
from ..utils import fileio

if typing.TYPE_CHECKING:
    from .descriptor import Descriptor
    from .manager import PackagesManager


class PackageEntry(TypedDict):
    """Represents a package entry in the package configuration file."""

    name: str
    version: str
    enabled: bool


PackageConfig = dict[str, PackageEntry]


class Environment:
    """Class that manages the TP DCC Python pipeline environment.

    This class is responsible for loading and resolving packages in the TP DCC
    Python pipeline environment.

        - Handles the loading of packages from configuration files, resolving
            dependencies, and applying the packages to the current environment.
        - Provides methods for managing callbacks and running startup commands
            for the packages.

    The environment is initialized with a `PackagesManager` instance, which
    is used to manage the packages and their dependencies and can be
    configured with a list of packages to be loaded and their versions.
    """

    def __init__(self, packages_manager: PackagesManager):
        """Initializes the TP DCC Python pipeline environment.

        Args:
            packages_manager: The TP DCC Python pipeline packages manager.
        """

        self._packages_manager = packages_manager
        self._cache: dict[str, Package] = {}
        self._project_package: Package | None = None
        self._callbacks: dict[str, list[Callable]] = {}
        self._project_package_root = os.environ.get("TP_DCC_PROJECT_PACKAGE_ROOT", "")

    @property
    def packages(self) -> list[Package]:
        """The list of packages in the environment."""

        return list(self._cache.values())

    @property
    def project_package(self) -> Package | None:
        """The project package in the environment."""

        return self._project_package

    @property
    def callbacks(self) -> dict[str, list[Callable]]:
        """The callbacks registered in the environment."""

        return self._callbacks

    @staticmethod
    def package_from_path(path: str) -> Package:
        """Returns the package from the given path. The path can be either a
        package file path or a directory containing the package.

        Args:
            path: The path to the package file or directory.

        Returns:
            The package from the given path.
        """

        return Package(
            path
            if path.endswith(constants.PACKAGE_NAME)
            else os.path.join(path, constants.PACKAGE_NAME)
        )

    @staticmethod
    def load_packages_configuration_file(
        packages_config_file_path,
    ) -> PackageConfig:
        """Loads the packages configuration file.

        Args:
            packages_config_file_path: The path to the packages configuration
                file.

        Returns:
            The loaded packages configuration file.
        """

        data = fileio.load_yaml(packages_config_file_path)
        if not data:
            raise ValueError(
                f"Packages configuration YAML file path has incorrect "
                f'syntax: "{packages_config_file_path}"'
            )

        return cast(PackageConfig, data)

    def environment_config_file_path(self) -> str:
        """Returns the path to the environment configuration path for the
        current host on disk.

        Returns:
            The path to the environment configuration path for the current
            host on disk.

        Raises:
            MissingEnvironmentConfigFilePath: If the environment configuration
                file path does not exist.
        """

        environment_config_file_path = self._resolve_environment_config_path()
        if not environment_config_file_path.exists():
            raise errors.MissingEnvironmentConfigFilePathError(
                f"Environment config file does not exist: "
                f'"{environment_config_file_path}"'
            )

        return str(environment_config_file_path)

    def resolve_from_environment_configuration_file_path(
        self, packages_config_file_path: str, **kwargs: Any
    ) -> set[Package]:
        """Resolves the packages from the given configuration file path that
        contains a list of packages to be loaded with their versions.

        Args:
            packages_config_file_path: The path to the packages configuration
                file.
            **kwargs: Additional arguments to be passed to the resolver.

        Returns:
            Set of resolved packages.

        Raises:
            ValueError: If the packages configuration file path has incorrect
                syntax.
            TypeError: If the packages configuration file does not contain a
                list of dicts.
        """

        try:
            packages_config = self.load_packages_configuration_file(
                packages_config_file_path
            )
        except ValueError:
            logger.error(
                f"Packages configuration YAML file path has incorrect "
                f'syntax: "{packages_config_file_path}"',
                exc_info=True,
            )
            raise

        return self.resolve_packages(packages_config, **kwargs)

    def resolve_packages(
        self,
        packages_config: PackageConfig,
        apply: bool = True,
        run_command_scripts: bool = True,
    ) -> set[Package]:
        """Resolves the packages from the given list of packages to be loaded
        with their versions.

        Args:
            packages_config: List of packages to be loaded with their versions.
            apply: Whether to apply the packages or not.
            run_command_scripts: Whether to run the command scripts or not.

        Returns:
            Set of resolved packages.
        """

        resolved: set[Package] = set()

        logger.debug("Resolving requested packages:")
        for k, v in packages_config.items():
            logger.debug(f"\t{k}: {v}")

        for package_name, package_entry in packages_config.items():
            package_entry["name"] = package_name
            package_descriptor = self._packages_manager.descriptor_from_package_entry(
                package_entry
            )
            existing_package = self._cache.get(
                Package.name_for_package_name_and_version(
                    package_name, package_descriptor.version
                )
            )
            if existing_package:
                resolved.add(existing_package)
                continue

            # Resolve the package descriptor.
            package = package_descriptor.resolve()
            if package:
                resolved.add(package)

        # Apply the packages to the current environment.
        for package in resolved:
            if str(package) in self._cache:
                continue
            package.resolve(apply_environment=apply)
            self._cache[str(package)] = package

        # Set the project package.
        project_package = self.find_project_config_package()
        if not project_package:
            raise errors.MissingProjectPackageError(
                "Project package not found in the environment."
            )
        self._project_package = project_package
        os.environ["TP_DCC_PROJECT_PACKAGE_ROOT"] = str(self._project_package.root)

        self._reload_tp_namespace()

        if not apply:
            return resolved

        self._run_callbacks("pre_startup_commands")

        if run_command_scripts:
            self._run_startup_commands()

        return resolved

    def find_project_config_package(self) -> Package | None:
        """Finds the project package in the environment.

        Returns:
            The project package in the environment.
        """

        found_project_package: Package | None = None
        for pkg in self.packages:
            if Path(pkg.root, "configs", "prefs", "roots.yaml").exists():
                found_project_package = pkg
                break

        return found_project_package

    def package_by_name(self, package_name: str) -> Package | None:
        """Returns the package with the given name from the cache of packages.

        Args:
            package_name: The name of the package to be returned.

        Returns:
            The package with the given name.
        """

        found_package: Package | None = None
        for package in self._cache.values():
            if package.name == package_name:
                found_package = package
                break

        return found_package

    def existing_package(self, package: Package) -> Package | None:
        """Returns the package if it exists in the cache, otherwise returns
        None.

        This function first checks if the package exists in the cache. If it
        does, it returns the cached package. If it doesn't, it searches for
        the package in the package paths and caches it if found.

        Note:
            This is used to check if the package is already loaded in the
            environment. If the package is not found, it will be cached for
            future use.

        Args:
            package: The package to be searched.

        Returns:
            The package if it exists in the cache, otherwise None.
        """

        cached_package = self._cache.get(str(package))
        if cached_package is not None:
            return cached_package

        package_file_paths_locations = self._search_package_file_paths(
            package.name, str(package.version)
        )
        if not package_file_paths_locations:
            return None

        found_pkg: Package | None = None
        for package_file_path_location in package_file_paths_locations:
            pkg = Package(package_file_path_location)
            if pkg.version != package.version:
                continue
            found_pkg = pkg
            break
        if found_pkg is None:
            return None

        self._cache[str(found_pkg)] = found_pkg

        return found_pkg

    def package_for_descriptor(self, descriptor: Descriptor) -> Package | None:
        """Returns the package for the given descriptor.

        Args:
            descriptor: The package descriptor.

        Returns:
            The package for the given descriptor.
        """

        package_file_paths = self._search_package_file_paths(
            descriptor.name, descriptor.version
        )
        found_package: Package | None = None
        for package_file_path in package_file_paths:
            pkg = Package(package_file_path)
            if str(pkg.version) != descriptor.version:
                continue
            found_package = pkg
            break
        if found_package is None:
            return None

        return self._cache.get(str(found_package), found_package)

    def shutdown(self):
        """Shuts down all packages in the environment.

        Iterates over all packages in the cache and shuts them down and their
        dependencies.

        The shutdown process is done in the order of the dependencies, so that
        all dependencies are shut down before the package itself. This
        ensures that all dependencies are available when the package is
        shut down.

        Note:
            This function is called when the environment is being shut down.
            It is important to ensure that all packages are shut down
            properly to avoid any issues with the environment.
        """

        # Remove the TP_DCC_PROJECT_PACKAGE_ROOT environment variable if it
        # is not set in the environment.
        if os.environ.get("TP_DCC_PROJECT_PACKAGE_ROOT"):
            if self._project_package_root:
                os.environ["TP_DCC_PROJECT_PACKAGE_ROOT"] = self._project_package_root
            else:
                del os.environ["TP_DCC_PROJECT_PACKAGE_ROOT"]

        # Shutdown all packages in the environment.
        visited: set[str] = set()
        for package_name, package in self._cache.items():
            if not package.resolved:
                continue
            for dependency in package.dependencies:
                dependency_package = self.package_by_name(dependency.name)
                if (
                    dependency_package is not None
                    and str(dependency_package) not in visited
                ):
                    # noinspection PyBroadException
                    try:
                        dependency_package.shutdown()
                    except Exception:
                        logger.error(
                            f"Failed to shutdown package: {dependency_package}",
                            exc_info=True,
                        )
                    visited.add(str(dependency_package))

            if str(package) in visited:
                continue

            # noinspection PyBroadException
            try:
                package.shutdown()
            except Exception:
                logger.error(f"Failed to shutdown package: {package}", exc_info=True)
            visited.add(str(package))

    # noinspection PyMethodMayBeStatic
    def _reload_tp_namespace(self):
        """Internal function that reloads the TP DCC namespace.

        This is necessary because the TP DCC namespace may have changed after
        loading packages. This function forces a reload of the TP DCC namespace
        to ensure that all packages are loaded correctly.
        """

        import tp

        reload(tp)

    def _resolve_environment_config_path(self) -> Path:
        """Internal function that handles the discovery of the environment
        path for TP DCC Python pipeline configuration.

        Returns:
            The path to the environment configuration path for the current
            host on disk.
        """

        # 1. Try user-defined environment variable path (expanded)
        custom_env_path = os.getenv(
            constants.PACKAGES_ENVIRONMENT_CONFIG_PATH_ENV_VAR, ""
        )
        resolved_path = Path(os.path.expanduser(os.path.expandvars(custom_env_path)))
        if resolved_path.is_file():
            logger.debug(
                f"Loading package environment configuration from: {resolved_path}"
            )
            return resolved_path

        # 2. Try zooConfig configPath + env + file from another environment
        # variable
        config_filename = os.getenv(
            constants.PACKAGES_ENVIRONMENT_CONFIG_FILE_ENV_VAR, ""
        )
        candidate_path = (
            Path(self._packages_manager.config_path) / "env" / config_filename
        )
        if candidate_path.is_file():
            logger.debug(
                f"Loading package environment configuration from: {candidate_path}"
            )
            return candidate_path

        # 3. Fallback to the default file
        default_path = Path(self._packages_manager.config_path) / "env" / "dev.yaml"
        logger.debug(f"Loading package environment configuration from: {default_path}")
        return default_path

    def _search_package_file_paths(
        self, package_name: str, package_version: str
    ) -> list[str]:
        """Internal function that searches for the package file paths in the
        packages folder.

        Args:
            package_name: The name of the package to be searched.
            package_version: The version of the package to be searched.

        Returns:
            A list of package file paths.
        """

        # By default, the package path folder is the package name and a
        # version folder.
        # For example:
        #   packages/tp-package/0.1.0/package.yaml
        search_root = (
            Path(self._packages_manager.packages_path)
            / package_name
            / package_version
            / constants.PACKAGE_NAME
        )
        matches = list(search_root.parent.glob(search_root.name))

        # If not found, search for the package name only.
        # For example:
        #   packages/tp-package/package.yaml
        if not matches:
            search_root = (
                Path(self._packages_manager.packages_path)
                / package_name
                / constants.PACKAGE_NAME
            )
            matches = list(search_root.parent.glob(search_root.name))

        return [str(path) for path in matches]

    def _run_callbacks(self, name: str):
        """Internal function that runs the callbacks registered for the
        given name.

        Args:
            name: The name of the callback to be run.
        """

        for callback in self._callbacks.get(name, []):
            callback()

    def _run_startup_commands(self):
        """Internal function that runs the startup commands for all packages
        in the environment.

        Note:
            This function iterates over all packages in the cache and runs
            their startup commands. It also runs the startup commands for any
            dependencies of the packages. The startup commands are run in the
            order of the dependencies, so that all dependencies are started
            before the package itself. This ensures that all dependencies
            are available when the package is started.
        """

        visited: set[str] = set()
        for package_name, package in self._cache.items():
            for dependency in package.dependencies:
                dependency_package = self.package_by_name(dependency.name)
                if dependency_package and str(dependency_package) not in visited:
                    # noinspection PyBroadException
                    try:
                        dependency_package.startup()
                    except Exception:
                        logger.error(
                            f"Failed to run startup command for package: {package}",
                            exc_info=True,
                        )
                    visited.add(str(dependency_package))

            if str(package) not in visited:
                # noinspection PyBroadException
                try:
                    package.startup()
                except Exception:
                    logger.error(
                        f"Failed to run startup command for package: {package}",
                        exc_info=True,
                    )
                visited.add(str(package))
