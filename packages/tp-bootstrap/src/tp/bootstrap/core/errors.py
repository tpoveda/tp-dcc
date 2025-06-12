from __future__ import annotations


class MissingPackageVersionError(Exception):
    """Raised when the requested package version does not exist."""


class MissingEnvironmentConfigFilePathError(Exception):
    """Raised when the environment configuration file is not found."""


class DescriptorMissingKeysError(Exception):
    """Raised when the descriptor is missing required keys."""


class MissingPackageNameError(Exception):
    """Raised when the package name is missing in the descriptor."""


class MissingProjectPackageNameError(Exception):
    """Raised when the project package name is missing in the descriptor."""


class MissingProjectPackageError(Exception):
    """Raised when the project package is missing in the descriptor."""
