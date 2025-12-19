from __future__ import annotations


class PyforceError(Exception):
    """Base exception for the `pyforce` package."""


class UserNotFoundError(PyforceError):
    """Raised when a user is request but doesn't exist."""


class ChangeUnknownError(PyforceError):
    """Raised when a changelist is requested but doesn't exist."""


class ClientNotFoundError(PyforceError):
    """Raised when a client workspace is request but doesn't exist."""


class ConnectionExpiredError(PyforceError):
    """Raised when the connection to the Helix Core Server has expired.

    You need to log back in.
    """


class AuthenticationError(PyforceError):
    """Raised when login to the Helix Core Server failed."""


class CommandExecutionError(PyforceError):
    """Raised when an error occurred during the execution of a `p4` command.

    Args:
        message: Error message.
        command: The executed command.
        data: Optional marshaled output returned by the command.
    """

    def __init__(
        self,
        message: str,
        command: list[str],
        data: dict[str, str] | None = None,
    ) -> None:
        self.command = command
        self.data = data or {}
        super().__init__(message)


__all__ = [
    "PyforceError",
    "ConnectionExpiredError",
    "AuthenticationError",
    "ChangeUnknownError",
    "CommandExecutionError",
    "UserNotFoundError",
    "ClientNotFoundError",
]
