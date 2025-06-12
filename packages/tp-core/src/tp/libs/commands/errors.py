from __future__ import annotations


class UserCancelError(Exception):
    """Exception that is raised when the user cancels a command."""

    def __init__(self, message: str, errors: list[str] | None = None):
        """Args:
        message: Message to be displayed when the exception is raised.
        errors: Errors that caused the exception to be raised.
        """

        super().__init__(message)

        self._errors = errors

    @property
    def errors(self) -> list[str] | None:
        """The errors that caused the exception to be raised."""

        return self._errors


class CommandExecutionError(Exception):
    """Exception that is raised when a command execution fails."""

    def __init__(self, message: str, *args, **kwargs):
        """Args:
        message: Message to be displayed when the exception is raised.
        *args: Additional arguments to be passed to the exception.
        **kwargs: Additional keyword arguments to be passed to the exception.
        """

        super().__init__(message, *args, **kwargs)
