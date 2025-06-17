from __future__ import annotations

import os
import re
import hmac
import hashlib
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.core.security import (
    env_control_enabled,
    remote_control_enabled,
    encryption_enabled,
    get_shared_secret,
    generate_auth_token,
    verify_auth_token,
    register_function_acl,
    check_function_access,
    require_auth,
    validate_input,
)


def test_env_control_enabled():
    # Test when enabled
    with patch.dict(os.environ, {"TP_DCC_RPC_ALLOW_ENV_CONTROL": "1"}):
        assert env_control_enabled() is True

    # Test when disabled
    with patch.dict(os.environ, {"TP_DCC_RPC_ALLOW_ENV_CONTROL": "0"}):
        assert env_control_enabled() is False

    # Test default value
    with patch.dict(os.environ, {}, clear=True):
        assert env_control_enabled() is True


def test_remote_control_enabled():
    # Test when enabled
    with patch.dict(os.environ, {"TP_DCC_RPC_ALLOW_REMOTE_CONTROL": "1"}):
        assert remote_control_enabled() is True

    # Test when disabled
    with patch.dict(os.environ, {"TP_DCC_RPC_ALLOW_REMOTE_CONTROL": "0"}):
        assert remote_control_enabled() is False

    # Test default value
    with patch.dict(os.environ, {}, clear=True):
        assert remote_control_enabled() is True


def test_encryption_enabled():
    # Test when enabled
    with patch.dict(os.environ, {"TP_DCC_RPC_ENABLE_ENCRYPTION": "1"}):
        assert encryption_enabled() is True

    # Test when disabled
    with patch.dict(os.environ, {"TP_DCC_RPC_ENABLE_ENCRYPTION": "0"}):
        assert encryption_enabled() is False

    # Test default value
    with patch.dict(os.environ, {}, clear=True):
        assert encryption_enabled() is False


def test_get_shared_secret():
    # Test with custom secret
    with patch.dict(os.environ, {"TP_DCC_RPC_SECRET": "custom-secret"}):
        assert get_shared_secret() == "custom-secret"

    # Test default value
    with patch.dict(os.environ, {}, clear=True):
        assert get_shared_secret() == "default-secret-change-me-in-production"


def test_generate_auth_token():
    # Test token generation
    with patch(
        "tp.libs.rpc.core.security.get_shared_secret", return_value="test-secret"
    ):
        token = generate_auth_token("test-message")

        # Verify the token is a hex string
        assert all(c in "0123456789abcdef" for c in token)

        # Verify the token is generated correctly
        expected = hmac.new(
            b"test-secret", b"test-message", hashlib.sha256
        ).hexdigest()
        assert token == expected


def test_verify_auth_token():
    # Test valid token
    with patch(
        "tp.libs.rpc.core.security.generate_auth_token", return_value="valid-token"
    ):
        assert verify_auth_token("test-message", "valid-token") is True

    # Test invalid token
    with patch(
        "tp.libs.rpc.core.security.generate_auth_token", return_value="valid-token"
    ):
        assert verify_auth_token("test-message", "invalid-token") is False


def test_register_function_acl():
    # Clear the ACL dictionary before testing
    from tp.libs.rpc.core.security import _function_acl

    _function_acl.clear()

    # Register ACL for a function
    register_function_acl("test_func", ["client1", "client2"])

    # Verify the ACL was registered
    assert _function_acl["test_func"] == ["client1", "client2"]


def test_check_function_access():
    # Clear the ACL dictionary before testing
    from tp.libs.rpc.core.security import _function_acl

    _function_acl.clear()

    # Register ACL for a function
    register_function_acl("test_func", ["client1", "client.*"])

    # Test access for allowed clients
    assert check_function_access("test_func", "client1") is True
    assert check_function_access("test_func", "client2") is True

    # Test access for disallowed clients
    assert check_function_access("test_func", "other") is False

    # Test access for function without ACL
    assert check_function_access("other_func", "any_client") is True


def test_require_auth_decorator():
    # Test function with the decorator
    @require_auth
    def test_func(a, b):
        return a + b

    # Test when auth is not required
    with patch.dict(os.environ, {"TP_DCC_RPC_REQUIRE_AUTH": "0"}):
        assert test_func(1, 2) == 3

    # Test when auth is required but no token provided
    with patch.dict(os.environ, {"TP_DCC_RPC_REQUIRE_AUTH": "1"}):
        with pytest.raises(PermissionError, match="Authentication required"):
            test_func(1, 2)

    # Test with valid token
    with patch("tp.libs.rpc.core.security.verify_auth_token", return_value=True):
        assert test_func(1, 2, _auth_token="valid-token") == 3

    # Test with invalid token
    with patch("tp.libs.rpc.core.security.verify_auth_token", return_value=False):
        with pytest.raises(
            PermissionError, match="Invalid authentication token"
        ):
            test_func(1, 2, _auth_token="invalid-token")


def test_validate_input_decorator():
    # Define validators
    def is_positive(value):
        return isinstance(value, int) and value > 0

    def is_string_with_length(value):
        return isinstance(value, str) and len(value) > 0

    # Test function with the decorator
    @validate_input({"a": is_positive, "b": is_string_with_length})
    def test_func(a, b):
        return f"{a}-{b}"

    # Test with valid inputs
    assert test_func(1, "test") == "1-test"

    # Test with invalid first parameter
    with pytest.raises(ValueError, match="Invalid value for parameter 'a'"):
        test_func(-1, "test")

    # Test with invalid second parameter
    with pytest.raises(ValueError, match="Invalid value for parameter 'b'"):
        test_func(1, "")

    # Test with validator that raises an exception
    def validator_with_error(value):
        raise ValueError("Custom error")

    @validate_input({"a": validator_with_error})
    def another_func(a):
        return a

    with pytest.raises(
        ValueError, match="Validation error for 'a': Custom error"
    ):
        another_func(1)
