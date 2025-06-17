from __future__ import annotations

import inspect
from typing import TypeVar, Any
from collections.abc import Callable

T = TypeVar("T")


class DependencyContainer:
    """A simple dependency injection container."""

    def __init__(self):
        """Initialize the dependency container."""

        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable[..., Any]] = {}

    def register(self, interface: type[T], implementation: T) -> None:
        """Register a service implementation.

        Args:
            interface: The interface or type to register.
            implementation: The implementation instance.
        """

        self._services[self._get_type_name(interface)] = implementation

    def register_factory(self, interface: type[T], factory: Callable[..., T]) -> None:
        """Register a factory function for creating service instances.

        Args:
            interface: The interface or type to register.
            factory: Factory function that creates instances.
        """

        self._factories[self._get_type_name(interface)] = factory

    def resolve(self, interface: type[T]) -> T:
        """Resolve a service implementation.

        Args:
            interface: The interface or type to resolve.

        Returns:
            The implementation instance.

        Raises:
            KeyError: If the interface is not registered.
        """

        type_name = self._get_type_name(interface)

        # Check if we have a direct service instance.
        if type_name in self._services:
            return self._services[type_name]

        # Check if we have a factory.
        if type_name in self._factories:
            # Create the instance and cache it.
            instance = self._factories[type_name]()
            self._services[type_name] = instance
            return instance

        raise KeyError(f"No implementation registered for {type_name}")

    def _get_type_name(self, type_obj: type) -> str:
        """Get a unique name for a type.

        Args:
            type_obj: The type object.

        Returns:
            A unique string identifier.
        """

        if hasattr(type_obj, "__module__") and hasattr(type_obj, "__name__"):
            return f"{type_obj.__module__}.{type_obj.__name__}"
        return str(type_obj)


# Global container instance.
_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """Get the global dependency container.

    Returns:
        The dependency container instance.
    """
    return _container


def inject(*dependencies: type) -> Callable:
    """Decorator to inject dependencies into a function or method.

    Args:
        *dependencies: Types to inject.

    Returns:
        Decorated function with dependencies injected.
    """

    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)

        def wrapper(*args, **kwargs):
            # Create a mapping of parameter names to their values
            bound_args = sig.bind_partial(*args, **kwargs)

            # For each parameter that wasn't provided, try to inject it
            for param_name, param in sig.parameters.items():
                if param_name not in bound_args.arguments:
                    # Find the corresponding dependency type
                    for dep_type in dependencies:
                        if param.annotation == dep_type:
                            # Resolve the dependency and add it to kwargs
                            kwargs[param_name] = get_container().resolve(dep_type)
                            break

            return func(*args, **kwargs)

        return wrapper

    return decorator
