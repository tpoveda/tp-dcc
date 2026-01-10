"""Configuration merging utilities."""

from __future__ import annotations

from typing import Any


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries.

    Values from override take precedence. Nested dictionaries are merged
    recursively. Lists are replaced, not merged.

    Args:
        base: Base dictionary.
        override: Override dictionary.

    Returns:
        Merged dictionary (new instance).

    Example:
        >>> base = {"a": 1, "b": {"c": 2, "d": 3}}
        >>> override = {"b": {"c": 10}, "e": 5}
        >>> deep_merge(base, override)
        {'a': 1, 'b': {'c': 10, 'd': 3}, 'e': 5}
    """

    result = base.copy()

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def merge_lists_by_key(
    base: list[dict],
    override: list[dict],
    key: str,
) -> list[dict]:
    """Merge two lists of dictionaries by a key field.

    Items with matching key values are merged, others are appended.

    Args:
        base: Base list of dictionaries.
        override: Override list of dictionaries.
        key: Key field to match on.

    Returns:
        Merged list of dictionaries.

    Example:
        >>> base = [{"name": "a", "value": 1}, {"name": "b", "value": 2}]
        >>> override = [{"name": "a", "value": 10}, {"name": "c", "value": 3}]
        >>> merge_lists_by_key(base, override, "name")
        [{'name': 'a', 'value': 10}, {'name': 'b', 'value': 2}, {'name': 'c', 'value': 3}]
    """

    # Create lookup for base items
    base_lookup = {item.get(key): item for item in base}

    result = []
    seen_keys = set()

    # First, process items from base (in order)
    for item in base:
        item_key = item.get(key)
        if item_key in seen_keys:
            continue
        seen_keys.add(item_key)

        # Check if there's an override
        override_item = next(
            (o for o in override if o.get(key) == item_key), None
        )

        if override_item:
            result.append(deep_merge(item, override_item))
        else:
            result.append(item.copy())

    # Then, add new items from override
    for item in override:
        item_key = item.get(key)
        if item_key not in seen_keys:
            seen_keys.add(item_key)
            result.append(item.copy())

    return result


def apply_overrides(config: dict, overrides: dict) -> dict:
    """Apply overrides to a configuration.

    Supports dot notation for nested keys.

    Args:
        config: Base configuration.
        overrides: Overrides to apply (can use dot notation).

    Returns:
        Configuration with overrides applied.

    Example:
        >>> config = {"tokens": {"side": {"default": "L"}}}
        >>> overrides = {"tokens.side.default": "R"}
        >>> apply_overrides(config, overrides)
        {'tokens': {'side': {'default': 'R'}}}
    """

    result = deep_merge(config, {})

    for key, value in overrides.items():
        if "." in key:
            # Dot notation - navigate to nested location
            parts = key.split(".")
            target = result

            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]

            target[parts[-1]] = value
        else:
            result[key] = value

    return result


class ConfigurationMerger:
    """Merge multiple configurations with precedence.

    Supports layered configurations where later configs override earlier ones.

    Example:
        >>> merger = ConfigurationMerger()
        >>> merger.add_layer(base_config, "base")
        >>> merger.add_layer(project_config, "project")
        >>> merger.add_layer(user_config, "user")
        >>> merged = merger.merge()
    """

    def __init__(self):
        """ConfigurationMerger constructor."""
        self._layers: list[tuple[str, dict]] = []

    def add_layer(self, config: dict, name: str = ""):
        """Add a configuration layer.

        Later layers take precedence over earlier ones.

        Args:
            config: Configuration dictionary.
            name: Optional name for debugging.
        """
        self._layers.append((name, config))

    def clear_layers(self):
        """Clear all configuration layers."""
        self._layers.clear()

    @property
    def layer_count(self) -> int:
        """Returns the number of layers."""
        return len(self._layers)

    @property
    def layer_names(self) -> list[str]:
        """Returns the names of all layers."""
        return [name for name, _ in self._layers]

    def merge(self) -> dict:
        """Merge all layers into a single configuration.

        Returns:
            Merged configuration dictionary.
        """
        if not self._layers:
            return {}

        result = {}
        for name, config in self._layers:
            result = deep_merge(result, config)

        return result

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the merged configuration.

        Supports dot notation for nested keys.

        Args:
            key: Key to retrieve (supports dot notation).
            default: Default value if not found.

        Returns:
            Value or default.
        """
        merged = self.merge()

        if "." not in key:
            return merged.get(key, default)

        parts = key.split(".")
        target = merged

        for part in parts:
            if not isinstance(target, dict) or part not in target:
                return default
            target = target[part]

        return target

    def get_layer(self, name: str) -> dict | None:
        """Get a specific layer by name.

        Args:
            name: Layer name.

        Returns:
            Layer configuration or None if not found.
        """
        for layer_name, config in self._layers:
            if layer_name == name:
                return config
        return None
