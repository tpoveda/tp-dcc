from __future__ import annotations

import inspect
from unittest.mock import patch, MagicMock

import pytest

from tp.libs.rpc.core.di import DependencyContainer, get_container, inject


class TestInterface:
    pass


class TestImplementation(TestInterface):
    def __init__(self, value=None):
        self.value = value


def test_dependency_container_init():
    """Test DependencyContainer initialization."""
    container = DependencyContainer()

    assert isinstance(container._services, dict)
    assert len(container._services) == 0
    assert isinstance(container._factories, dict)
    assert len(container._factories) == 0


def test_register_service():
    """Test registering a service."""
    container = DependencyContainer()
    implementation = TestImplementation()

    container.register(TestInterface, implementation)

    # Should store the implementation under the interface's type name
    type_name = f"{TestInterface.__module__}.{TestInterface.__name__}"
    assert container._services[type_name] is implementation


def test_register_factory():
    """Test registering a factory."""
    container = DependencyContainer()
    factory = lambda: TestImplementation("factory_value")

    container.register_factory(TestInterface, factory)

    # Should store the factory under the interface's type name
    type_name = f"{TestInterface.__module__}.{TestInterface.__name__}"
    assert container._factories[type_name] is factory


def test_resolve_service():
    """Test resolving a registered service."""
    container = DependencyContainer()
    implementation = TestImplementation()

    container.register(TestInterface, implementation)

    resolved = container.resolve(TestInterface)

    assert resolved is implementation


def test_resolve_factory():
    """Test resolving a service from a factory."""
    container = DependencyContainer()
    factory = lambda: TestImplementation("factory_value")

    container.register_factory(TestInterface, factory)

    # First resolution should call the factory
    resolved1 = container.resolve(TestInterface)

    assert isinstance(resolved1, TestImplementation)
    assert resolved1.value == "factory_value"

    # Second resolution should return the cached instance
    resolved2 = container.resolve(TestInterface)

    assert resolved2 is resolved1


def test_resolve_not_registered():
    """Test resolving a service that is not registered."""
    container = DependencyContainer()

    with pytest.raises(KeyError, match="No implementation registered for"):
        container.resolve(TestInterface)


def test_get_type_name():
    """Test getting a type name."""
    container = DependencyContainer()

    # Test with a class
    type_name = container._get_type_name(TestInterface)
    assert type_name == f"{TestInterface.__module__}.{TestInterface.__name__}"

    # Test with an object that doesn't have __module__ and __name__
    class NoModuleNameType:
        pass

    # Remove __module__ and __name__
    no_module_name_type = type("NoModuleNameType", (), {})
    delattr(no_module_name_type, "__module__")

    type_name = container._get_type_name(no_module_name_type)
    assert isinstance(type_name, str)


def test_get_container():
    """Test the get_container function."""
    # Should return the singleton instance
    container1 = get_container()
    container2 = get_container()

    assert container1 is container2
    assert isinstance(container1, DependencyContainer)


def test_inject_decorator():
    """Test the inject decorator."""
    # Create a test container and register a service
    container = DependencyContainer()
    implementation = TestImplementation("test_value")
    container.register(TestInterface, implementation)

    # Mock get_container to return our test container
    with patch("tp.libs.rpc.core.di.get_container", return_value=container):
        # Define a function that uses the inject decorator
        @inject(TestInterface)
        def test_function(interface: TestInterface):
            return interface.value

        # Call the function without providing the dependency
        result = test_function()

        # Should have injected the dependency
        assert result == "test_value"

        # Call the function with an explicit dependency
        explicit_impl = TestImplementation("explicit_value")
        result = test_function(interface=explicit_impl)

        # Should use the provided dependency
        assert result == "explicit_value"


def test_inject_with_multiple_dependencies():
    """Test inject with multiple dependencies."""
    # Create a test container and register services
    container = DependencyContainer()

    class Service1:
        value = "service1"

    class Service2:
        value = "service2"

    container.register(Service1, Service1())
    container.register(Service2, Service2())

    # Mock get_container to return our test container
    with patch("tp.libs.rpc.core.di.get_container", return_value=container):
        # Define a function that uses the inject decorator with multiple dependencies
        @inject(Service1, Service2)
        def test_function(service1: Service1, service2: Service2):
            return f"{service1.value}_{service2.value}"

        # Call the function without providing dependencies
        result = test_function()

        # Should have injected both dependencies
        assert result == "service1_service2"

        # Call with one explicit dependency
        explicit_service1 = Service1()
        explicit_service1.value = "explicit1"

        result = test_function(service1=explicit_service1)

        # Should use the provided dependency and inject the other
        assert result == "explicit1_service2"
