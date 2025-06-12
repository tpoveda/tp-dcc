from __future__ import annotations

from typing import Any


class Ignore:
    """This class can be used as a return item when you specifically do not
    want the value of a function to contribute a bound result, so the method
    result is ignored during the composition process.

    Use this as a return value from any composited method when you explicitly
    want to exclude that method's result from the final composed result.
    """

    pass


class Composition:
    """Base class for creating composite objects that can bind other objects
    and delegate method calls to them using decorated composition strategies.

    Subclasses can define methods decorated with composition decorators to
    control how results from multiple bound components are combined.

    Attributes:
        _components: The list of objects bound to this composite instance.

    Example:
        class A(Composition):
            @extend_results
            def items(self):
                return ['a', 'b']

        class B:
            def items(self):
                return ['x', 'y']

        a = A()
        a.bind(B())
        print(a.items())  # ['a', 'b', 'x', 'y']
    """

    def __init__(self):
        """Initializes the Composition class."""

        super().__init__()

        self._components: list[Any] = []

    def __repr__(self) -> str:
        """Returns a string representation of the class name and its
        components.

        Returns:
            A string representation of the class name and its components.
        """

        if not self._components:
            return self.__class__.__name__

        components = "; ".join(
            [
                component.__class__.__name__
                for component in self._components
                if component != self
            ]
        )
        return f"[{self.__class__.__name__} ({components})]"

    def __getattr__(self, name: str) -> Any:
        """Returns the attribute of the first component that has it.

        Delegate attribute access to bound components if the attribute is not
        found on the base object.

        Args:
            name: The name of the attribute to get.

        Returns:
            The value of the attribute from the first component that has it.

        Raises:
            AttributeError: If the attribute is not found in any component.
        """

        for component in self._components:
            if hasattr(component, name):
                return getattr(component, name)

        raise AttributeError(f"{self.__class__.__name__!r} has no attribute {name!r}")

    def __setattr__(self, name: str, value: Any):
        """Sets the attribute of the first component that has it.

        Delegate attribute assignment to components if possible.

        If the attribute is not found in any component, the attribute is set
        on the `Composition` instance itself (default Python behavior).

        Args:
            name: The name of the attribute to set.
            value: The value to set the attribute to.

        Raises:
            AttributeError: If the attribute is not found in any component.
        """

        if name.startswith("_") or name in self.__dict__:
            object.__setattr__(self, name, value)
            return

        for component in self._components:
            if hasattr(component, name):
                setattr(component, name, value)
                return

        object.__setattr__(self, name, value)

    @property
    def components(self) -> list[Any]:
        """The list of bound components."""

        return self._components.copy()

    def bind(self, component: Any) -> None:
        """Adds a new component to this composite object.

        Args:
            component: The object to bind.

        Raises:
            ValueError: If attempting to bind self to itself.
        """

        if component is self:
            raise ValueError("Cannot bind self to self.")

        self._components.append(component)

    def unbind(self, component_or_type: Any) -> bool:
        """Remove a component or type of component.

        Args:
            component_or_type: The instance or type of component to remove.

        Returns:
            True if a component was removed, False otherwise.
        """

        for component in list(self._components):
            if component == component_or_type or isinstance(
                component, component_or_type
            ):
                self._components.remove(component)
                return True

        return False
