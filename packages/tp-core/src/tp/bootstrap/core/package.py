from __future__ import annotations

import os
import sys
import copy
import platform
from typing import cast, Any
from pathlib import Path

from loguru import logger
from packaging.version import parse as parse_version, Version

from tp.libs.python import osplatform

from .variable import Variable
from .dependency import Dependency
from ..utils import fileio, dcc, modules


class Package:
    """Class that represents a TP DCC package.
    This class is responsible for loading the package YAML file, resolving
    the package environment, and executing startup and shutdown commands.
    It also provides methods to access package metadata such as name, version,
    dependencies, and documentation.
    """

    def __init__(self, package_file_path: str | None = None):
        """Initializes the package.

        Args:
            package_file_path: The path to the package YAML file.
        """

        self._path = package_file_path or ""
        self._root = str(Path(package_file_path).parent) if package_file_path else ""
        self._environ: dict[str, list[str]] = {}
        self._name = ""
        self._display_name = ""
        self._description = ""
        self._author = ""
        self._author_email = ""
        self._enabled = True
        self._required = False
        self._version = Version("0.0.0")
        self._tokens: dict[str, str] = {}
        self._tests: list[str] = []
        self._documentation: dict[str, str] = {}
        self._command_paths: list[str] = []
        self._dependencies: list[Dependency] = []
        self._cache: dict[str, str] = {}
        self._resolved = False
        self._resolved_env: dict[str, Variable] = {}

        if package_file_path is not None and os.path.exists(package_file_path):
            self._process_package_file(package_file_path)

    def __repr__(self) -> str:
        """Returns a string representation of the package."""

        return self.search_str()

    @staticmethod
    def name_for_package_name_and_version(
        package_name: str, package_version: str
    ) -> str:
        """Generates the package name for the given package name and version.

        Args:
            package_name: The name of the package.
            package_version: The version of the package.

        Returns:
            The generated package name.
        """

        return "-".join((package_name, package_version))

    @property
    def root(self) -> str:
        """The root path of the package."""

        return self._root

    @property
    def name(self) -> str:
        """The name of the package."""

        return self._name

    @property
    def display_name(self) -> str:
        """The display name of the package."""

        return self._display_name

    @property
    def description(self) -> str:
        """The description of the package."""

        return self._description

    @property
    def author(self) -> str:
        """The author of the package."""

        return self._author

    @property
    def author_email(self) -> str:
        """The author email of the package."""

        return self._author_email

    @property
    def enabled(self) -> bool:
        """Whether the package is enabled or not."""

        return self._enabled

    @property
    def required(self) -> bool:
        """Whether the package is required or not."""

        return self._required

    @property
    def version(self) -> Version:
        """The version of the package."""

        return self._version

    @version.setter
    def version(self, value: str):
        """Sets the version of the package."""

        self._version = parse_version(value)
        self._cache["version"] = str(self._version)

    @property
    def dependencies(self) -> list[Dependency]:
        """The dependencies of the package."""

        return self._dependencies

    @property
    def resolved(self) -> bool:
        """Whether the package is resolved or not."""

        return self._resolved

    def search_str(self) -> str:
        """Returns the search string for the package.

        Returns:
            The search string for the package.
        """

        return "-".join((self._name, str(self._version)))

    def exists(self) -> bool:
        """Checks if the package exists.

        Returns:
            True if the package exists, False otherwise.
        """

        return Path(self._path).exists()

    def set_package_file_path(self, package_file_path: str):
        """Sets the package internal file path variables.

        Args:
            package_file_path: The path to the package YAML file.
        """

        self._path = str(Path(package_file_path))
        self._root = str(Path(package_file_path).parent)

    def resolve(self, apply_environment: bool = True):
        """Resolves the package.

        Args:
            apply_environment: Whether to apply the environment.
        """

        environ = self._environ
        if not environ:
            logger.warning(f"Unable to resolve package environment: {self._path}")
            self._resolved = False
            return

        package_variables: dict[str, Variable] = {}
        for key, paths in environ.items():
            if not paths:
                continue
            var = (
                Variable(key, [paths])
                if isinstance(paths, str)
                else Variable(key, paths)
            )
            var.solve(self._tokens)
            if apply_environment:
                osplatform.add_paths_to_env(key, var.values)
            package_variables[key] = var

        # Update system path with PYTHONPATH variables.
        if apply_environment and "PYTHONPATH" in package_variables:
            for i in package_variables["PYTHONPATH"].values:
                i = os.path.abspath(i)
                if i not in sys.path:
                    sys.path.append(i)

        logger.debug(f"Resolved: {self._name} | {self._root}")
        self._resolved_env = package_variables
        self._resolved = True

    def startup(self):
        """Starts up the package by executing the startup command.

        Note:
            More specifically, it runs the startup function from each of the
            command scripts defined in the package's command paths.
        """

        logger.info(f"Starting up package: {self._name}")
        self._run_commands("startup")

    def shutdown(self):
        """Shuts down the package by executing the shutdown command.

        Note:
            More specifically, it runs the shutdown function from each of the
            command scripts defined in the package's command paths.
        """

        logger.info(f"Shutting down package: {self._name}")
        self._run_commands("shutdown")

    def _process_package_file(self, package_file_path: str):
        """Internal function that processes the package file.

        Args:
            package_file_path: The path to the package YAML file.
        """

        self.set_package_file_path(package_file_path)
        try:
            data = fileio.load_yaml(package_file_path)
        except ValueError:
            logger.error(
                f"Failed to load TP DCC package YAML file: {package_file_path}",
                exc_info=True,
            )
            data = {}

        self._process_data(cast(dict[str, Any], data))

    def _process_data(self, data: dict[str, Any]):
        """Internal function that fills package internal variables based on
        the data contained in the given dictionary loaded from the package
        YAML file.

        Args:
            data: The dictionary containing the package data.
        """

        self._environ = data.get("environment", {})
        self._cache = copy.deepcopy(data)
        self._version = parse_version(data.get("version", "0.0.0"))
        self._name = data.get("name", "No_Name")
        self._display_name = data.get("displayName", "No Name")
        self._description = data.get("description", "No description")
        self._author = data.get("author", "")
        self._author_email = data.get("authorEmail", "")
        self._documentation = data.get("documentation", {})
        self._dependencies = list(
            map(Dependency.from_string, data.get("dependencies", []))
        )
        self._tokens = {
            "self": self._root,
            "self.name": self._name,
            "self.path": self._root,
            "self.version": str(self._version),
            "platform.system": platform.system().lower(),
            "platform.arch": platform.machine(),
            "dcc": dcc.current_dcc(),
        }
        self._tests = Variable("tests", data.get("tests", [])).solve(self._tokens)
        self._command_paths = Variable("commands", data.get("commands", [])).solve(
            self._tokens
        )

    def _run_commands(self, command_name: str):
        """Internal function that executes a command function from a list of
        module file paths.

        For each file path in `self._command_paths`, this method attempts to
        import and execute the specified command function.

        Args:
            command_name: Name of the function to execute inside each module.
        """

        for command_path in self._command_paths:
            path = Path(command_path)
            if not path.is_file():
                logger.warning(f"Command path is not a file: {path}")
                continue

            try:
                file_path = path.resolve(strict=True)
            except OSError as err:
                logger.warning(f"Failed to resolve path {path}: {err}")
                continue

            logger.debug(f"Importing package {command_name} from file: {path}")

            modules.run_script_function(
                str(file_path),
                command_name,
                f"Running {command_name} function for Module: {path}",
                self,
            )
