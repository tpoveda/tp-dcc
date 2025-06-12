from __future__ import annotations

import os
from pathlib import Path
from typing import cast, Any

from loguru import logger

from tp.core.utils import env

from .host import Host
from . import constants
from .descriptor import PackageDescriptor
from .resolver import Environment, PackageEntry
from ..utils import fileio, flush


class PackagesManager:
    """Class that manages the TP DCC Python pipeline packages."""

    # Singleton instance of the TP DCC packages manager.
    _instance: PackagesManager | None = None

    def __init__(self, root_path: str):
        """Initializes the TP DCC Python pipeline packages manager.

        Args:
            root_path: The root location of the TP DCC Python packages.

        Raises:
            RuntimeError: If the TP DCC packages manager instance already
                exists.
            FileNotFoundError: If the TP DCC root path does not exist.
        """

        if self.__class__._instance is not None:
            raise RuntimeError(
                "Use `packages_manager_from_path()` to create the instance."
            )

        if not Path(root_path).exists():
            raise FileNotFoundError(f"TP DCC root path does not exist: {root_path}")

        tp_dcc_paths = self._resolve_paths(root_path)
        logger.debug(f"Initializing TP DCC Packages Manager from: {root_path}")
        logger.debug("TP DCC paths:")
        for k, v in tp_dcc_paths.items():
            logger.debug(f"\t{k}: {v}")

        self._root_path = tp_dcc_paths["root"]
        self._dev_path = tp_dcc_paths["dev"]
        self._config_path = tp_dcc_paths["config"]
        self._packages_path = tp_dcc_paths["packages"]
        self._resolver = Environment(self)

    @property
    def root_path(self) -> str:
        """The root path of the TP DCC Python pipeline packages."""

        return self._root_path

    @property
    def dev_path(self) -> str:
        """The path to the TP DCC Python packages dev folder."""

        return self._dev_path

    @property
    def config_path(self) -> str:
        """The path to the TP DCC Python packages config folder."""

        return self._config_path

    @property
    def packages_path(self) -> str:
        """The path to the TP DCC Python packages folder."""

        return self._packages_path

    @property
    def resolver(self) -> Environment:
        """The TP DCC Python pipeline packages resolver."""

        return self._resolver

    @classmethod
    def from_path(cls, path: str | Path) -> PackagesManager:
        """Creates a TP DCC packages manager instance from the given path.

        Args:
            path: Path to the TP DCC root folder.

        Returns:
            A TP DCC packages manager instance.

        Raises:
            FileNotFoundError: If the TP DCC root path does not exist.
        """

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"TP DCC Pipeline root path does not exist: {path}")

        if cls._instance is None:
            cls._instance = cls(str(path))

        return cls._instance

    @classmethod
    def current(cls) -> PackagesManager | None:
        """Returns the current TP DCC packages manager instance.

        Returns:
            The current initialized TP DCC packages manager instance.
        """

        return cls._instance

    @classmethod
    def set_current(cls, packages_manager: PackagesManager | None):
        """Sets the current TP DCC packages manager instance.

        Args:
            packages_manager: The TP DCC packages manager instance to set as
                current.
        """

        cls._instance = packages_manager

    @staticmethod
    def _resolve_paths(path: str) -> dict[str, str]:
        """Internal function that resolves all TP DCC packages paths from the
        given path.

        Args:
            path: Root path to start searching for packages from.

        Returns:
            Dictionary with the following keys:
                - root: Path to the TP DCC root folder.
                - config: Path to the TP DCC config folder.
                - packages: Path to the TP DCC packages folder.
        """

        logger.debug(f"Resolving TP DCC paths from: {path}")

        dev_folder = Path(path) / constants.DEV_FOLDER_NAME
        config_folder = dev_folder / constants.CONFIG_FOLDER_NAME
        packages_folder = Path(path) / constants.PACKAGES_FOLDER_NAME

        output_paths = dict(
            root=path,
            dev=str(dev_folder),
            config=str(config_folder),
            packages=str(packages_folder),
        )

        return output_paths

    def preference_roots_path(self) -> str:
        """Returns the path to the TP DCC preferences root file.

        Returns:
            The path to the TP DCC preferences root file.
        """

        project_package = self._resolver.project_package
        if not project_package:
            raise RuntimeError("Project config package not found.")

        return str(Path(project_package.root, "configs", "prefs", "roots.yaml"))

    def preference_roots_config(self) -> dict[str, str]:
        """Loads and returns the preference root file contents as a dictionary.

        Returns:
            A dictionary with the preference root file contents.
        """

        return cast(dict[str, Any], fileio.load_yaml(self.preference_roots_path()))

    def cache_folder_path(self) -> str:
        """Returns the current TP DCC bootstrap cache folder path.

        Returns:
            The current TP DCC bootstrap cache folder path.
        """

        cache_env = os.getenv(constants.CACHE_FOLDER_PATH_ENV_VAR)
        if cache_env is None:
            root_path = os.path.join(self.preference_roots_config()["user"], "cache")
            root_path = env.patch_windows_user_home(root_path)
            return root_path

        return os.path.expandvars(os.path.expanduser(cache_env))

    def descriptor_from_package_entry(
        self, package_entry: PackageEntry
    ) -> PackageDescriptor:
        """Creates a descriptor from the given package entry.

        Args:
            package_entry: The package entry to create the descriptor from.

        Returns:
            The created descriptor.
        """

        return PackageDescriptor(self, package_entry)

    def reload(self) -> PackagesManager:
        """Reloads the TP DCC packages manager.

        This method is used to reload the TP DCC packages manager when the
        environment changes.

        Returns:
            The reloaded TP DCC packages manager instance.
        """

        root = self._root_path
        self.shutdown()
        packages_manager = PackagesManager.from_path(root)
        packages_manager.resolver.resolve_from_environment_configuration_file_path(
            packages_manager.resolver.environment_config_file_path()
        )

        return packages_manager

    def shutdown(self):
        """Shuts down the TP DCC packages manager."""

        # Shutdown the host application.
        host = Host.current()
        if host is not None:
            host.shutdown()

        # Unload all packages.
        self._resolver.shutdown()

        # Reload TP DCC modules.
        flush.reload_tp(force=True)

        # Remove the current packages manager instance.
        PackagesManager.set_current(None)
