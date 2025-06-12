from __future__ import annotations

import typing
import logging
from typing import cast, Any
from abc import ABC, abstractmethod

from . import errors

if typing.TYPE_CHECKING:
    from .package import Package
    from .resolver import PackageEntry
    from .manager import PackagesManager

logger = logging.getLogger(__name__)


class Descriptor(ABC):
    """Abstract class that defines the interface for a descriptor."""

    REQUIRED_KEYS: set[str] = set()

    def __init__(self, packages_manager: PackagesManager, package_data: dict[str, Any]):
        """Initializes the descriptor.

        Args:
            packages_manager: The TP DCC Python pipeline packages manager.
            package_data: The package configuration.

        Raises:
            MissingPackageNameError: If the package name is missing.
            MissingPackageVersionError: If the package version is missing.
        """

        self._packages_manager = packages_manager
        self._package_data = package_data
        try:
            self._name = package_data["name"]
        except KeyError:
            raise errors.MissingPackageNameError(
                f"Missing package name in package data: {package_data}."
            )
        self._enabled = package_data.get("enabled", True)
        self._version = ""
        self._package: Package | None = None

        self._validate(package_data)

    def __repr__(self) -> str:
        """Returns a string representation of the descriptor."""

        return f"<{self.__class__.__name__}> Name: {self._name}"

    @property
    def name(self) -> str:
        """The name of the package descriptor."""

        return self._name

    @property
    def enabled(self) -> bool:
        """Whether the package descriptor is enabled or not."""

        return self._enabled

    @property
    def version(self) -> str:
        """The version of the package descriptor."""

        return self._version

    @property
    def package(self) -> Package | None:
        """The package associated with the descriptor."""

        return self._package

    @abstractmethod
    def resolve(self, *args: Any, **kwargs: Any) -> Package:
        """Resolves the descriptor.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            The resolved package.
        """

        raise NotImplementedError("Subclasses must implement this method.")

    def _validate(self, package_data: dict[str, Any]) -> bool:
        """Internal function that validates the given package data by checking that all
        the required keys are present.

        Args:
            package_data: The package configuration.

        Returns:
            True if the package data is valid, False otherwise.

        Raises:
            ValueError: If the package configuration is invalid.
        """

        missing_keys = self.REQUIRED_KEYS - package_data.keys()
        if missing_keys:
            raise errors.MissingPackageVersionError(
                f"Missing required keys in package data: {missing_keys}"
            )

        return True


class PackageDescriptor(Descriptor):
    """Class that represents a package descriptor."""

    REQUIRED_KEYS = {"name"}

    def __init__(self, packages_manager: PackagesManager, package_config: PackageEntry):
        """Initializes the TP DCC package descriptor.

        Args:
            packages_manager: The TP DCC Python pipeline packages manager.
            package_config: The package configuration.
        """

        super().__init__(packages_manager, cast(dict[str, Any], package_config))

        self._version = package_config.get("version", "")

    def resolve(self, *args: Any, **kwargs: Any) -> Package:
        """Resolves the descriptor.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            True if the package was resolved successfully, False otherwise.

        Raises:
            MissingPackageVersionError: If the package version is missing.
        """

        logger.debug(f"Resolving package descriptor: {self._name} - {self._version}")
        existing_package = self._packages_manager.resolver.package_for_descriptor(self)
        if not existing_package:
            raise errors.MissingPackageVersionError(
                f"Missing package: {self._name} - {self._version}"
            )

        self._package = existing_package

        return self._package
