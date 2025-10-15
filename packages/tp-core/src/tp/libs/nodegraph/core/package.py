from __future__ import annotations

import os
import pkgutil
from pathlib import Path

from loguru import logger

from tp.libs.plugin import PluginsManager
from tp.libs.python.decorators import Singleton
from tp.preferences.interfaces import core as core_interface

from .node import Node


class Package:
    id: str = ""

    def __init__(self, package_path: str):
        super().__init__()

        self._path = package_path
        self._name = os.path.basename(package_path)

        self._nodes_manager = PluginsManager(
            interfaces=[Node],
            variable_name="type_name",
            name=f"tp.nodegraph.{self._name}.nodes",
        )

    @property
    def name(self) -> str:
        """The name of the package."""

        return self._name

    @property
    def path(self) -> str:
        """The path to the package."""

        return self._path

    @property
    def nodes_directory(self) -> str:
        """The path to the nodes directory within the package."""

        return os.path.join(self._path, "nodes")

    def analyze(self):
        self._nodes_manager.register_paths([self.nodes_directory])


class PackagesManager(metaclass=Singleton):
    ENV_VAR = "TP_NODEGRAPH_PACKAGE_PATHS"

    def __init__(self):
        super().__init__()

        self._prefs = core_interface.nodegraph_interface()

        self._packages: dict[str, Package] = {}
        self._package_paths: list[Path] = []

    def initialize(self, additional_package_locations: list[str] | None = None) -> None:
        """Initializes the packages manager, loading packages from default
        and additional locations.

        Args:
            additional_package_locations: Optional list of additional package
                locations to load from.
        """

        self._packages.clear()
        self._package_paths.clear()

        package_paths: list[str] = []
        package_paths_to_check = []
        package_paths_to_check.extend(additional_package_locations or [])
        package_paths_to_check.extend(self._prefs.user_package_paths())
        package_paths_to_check.extend(
            os.environ.get(self.ENV_VAR, "").split(os.pathsep)
        )
        for package_path in package_paths_to_check:
            path = Path(package_path).expanduser().resolve()
            if not path.exists():
                continue
            for sub_folder in path.iterdir():
                if sub_folder.is_dir():
                    if sub_folder.name == "__pycache__":
                        continue
                    package_paths.append(str(sub_folder))
        package_paths = list(set(package_paths))

        for package_path in package_paths:
            package = Package(package_path)
            package.analyze()
            self._packages[package.name] = package
            self._package_paths.append(Path(package_path))


# noinspection PyTypeChecker
manager: PackagesManager = PackagesManager()
