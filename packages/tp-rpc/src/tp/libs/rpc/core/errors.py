from __future__ import annotations

from typing import Any


class RPCError(Exception):
    """Base exception class for all RPC-related errors."""

    ERROR_CODE = "RPC_ERROR"
    HTTP_STATUS = 500

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            details: Additional error details.
        """

        self.message = message
        self.details = details or {}

        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert the exception to a dictionary representation.

        Returns:
            Dictionary with error information.
        """

        return {
            "error_code": self.ERROR_CODE,
            "message": self.message,
            "details": self.details,
        }


class RPCConnectionError(RPCError):
    """Raised when there's an error connecting to a remote service."""

    ERROR_CODE = "CONNECTION_ERROR"
    HTTP_STATUS = 503


class AuthenticationError(RPCError):
    """Raised when authentication fails."""

    ERROR_CODE = "AUTHENTICATION_ERROR"
    HTTP_STATUS = 401


class AuthorizationError(RPCError):
    """Raised when a user doesn't have permission to perform an action."""

    ERROR_CODE = "AUTHORIZATION_ERROR"
    HTTP_STATUS = 403


class FunctionNotFoundError(RPCError):
    """Raised when a requested function doesn't exist."""

    ERROR_CODE = "FUNCTION_NOT_FOUND"
    HTTP_STATUS = 404


class InvalidArgumentError(RPCError):
    """Raised when invalid arguments are provided to a function."""

    ERROR_CODE = "INVALID_ARGUMENT"
    HTTP_STATUS = 400


class RemoteExecutionError(RPCError):
    """Raised when an error occurs during remote execution."""

    ERROR_CODE = "REMOTE_EXECUTION_ERROR"
    HTTP_STATUS = 500

    def __init__(
        self,
        message: str,
        original_error: Exception | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            original_error: The original exception that was raised.
            details: Additional error details.
        """

        super().__init__(message, details)
        self.original_error = original_error


# Error handler decorator
def handle_rpc_errors(
    error_map: dict[type[Exception], type[RPCError]] | None = None,
):
    """Decorator to standardize error handling in RPC functions.

    Args:
        error_map: Mapping of exception types to RPC error types.

    Returns:
        Decorated function with standardized error handling.
    """

    error_map = error_map or {}

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RPCError:
                # Already a standardized error, re-raise
                raise
            except Exception as e:
                # Map to a standardized error if possible
                error_type = type(e)
                if error_type in error_map:
                    raise error_map[error_type](str(e), original_error=e)
                # Default to RemoteExecutionError
                raise RemoteExecutionError(
                    f"Error executing {func.__name__}: {str(e)}",
                    original_error=e,
                    details={"function": func.__name__},
                )

        return wrapper

    return decorator
