from __future__ import annotations

import json
from abc import abstractmethod
from copy import deepcopy
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

from loguru import logger

from tp.libs.plugin import PluginsManager
from tp.libs.python import paths

_plugin_manager: PluginsManager | None = None

# Type variable for callback functions
T = TypeVar("T", bound="MetadataDictionary")


class MergeStrategy(Enum):
    """Enum defining merge strategies for loading metadata."""

    REPLACE = auto()  # Replace current data with loaded data
    MERGE = auto()  # Shallow merge (update with loaded data)
    DEEP_MERGE = auto()  # Deep merge nested dictionaries


class MetadataDictionary(dict):
    """A dictionary class that provides persistent metadata storage across DCC applications.

    This class serves as the base interface for storing and retrieving metadata
    in a dictionary-like format. Each DCC application can provide its own implementation
    to store metadata in application-specific locations (nodes, properties, etc.).

    Features:
        - Unified API across multiple DCC applications
        - Schema validation support
        - Version tracking and migration
        - Callback hooks for pre/post save/load operations
        - Dot notation access for nested keys
        - Export/import to JSON files

    Attributes:
        priority: Priority of the MetadataDictionary plugin. Higher priority
            implementations are preferred when multiple are available.
    """

    priority: int = 1

    # Callback hooks
    _pre_save_callbacks: list[Callable[[MetadataDictionary], None]] = []
    _post_save_callbacks: list[Callable[[MetadataDictionary], None]] = []
    _pre_load_callbacks: list[Callable[[MetadataDictionary], None]] = []
    _post_load_callbacks: list[Callable[[MetadataDictionary], None]] = []
    _on_change_callbacks: list[
        Callable[[MetadataDictionary, str, Any], None]
    ] = []

    def __init__(
        self,
        identifier: str,
        *args: Any,
        schema: dict[str, Any] | None = None,
        version: int = 1,
        merge_strategy: MergeStrategy = MergeStrategy.REPLACE,
        **kwargs: Any,
    ):
        """Initialize a MetadataDictionary with the given identifier.

        Args:
            identifier: Unique identifier for this metadata dictionary instance.
            *args: Variable length argument list passed to dict.
            schema: Optional JSON schema for validation.
            version: Version number for this metadata dictionary.
            merge_strategy: Strategy to use when loading/merging data.
            **kwargs: Arbitrary keyword arguments passed to dict.
        """

        super().__init__(*args, **kwargs)

        self._id = identifier
        self._schema = schema
        self._version = version
        self._merge_strategy = merge_strategy
        self._callbacks: dict[str, list[Callable]] = {
            "pre_save": [],
            "post_save": [],
            "pre_load": [],
            "post_load": [],
            "on_change": [],
        }

        # Load any persistent data for the given identifier.
        self.load()

    @property
    def id(self) -> str:
        """Return the identifier for this MetadataDictionary.

        Returns:
            Identifier for this MetadataDictionary.
        """

        return self._id

    @property
    def version(self) -> int:
        """Return the version number of this MetadataDictionary.

        Returns:
            Version number.
        """

        return self._version

    @property
    def schema(self) -> dict[str, Any] | None:
        """Return the JSON schema for this MetadataDictionary.

        Returns:
            JSON schema dictionary or None if no schema is set.
        """

        return self._schema

    @schema.setter
    def schema(self, value: dict[str, Any] | None) -> None:
        """Set the JSON schema for validation.

        Args:
            value: JSON schema dictionary or None to disable validation.
        """

        self._schema = value

    # -------------------------------------------------------------------------
    # Dict overrides for change notifications
    # -------------------------------------------------------------------------

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item and trigger change callbacks.

        Args:
            key: Key to set.
            value: Value to set.
        """

        super().__setitem__(key, value)
        self._trigger_callbacks("on_change", key, value)

    def __delitem__(self, key: str) -> None:
        """Delete an item and trigger change callbacks.

        Args:
            key: Key to delete.
        """

        super().__delitem__(key)
        self._trigger_callbacks("on_change", key, None)

    # -------------------------------------------------------------------------
    # Dot notation access
    # -------------------------------------------------------------------------

    def get_nested(
        self, key_path: str, default: Any = None, separator: str = "."
    ) -> Any:
        """Get a value using dot notation for nested keys.

        Args:
            key_path: Dot-separated path to the key (e.g., "config.render.quality").
            default: Default value if key is not found.
            separator: Separator character for the path (default ".").

        Returns:
            Value at the key path, or default if not found.

        Example:
            >>> data = get('mydata')
            >>> data['config'] = {'render': {'quality': 'high'}}
            >>> data.get_nested('config.render.quality')
            'high'
        """

        keys = key_path.split(separator)
        value: Any = self
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set_nested(
        self, key_path: str, value: Any, separator: str = "."
    ) -> None:
        """Set a value using dot notation for nested keys.

        Creates intermediate dictionaries if they don't exist.

        Args:
            key_path: Dot-separated path to the key (e.g., "config.render.quality").
            value: Value to set.
            separator: Separator character for the path (default ".").

        Example:
            >>> data = get('mydata')
            >>> data.set_nested('config.render.quality', 'ultra')
            >>> data['config']['render']['quality']
            'ultra'
        """

        keys = key_path.split(separator)
        current: dict = self
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
        self._trigger_callbacks("on_change", key_path, value)

    def delete_nested(self, key_path: str, separator: str = ".") -> bool:
        """Delete a value using dot notation for nested keys.

        Args:
            key_path: Dot-separated path to the key.
            separator: Separator character for the path (default ".").

        Returns:
            True if the key was deleted, False if it didn't exist.
        """

        keys = key_path.split(separator)
        current: Any = self
        for key in keys[:-1]:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False
        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
            self._trigger_callbacks("on_change", key_path, None)
            return True
        return False

    # -------------------------------------------------------------------------
    # Callback/hooks system
    # -------------------------------------------------------------------------

    def add_callback(
        self,
        event: str,
        callback: Callable,
    ) -> None:
        """Register a callback for a specific event.

        Args:
            event: Event name ('pre_save', 'post_save', 'pre_load', 'post_load', 'on_change').
            callback: Callback function to register.

        Raises:
            ValueError: If the event name is not recognized.

        Example:
            >>> def on_save(data):
            ...     print(f"Saving data: {data}")
            >>> data = get('mydata')
            >>> data.add_callback('pre_save', on_save)
        """

        if event not in self._callbacks:
            raise ValueError(
                f"Unknown event '{event}'. Valid events: {list(self._callbacks.keys())}"
            )
        self._callbacks[event].append(callback)

    def remove_callback(self, event: str, callback: Callable) -> bool:
        """Remove a callback for a specific event.

        Args:
            event: Event name.
            callback: Callback function to remove.

        Returns:
            True if the callback was removed, False if it wasn't found.
        """

        if event not in self._callbacks:
            return False
        try:
            self._callbacks[event].remove(callback)
            return True
        except ValueError:
            return False

    def clear_callbacks(self, event: str | None = None) -> None:
        """Clear all callbacks for an event, or all events if none specified.

        Args:
            event: Optional event name. If None, clears all callbacks.
        """

        if event is None:
            for key in self._callbacks:
                self._callbacks[key].clear()
        elif event in self._callbacks:
            self._callbacks[event].clear()

    def _trigger_callbacks(self, event: str, *args: Any) -> None:
        """Trigger all callbacks for a specific event.

        Args:
            event: Event name.
            *args: Arguments to pass to the callbacks.
        """

        for callback in self._callbacks.get(event, []):
            try:
                if event == "on_change":
                    callback(self, *args)
                else:
                    callback(self)
            except Exception as err:
                logger.warning(f"Callback error for event '{event}': {err}")

    # -------------------------------------------------------------------------
    # Schema validation
    # -------------------------------------------------------------------------

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the dictionary contents against the schema.

        Returns:
            Tuple of (is_valid, list_of_errors).

        Example:
            >>> data = get('mydata', schema={'type': 'object', 'required': ['name']})
            >>> data['name'] = 'test'
            >>> is_valid, errors = data.validate()
            >>> print(is_valid)
            True
        """

        if self._schema is None:
            return True, []

        errors: list[str] = []

        # Basic schema validation (type checking)
        schema_type = self._schema.get("type")
        if schema_type == "object":
            # Check required fields
            required = self._schema.get("required", [])
            for field in required:
                if field not in self:
                    errors.append(f"Missing required field: '{field}'")

            # Check properties
            properties = self._schema.get("properties", {})
            for key, prop_schema in properties.items():
                if key in self:
                    value = self[key]
                    prop_type = prop_schema.get("type")
                    if not self._validate_type(value, prop_type):
                        errors.append(
                            f"Field '{key}' has wrong type. Expected {prop_type}, "
                            f"got {type(value).__name__}"
                        )

        return len(errors) == 0, errors

    @staticmethod
    def _validate_type(value: Any, expected_type: str | None) -> bool:
        """Validate a value against an expected JSON schema type.

        Args:
            value: Value to validate.
            expected_type: Expected JSON schema type.

        Returns:
            True if the value matches the expected type.
        """

        if expected_type is None:
            return True

        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }

        expected = type_map.get(expected_type)
        if expected is None:
            return True
        return isinstance(value, expected)

    def validate_and_raise(self) -> None:
        """Validate the dictionary and raise an exception if invalid.

        Raises:
            ValueError: If validation fails.
        """

        is_valid, errors = self.validate()
        if not is_valid:
            raise ValueError(f"Schema validation failed: {'; '.join(errors)}")

    # -------------------------------------------------------------------------
    # Versioning and migration
    # -------------------------------------------------------------------------

    def get_stored_version(self) -> int:
        """Get the version number stored in the metadata.

        Returns:
            Stored version number, or 0 if not found.
        """

        return self.get("__version__", 0)

    def set_version(self, version: int) -> None:
        """Set the version number in the metadata.

        Args:
            version: Version number to set.
        """

        self["__version__"] = version
        self._version = version

    def migrate(
        self,
        migrations: dict[int, Callable[[dict], dict]],
    ) -> bool:
        """Apply migrations to update data from an older version.

        Args:
            migrations: Dictionary mapping version numbers to migration functions.
                Each function takes the current data dict and returns the migrated dict.

        Returns:
            True if any migrations were applied, False otherwise.

        Example:
            >>> def migrate_v1_to_v2(data):
            ...     # Rename 'old_key' to 'new_key'
            ...     if 'old_key' in data:
            ...         data['new_key'] = data.pop('old_key')
            ...     return data
            >>>
            >>> data = get('mydata', version=2)
            >>> data.migrate({1: migrate_v1_to_v2})
        """

        stored_version = self.get_stored_version()
        if stored_version >= self._version:
            return False

        applied = False
        for version in sorted(migrations.keys()):
            if stored_version < version <= self._version:
                try:
                    migration_func = migrations[version]
                    migrated = migration_func(dict(self))
                    self.clear()
                    self.update(migrated)
                    applied = True
                    logger.info(f"Applied migration to version {version}")
                except Exception as err:
                    logger.error(
                        f"Migration to version {version} failed: {err}"
                    )
                    raise

        if applied:
            self.set_version(self._version)

        return applied

    # -------------------------------------------------------------------------
    # Merge strategies
    # -------------------------------------------------------------------------

    @staticmethod
    def deep_merge(base: dict, update: dict) -> dict:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary.
            update: Dictionary to merge into base.

        Returns:
            Merged dictionary.
        """

        result = deepcopy(base)
        for key, value in update.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = MetadataDictionary.deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result

    def merge_with(
        self, data: dict[str, Any], strategy: MergeStrategy | None = None
    ) -> None:
        """Merge data into this dictionary using the specified strategy.

        Args:
            data: Data to merge.
            strategy: Merge strategy to use. If None, uses the instance's default.
        """

        strategy = strategy or self._merge_strategy

        if strategy == MergeStrategy.REPLACE:
            self.clear()
            self.update(data)
        elif strategy == MergeStrategy.MERGE:
            self.update(data)
        elif strategy == MergeStrategy.DEEP_MERGE:
            merged = self.deep_merge(dict(self), data)
            self.clear()
            self.update(merged)

    # -------------------------------------------------------------------------
    # Export/Import functionality
    # -------------------------------------------------------------------------

    def export_to_file(
        self,
        file_path: str | Path,
        include_version: bool = True,
        indent: int = 2,
    ) -> None:
        """Export the metadata dictionary to a JSON file.

        Args:
            file_path: Path to the output JSON file.
            include_version: Whether to include version info in export.
            indent: JSON indentation level.

        Raises:
            ValueError: If the data cannot be serialized to JSON.

        Example:
            >>> data = get('mydata')
            >>> data['name'] = 'test'
            >>> data.export_to_file('metadata_backup.json')
        """

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        export_data = dict(self)
        if include_version and "__version__" not in export_data:
            export_data["__version__"] = self._version

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=indent, ensure_ascii=False)
            logger.info(f"Exported metadata to {file_path}")
        except (TypeError, ValueError) as err:
            raise ValueError(
                f"Failed to export metadata to JSON: {err}"
            ) from err

    def import_from_file(
        self,
        file_path: str | Path,
        strategy: MergeStrategy | None = None,
        validate_after: bool = True,
    ) -> None:
        """Import metadata from a JSON file.

        Args:
            file_path: Path to the JSON file to import.
            strategy: Merge strategy to use. If None, uses the instance's default.
            validate_after: Whether to validate after import (if schema is set).

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file contains invalid JSON or fails validation.

        Example:
            >>> data = get('mydata')
            >>> data.import_from_file('metadata_backup.json')
        """

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)
        except json.JSONDecodeError as err:
            raise ValueError(
                f"Invalid JSON in file {file_path}: {err}"
            ) from err

        self.merge_with(import_data, strategy)

        if validate_after and self._schema:
            self.validate_and_raise()

        logger.info(f"Imported metadata from {file_path}")

    # -------------------------------------------------------------------------
    # Abstract methods
    # -------------------------------------------------------------------------

    @classmethod
    @abstractmethod
    def usable(cls) -> bool:
        """Return whether this MetadataDictionary is usable in the current environment.

        This method should check if the current DCC application matches the
        implementation (e.g., Maya, Houdini, MotionBuilder).

        Returns:
            True if this MetadataDictionary can be used, False otherwise.
        """

        raise NotImplementedError(
            "Method 'usable' must be implemented in subclasses"
        )

    @abstractmethod
    def _load_data(self) -> dict[str, Any]:
        """Load raw data from persistent storage.

        This is the internal method that subclasses should implement.

        Returns:
            Dictionary of loaded data.
        """

        raise NotImplementedError(
            "Method '_load_data' must be implemented in subclasses"
        )

    @abstractmethod
    def _save_data(self, data: dict[str, Any]) -> None:
        """Save raw data to persistent storage.

        This is the internal method that subclasses should implement.

        Args:
            data: Dictionary data to save.
        """

        raise NotImplementedError(
            "Method '_save_data' must be implemented in subclasses"
        )

    def load(self, strategy: MergeStrategy | None = None) -> None:
        """Load the data from persistent storage and update this dictionary.

        Args:
            strategy: Optional merge strategy override.
        """

        self._trigger_callbacks("pre_load")
        try:
            data = self._load_data()
            if data:
                self.merge_with(data, strategy)
        except Exception as err:
            logger.warning(f"Failed to load metadata '{self._id}': {err}")
        self._trigger_callbacks("post_load")

    def save(self, validate_before: bool = False) -> None:
        """Save the MetadataDictionary data to persistent storage.

        Args:
            validate_before: Whether to validate before saving (if schema is set).

        Raises:
            ValueError: If validation is enabled and fails.
        """

        if validate_before and self._schema:
            self.validate_and_raise()

        self._trigger_callbacks("pre_save")
        try:
            self._save_data(dict(self))
        except Exception as err:
            logger.error(f"Failed to save metadata '{self._id}': {err}")
            raise
        self._trigger_callbacks("post_save")

    def clear_and_save(self) -> None:
        """Clear all data from this dictionary and save the empty state."""

        self.clear()
        self.save()

    def update_and_save(
        self, data: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        """Update the dictionary with provided data and save.

        Args:
            data: Optional dictionary of data to update with.
            **kwargs: Additional key-value pairs to update.
        """

        if data:
            self.update(data)
        if kwargs:
            self.update(kwargs)
        self.save()

    @abstractmethod
    def delete(self) -> bool:
        """Delete the metadata from persistent storage.

        Returns:
            True if the metadata was deleted, False if it didn't exist.
        """

        raise NotImplementedError(
            "Method 'delete' must be implemented in subclasses"
        )


def get(identifier: str, *args: Any, **kwargs: Any) -> MetadataDictionary:
    """Return a MetadataDictionary instance for the current DCC application.

    This function automatically detects the current DCC application and returns
    an appropriate MetadataDictionary implementation that can serialize itself
    within that application.

    Args:
        identifier: Unique identifier for the MetadataDictionary to return.
        *args: Variable length argument list passed to the MetadataDictionary.
        **kwargs: Arbitrary keyword arguments passed to the MetadataDictionary.
            Special kwargs:
            - schema: JSON schema for validation.
            - version: Version number for versioning support.
            - merge_strategy: MergeStrategy enum for load/merge operations.

    Returns:
        MetadataDictionary instance appropriate for the current DCC application.

    Raises:
        RuntimeError: If no suitable MetadataDictionary implementation could be found.

    Example:
        >>> from tp.libs.metadict import get, MergeStrategy
        >>>
        >>> # Simple usage
        >>> data = get('mydata')
        >>> data['key'] = 'value'
        >>> data.save()
        >>>
        >>> # With schema validation
        >>> schema = {'type': 'object', 'required': ['name'], 'properties': {'name': {'type': 'string'}}}
        >>> data = get('validated_data', schema=schema)
        >>>
        >>> # With versioning
        >>> data = get('versioned_data', version=2)
    """

    global _plugin_manager

    if not _plugin_manager:
        _plugin_manager = PluginsManager(
            interfaces=[MetadataDictionary],
            variable_name="__name__",
            log_errors=False,
        )
        _plugin_manager.register_paths([paths.canonical_path("./apps")])

    for plugin in sorted(
        _plugin_manager.plugin_classes, key=lambda p: p.priority, reverse=True
    ):
        if plugin.usable():  # type: ignore[union-attr]
            return plugin(identifier, *args, **kwargs)  # type: ignore[return-value]

    raise RuntimeError(
        "No MetadataDictionary implementation found for the current host application. "
        "Ensure a suitable plugin is available in the 'apps' directory."
    )
