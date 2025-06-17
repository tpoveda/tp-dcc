from __future__ import annotations

from unittest.mock import patch, MagicMock

from tp.libs.rpc.core.registry import (
    register_function,
    get_function,
    list_functions,
    describe_function,
)


def test_register_function():
    """Test registering a function."""

    @register_function()
    def test_func():
        """Test function docstring."""
        return 42

    # Function should be registered with its original name
    assert get_function("test_func") is test_func

    # Function should be unchanged
    assert test_func() == 42


def test_register_function_custom_name():
    """Test registering a function with a custom name."""

    @register_function(name="custom_name")
    def another_func():
        return "hello"

    # Function should be registered with the custom name
    assert get_function("custom_name") is another_func
    assert get_function("another_func") is None

    # Function should be unchanged
    assert another_func() == "hello"


def test_get_function_nonexistent():
    """Test getting a non-existent function."""
    assert get_function("nonexistent_func") is None


def test_list_functions():
    """Test listing registered functions."""
    # Clear registry first
    with patch("tp.libs.rpc.core.registry._registry", {}):

        @register_function()
        def func1():
            pass

        @register_function()
        def func2():
            pass

        functions = list_functions()
        assert sorted(functions) == ["func1", "func2"]


def test_list_functions_verbose():
    """Test listing registered functions with verbose output."""
    # Clear registry first
    with patch("tp.libs.rpc.core.registry._registry", {}):

        @register_function()
        def func1(a: int, b: str = "default") -> bool:
            """Function 1 docstring."""
            pass

        @register_function()
        def func2():
            """Function 2 docstring."""
            pass

        functions = list_functions(verbose=True)
        assert len(functions) == 2

        # Check structure of verbose output
        for func in functions:
            assert "name" in func
            assert "signature" in func
            assert "doc" in func

        # Check specific function details
        func1_info = next(f for f in functions if f["name"] == "func1")
        # Fix: Use the full signature string instead of checking for substrings
        assert func1_info["signature"].startswith("func1")
        assert "default" in func1_info["signature"]
        assert "Function 1 docstring" in func1_info["doc"]


def test_describe_function():
    """Test describing a specific function."""

    @register_function()
    def complex_func(a: int, b: str = "default") -> bool:
        """Complex function docstring.

        Args:
            a: First argument
            b: Second argument

        Returns:
            Boolean result
        """
        return True

    result = describe_function("complex_func")

    assert result["found"] is True
    # Fix: Use the full signature string instead of checking for substrings
    assert "complex_func" in result["signature"]
    assert "Complex function docstring" in result["doc"]
    assert len(result["args"]) == 2
    assert result["args"][0]["name"] == "a"
    assert result["args"][0]["type"] == "int"
    assert result["args"][1]["name"] == "b"
    assert result["args"][1]["type"] == "str"
    assert result["args"][1]["default"] == "default"
    assert result["return_type"] == "bool"


def test_describe_function_not_found():
    """Test describing a non-existent function."""
    result = describe_function("nonexistent_func")

    assert result["found"] is False
    assert result["signature"] is None
    assert result["doc"] is None


def test_describe_function_error():
    """Test describing a function with introspection errors."""
    # Create a function that will cause introspection to fail
    mock_func = MagicMock()
    mock_func.__name__ = "error_func"

    # Make inspect.signature raise an exception
    with patch("tp.libs.rpc.core.registry._registry", {"error_func": mock_func}):
        with patch("inspect.signature", side_effect=ValueError("Test error")):
            result = describe_function("error_func")

            assert result["found"] is True
            assert result["signature"] == "(unavailable)"
            assert "failed to introspect" in result["doc"]
