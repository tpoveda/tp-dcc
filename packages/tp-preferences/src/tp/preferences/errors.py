from __future__ import annotations


class RootAlreadyExistsError(Exception):
    """Exception raised when the root of the preferences already exists."""


class RootDoesNotExistError(Exception):
    """Exception raised when the root of the preferences does not exist."""


class InvalidSettingsPathError(Exception):
    """Exception raised when the settings path is invalid."""


class SettingsNameDoesntExistError(Exception):
    """Exception raised when the settings name does not exist."""

    pass
