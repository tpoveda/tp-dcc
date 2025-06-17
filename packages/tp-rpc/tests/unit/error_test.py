from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.core.errors import (
    RPCError,
    RPCConnectionError,
    AuthenticationError,
    AuthorizationError,
    FunctionNotFoundError,
    InvalidArgumentError,
    RemoteExecutionError,
    handle_rpc_errors,
)


def test_rpc_error_init():
    """Test RPCError initialization."""
    error = RPCError("Test message", {"detail_key": "detail_value"})

    assert error.message == "Test message"
    assert error.details == {"detail_key": "detail_value"}
    assert str(error) == "Test message"


def test_rpc_error_init_no_details():
    """Test RPCError initialization without details."""
    error = RPCError("Test message")

    assert error.message == "Test message"
    assert error.details == {}


def test_rpc_error_to_dict():
    """Test RPCError to_dict method."""
    error = RPCError("Test message", {"detail_key": "detail_value"})

    error_dict = error.to_dict()

    assert error_dict["error_code"] == "RPC_ERROR"
    assert error_dict["message"] == "Test message"
    assert error_dict["details"] == {"detail_key": "detail_value"}


def test_rpc_connection_error():
    """Test RPCConnectionError."""
    error = RPCConnectionError("Connection failed")

    assert error.ERROR_CODE == "CONNECTION_ERROR"
    assert error.HTTP_STATUS == 503
    assert error.message == "Connection failed"


def test_authentication_error():
    """Test AuthenticationError."""
    error = AuthenticationError("Authentication failed")

    assert error.ERROR_CODE == "AUTHENTICATION_ERROR"
    assert error.HTTP_STATUS == 401
    assert error.message == "Authentication failed"


def test_authorization_error():
    """Test AuthorizationError."""
    error = AuthorizationError("Authorization failed")

    assert error.ERROR_CODE == "AUTHORIZATION_ERROR"
    assert error.HTTP_STATUS == 403
    assert error.message == "Authorization failed"


def test_function_not_found_error():
    """Test FunctionNotFoundError."""
    error = FunctionNotFoundError("Function not found")

    assert error.ERROR_CODE == "FUNCTION_NOT_FOUND"
    assert error.HTTP_STATUS == 404
    assert error.message == "Function not found"


def test_invalid_argument_error():
    """Test InvalidArgumentError."""
    error = InvalidArgumentError("Invalid argument")

    assert error.ERROR_CODE == "INVALID_ARGUMENT"
    assert error.HTTP_STATUS == 400
    assert error.message == "Invalid argument"


def test_remote_execution_error():
    """Test RemoteExecutionError."""
    original_error = ValueError("Original error")
    error = RemoteExecutionError(
        "Execution failed",
        original_error=original_error,
        details={"function": "test_func"},
    )

    assert error.ERROR_CODE == "REMOTE_EXECUTION_ERROR"
    assert error.HTTP_STATUS == 500
    assert error.message == "Execution failed"
    assert error.original_error is original_error
    assert error.details == {"function": "test_func"}


def test_handle_rpc_errors_no_error():
    """Test handle_rpc_errors decorator with no error."""

    @handle_rpc_errors()
    def test_func():
        return "success"

    result = test_func()

    assert result == "success"


def test_handle_rpc_errors_with_rpc_error():
    """Test handle_rpc_errors decorator with an RPCError."""

    @handle_rpc_errors()
    def test_func():
        raise AuthenticationError("Auth failed")

    with pytest.raises(AuthenticationError) as excinfo:
        test_func()

    assert str(excinfo.value) == "Auth failed"


def test_handle_rpc_errors_with_mapped_error():
    """Test handle_rpc_errors decorator with a mapped error."""
    error_map = {
        ValueError: InvalidArgumentError,
        KeyError: FunctionNotFoundError,
    }

    @handle_rpc_errors(error_map)
    def test_func():
        raise ValueError("Invalid value")

    with pytest.raises(InvalidArgumentError) as excinfo:
        test_func()

    assert str(excinfo.value) == "Invalid value"


def test_handle_rpc_errors_with_unmapped_error():
    """Test handle_rpc_errors decorator with an unmapped error."""

    @handle_rpc_errors()
    def test_func():
        raise RuntimeError("Runtime error")

    with pytest.raises(RemoteExecutionError) as excinfo:
        test_func()

    assert "Error executing test_func: Runtime error" in str(excinfo.value)
    assert excinfo.value.details == {"function": "test_func"}
    assert isinstance(excinfo.value.original_error, RuntimeError)
