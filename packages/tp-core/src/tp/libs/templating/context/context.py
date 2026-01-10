"""Hierarchical template context with inheritance."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tp.libs.templating.config.loader import TemplateConfiguration
    from tp.libs.templating.naming.convention import NamingConvention
    from tp.libs.templating.paths.resolver import PathResolver


class TemplateContext:
    """Hierarchical context for template resolution.

    Provides a context hierarchy where child contexts can override
    values from parent contexts. Useful for project/shot/asset level
    configurations.

    Example:
        >>> # Create project-level context
        >>> project_ctx = TemplateContext(name="project")
        >>> project_ctx.set("project", "MyGame")
        >>> project_ctx.set("root", "/content")
        >>>
        >>> # Create shot-level context with overrides
        >>> shot_ctx = project_ctx.with_override(
        ...     name="shot_010",
        ...     shot="010",
        ...     episode="ep01"
        ... )
        >>>
        >>> # Values inherit from parent
        >>> print(shot_ctx.get("project"))  # "MyGame"
        >>> print(shot_ctx.get("shot"))     # "010"
        >>>
        >>> # Resolve using context
        >>> path = shot_ctx.resolve_path("shot_output", frame=100)
    """

    def __init__(
        self,
        name: str = "default",
        parent: TemplateContext | None = None,
        configuration: TemplateConfiguration | None = None,
    ):
        """TemplateContext constructor.

        Args:
            name: Context name for identification.
            parent: Parent context to inherit from.
            configuration: Optional TemplateConfiguration for this context.
        """

        self._name = name
        self._parent = parent
        self._configuration = configuration
        self._values: dict[str, Any] = {}
        self._naming_convention: NamingConvention | None = None
        self._path_resolver: PathResolver | None = None

    @property
    def name(self) -> str:
        """Returns the context name."""
        return self._name

    @property
    def parent(self) -> TemplateContext | None:
        """Returns the parent context."""
        return self._parent

    @property
    def configuration(self) -> TemplateConfiguration | None:
        """Returns the configuration for this context."""
        return self._configuration

    @configuration.setter
    def configuration(self, value: TemplateConfiguration | None):
        """Sets the configuration and resets cached components."""
        self._configuration = value
        self._naming_convention = None
        self._path_resolver = None

    @property
    def depth(self) -> int:
        """Returns the depth of this context in the hierarchy."""
        if self._parent is None:
            return 0
        return self._parent.depth + 1

    @property
    def root(self) -> TemplateContext:
        """Returns the root context."""
        if self._parent is None:
            return self
        return self._parent.root

    def with_override(self, name: str = "", **overrides) -> TemplateContext:
        """Create child context with overrides.

        Args:
            name: Name for the child context.
            **overrides: Values to override in the child.

        Returns:
            New child context.
        """

        child = TemplateContext(
            name=name or f"{self._name}_child",
            parent=self,
            configuration=self._configuration,
        )

        for key, value in overrides.items():
            child.set(key, value)

        return child

    def get(self, key: str, default: Any = None) -> Any:
        """Get value with inheritance chain lookup.

        First checks this context, then walks up the parent chain.

        Args:
            key: Key to retrieve.
            default: Default value if not found in any context.

        Returns:
            Value or default.
        """

        if key in self._values:
            return self._values[key]

        if self._parent is not None:
            return self._parent.get(key, default)

        return default

    def get_local(self, key: str, default: Any = None) -> Any:
        """Get value from this context only (no inheritance).

        Args:
            key: Key to retrieve.
            default: Default value if not found.

        Returns:
            Value or default.
        """

        return self._values.get(key, default)

    def set(self, key: str, value: Any):
        """Set value in this context.

        Args:
            key: Key to set.
            value: Value to set.
        """

        self._values[key] = value

    def delete(self, key: str) -> bool:
        """Delete value from this context.

        Args:
            key: Key to delete.

        Returns:
            True if deleted, False if not found.
        """

        if key in self._values:
            del self._values[key]
            return True
        return False

    def has(self, key: str, check_parents: bool = True) -> bool:
        """Check if a key exists.

        Args:
            key: Key to check.
            check_parents: If True, also check parent contexts.

        Returns:
            True if key exists.
        """

        if key in self._values:
            return True

        if check_parents and self._parent is not None:
            return self._parent.has(key, check_parents=True)

        return False

    def keys(self, include_parents: bool = True) -> set[str]:
        """Get all keys in the context.

        Args:
            include_parents: If True, include keys from parent contexts.

        Returns:
            Set of all keys.
        """

        all_keys = set(self._values.keys())

        if include_parents and self._parent is not None:
            all_keys.update(self._parent.keys(include_parents=True))

        return all_keys

    def to_dict(self, include_parents: bool = True) -> dict[str, Any]:
        """Convert context to dictionary.

        Args:
            include_parents: If True, include values from parent contexts.

        Returns:
            Dictionary of all values.
        """

        if include_parents and self._parent is not None:
            result = self._parent.to_dict(include_parents=True)
            result.update(self._values)
            return result

        return self._values.copy()

    def clear(self):
        """Clear all values from this context."""
        self._values.clear()

    @property
    def naming_convention(self) -> NamingConvention | None:
        """Get naming convention for this context.

        First checks for a cached convention, then builds from configuration,
        then falls back to parent.

        Returns:
            NamingConvention or None.
        """

        if self._naming_convention is not None:
            return self._naming_convention

        if self._configuration is not None:
            self._naming_convention = (
                self._configuration.build_naming_convention()
            )
            return self._naming_convention

        if self._parent is not None:
            return self._parent.naming_convention

        return None

    @naming_convention.setter
    def naming_convention(self, value: NamingConvention | None):
        """Set naming convention for this context."""
        self._naming_convention = value

    @property
    def path_resolver(self) -> PathResolver | None:
        """Get path resolver for this context.

        First checks for a cached resolver, then builds from configuration,
        then falls back to parent.

        Returns:
            PathResolver or None.
        """

        if self._path_resolver is not None:
            return self._path_resolver

        if self._configuration is not None:
            self._path_resolver = self._configuration.build_path_resolver()
            return self._path_resolver

        if self._parent is not None:
            return self._parent.path_resolver

        return None

    @path_resolver.setter
    def path_resolver(self, value: PathResolver | None):
        """Set path resolver for this context."""
        self._path_resolver = value

    def resolve_name(self, rule_name: str, **tokens) -> str:
        """Resolve a name using this context.

        Merges context values with provided tokens.

        Args:
            rule_name: Name of the naming rule to use.
            **tokens: Token values to use.

        Returns:
            Resolved name string.

        Raises:
            ValueError: If no naming convention is available.
        """

        convention = self.naming_convention
        if convention is None:
            raise ValueError("No naming convention available in context")

        # Merge context values with provided tokens
        merged_tokens = self.to_dict()
        merged_tokens.update(tokens)

        return convention.solve(rule_name=rule_name, **merged_tokens)

    def resolve_path(self, template_name: str, **tokens) -> str:
        """Resolve a path using this context.

        Merges context values with provided tokens.

        Args:
            template_name: Name of the path template to use.
            **tokens: Token values to use.

        Returns:
            Resolved path string.

        Raises:
            ValueError: If no path resolver is available.
        """

        resolver = self.path_resolver
        if resolver is None:
            raise ValueError("No path resolver available in context")

        # Merge context values with provided tokens
        merged_tokens = self.to_dict()
        merged_tokens.update(tokens)

        return resolver.resolve_path(template_name, **merged_tokens)

    def __repr__(self) -> str:
        return (
            f"<TemplateContext(name={self._name!r}, "
            f"depth={self.depth}, "
            f"keys={len(self._values)})>"
        )

    def __contains__(self, key: str) -> bool:
        return self.has(key)

    def __getitem__(self, key: str) -> Any:
        value = self.get(key)
        if value is None and not self.has(key):
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any):
        self.set(key, value)

    def __delitem__(self, key: str):
        if not self.delete(key):
            raise KeyError(key)


class ContextStack:
    """Stack-based context management.

    Provides a simpler interface for managing temporary context overrides
    using a stack pattern.

    Example:
        >>> stack = ContextStack()
        >>> stack.push(project="MyGame")
        >>> stack.push(shot="010")
        >>> print(stack.get("project"))  # "MyGame"
        >>> print(stack.get("shot"))     # "010"
        >>> stack.pop()
        >>> print(stack.get("shot"))     # None
    """

    def __init__(self):
        """ContextStack constructor."""
        self._root = TemplateContext(name="root")
        self._stack: list[TemplateContext] = [self._root]

    @property
    def current(self) -> TemplateContext:
        """Returns the current context."""
        return self._stack[-1]

    @property
    def depth(self) -> int:
        """Returns the stack depth."""
        return len(self._stack)

    def push(self, name: str = "", **values) -> TemplateContext:
        """Push a new context onto the stack.

        Args:
            name: Name for the new context.
            **values: Values to set in the new context.

        Returns:
            The new context.
        """

        new_context = self.current.with_override(
            name=name or f"level_{self.depth}", **values
        )
        self._stack.append(new_context)
        return new_context

    def pop(self) -> TemplateContext | None:
        """Pop the current context from the stack.

        Returns:
            The popped context, or None if at root.
        """

        if len(self._stack) <= 1:
            return None

        return self._stack.pop()

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from current context.

        Args:
            key: Key to retrieve.
            default: Default value if not found.

        Returns:
            Value or default.
        """

        return self.current.get(key, default)

    def set(self, key: str, value: Any):
        """Set value in current context.

        Args:
            key: Key to set.
            value: Value to set.
        """

        self.current.set(key, value)

    def clear_to_root(self):
        """Clear stack back to root context."""
        self._stack = [self._root]
