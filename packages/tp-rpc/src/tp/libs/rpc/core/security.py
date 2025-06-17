from __future__ import annotations

import os
import re
import hmac
import hashlib
from typing import Any
from functools import wraps
from collections.abc import Callable


def env_control_enabled() -> bool:
    """Check if environment variable control is allowed.

    Returns:
        True if TP_DCC_RPC_ALLOW_ENV_CONTROL is "1".
    """

    return os.environ.get("TP_DCC_RPC_ALLOW_ENV_CONTROL", "1") == "1"


def remote_control_enabled() -> bool:
    """Check if remote control operations like shutdown, kill, or dynamic
    registration are allowed.

    Returns:
        True if TP_DCC_RPC_ALLOW_REMOTE_CONTROL is "1".
    """

    return os.environ.get("TP_DCC_RPC_ALLOW_REMOTE_CONTROL", "1") == "1"


def encryption_enabled() -> bool:
    """Check if encryption is enabled for RPC communications.

    Returns:
        True if TP_DCC_RPC_ENABLE_ENCRYPTION is "1".
    """

    return os.environ.get("TP_DCC_RPC_ENABLE_ENCRYPTION", "0") == "1"


def get_shared_secret() -> str:
    """Get the shared secret for authentication.

    If TP_DCC_RPC_SECRET is not set, a default value is used.
    In production, always set TP_DCC_RPC_SECRET to a strong random value.

    Returns:
        The shared secret string.
    """

    return os.environ.get("TP_DCC_RPC_SECRET", "default-secret-change-me-in-production")


def generate_auth_token(message: str) -> str:
    """Generate an HMAC authentication token for a message.

    Args:
        message: The message to authenticate.

    Returns:
        Hex-encoded HMAC token.
    """

    secret = get_shared_secret().encode("utf-8")
    return hmac.new(secret, message.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_auth_token(message: str, token: str) -> bool:
    """Verify an HMAC authentication token.

    Args:
        message: The original message.
        token: The token to verify.

    Returns:
        True if the token is valid.
    """

    expected = generate_auth_token(message)
    return hmac.compare_digest(expected, token)


_function_acl: dict[str, list[str]] = {}


def register_function_acl(function_name: str, allowed_clients: list[str]):
    """Register access control for a function.

    Args:
        function_name: Name of the function.
        allowed_clients: List of client patterns (regex) allowed to call
            this function.
    """

    _function_acl[function_name] = allowed_clients


def check_function_access(function_name: str, client_id: str) -> bool:
    """Check if a client is allowed to call a function.

    Args:
        function_name: Name of the function.
        client_id: Client identifier (e.g., "maya-1").

    Returns:
        True if access is allowed.
    """

    # If no ACL is defined for this function, allow access.
    if function_name not in _function_acl:
        return True

    # Check if the client matches any allowed pattern.
    for pattern in _function_acl[function_name]:
        if re.match(pattern, client_id):
            return True

    return False


def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication for a function.

    Args:
        func: The function to protect.

    Returns:
        Decorated function that checks authentication.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract auth token from kwargs.
        auth_token = kwargs.pop("_auth_token", None)

        # Get the function name for the message.
        function_name = func.__name__

        # If no token is provided, check if auth is required.
        if auth_token is None:
            if os.environ.get("TP_DCC_RPC_REQUIRE_AUTH", "0") == "1":
                raise PermissionError("Authentication required")
            return func(*args, **kwargs)

        # Verify the token.
        if not verify_auth_token(function_name, auth_token):
            raise PermissionError("Invalid authentication token")

        return func(*args, **kwargs)

    return wrapper


def validate_input(schema: dict[str, Any]) -> Callable:
    """Decorator to validate function inputs against a schema.

    Args:
        schema: Dictionary mapping parameter names to validation functions.

    Returns:
        Decorated function with input validation.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each parameter
            for param_name, param_value in bound_args.arguments.items():
                if param_name in schema:
                    validator = schema[param_name]
                    try:
                        if not validator(param_value):
                            raise ValueError(
                                f"Invalid value for parameter '{param_name}'"
                            )
                    except Exception as e:
                        raise ValueError(f"Validation error for '{param_name}': {e}")

            return func(*args, **kwargs)

        return wrapper

    return decorator
