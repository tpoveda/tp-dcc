from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tp.libs.metadict import MetadataDictionary

# In-memory storage for standalone mode.
_standalone_storage: dict[str, dict[str, Any]] = {}

# File-based storage directory (configurable)
_file_storage_dir: Path | None = None


def set_file_storage_directory(directory: str | Path | None) -> None:
    """Set the directory for file-based persistent storage.

    When set, standalone mode will persist data to JSON files in this directory.
    Set to None to disable file persistence and use memory-only storage.

    Args:
        directory: Path to the storage directory, or None to disable.

    Example:
        >>> from tp.libs.metadict.apps.standalone.metadict import set_file_storage_directory
        >>> set_file_storage_directory('/path/to/storage')
    """

    global _file_storage_dir
    if directory is None:
        _file_storage_dir = None
    else:
        _file_storage_dir = Path(directory)
        _file_storage_dir.mkdir(parents=True, exist_ok=True)


def get_file_storage_directory() -> Path | None:
    """Get the current file storage directory.

    Returns:
        Current storage directory path, or None if file persistence is disabled.
    """

    return _file_storage_dir


class StandaloneMetadataDictionary(MetadataDictionary):
    """Metadata dictionary class for standalone Python applications.

    This implementation stores metadata in memory by default, with optional
    file-based persistence. Data is not persisted across Python sessions
    unless file storage is enabled.

    This serves as a fallback when no DCC application is detected and is useful
    for testing or scripting outside of DCC environments.

    To enable file persistence:
        >>> from tp.libs.metadict.apps.standalone.metadict import set_file_storage_directory
        >>> set_file_storage_directory('/path/to/storage')

    Attributes:
        priority: Lower priority ensures DCC-specific implementations are preferred.
    """

    priority: int = 1

    @classmethod
    def usable(cls) -> bool:
        """Return whether this MetadataDictionary is usable.

        Always returns True as this is the fallback implementation.

        Returns:
            True (always usable as fallback).
        """

        return True

    def _load_data(self) -> dict[str, Any]:
        """Load raw data from storage (memory or file).

        Returns:
            Dictionary of loaded data.
        """

        # Try file storage first if enabled
        if _file_storage_dir is not None:
            file_path = _file_storage_dir / f"{self.id}.json"
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, OSError):
                    pass

        # Fall back to memory storage
        if self.id in _standalone_storage:
            return _standalone_storage[self.id].copy()

        return {}

    def _save_data(self, data: dict[str, Any]) -> None:
        """Save raw data to storage (memory and optionally file).

        Args:
            data: Dictionary data to save.
        """

        # Always save to memory
        _standalone_storage[self.id] = data.copy()

        # Also save to file if enabled
        if _file_storage_dir is not None:
            file_path = _file_storage_dir / f"{self.id}.json"
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except (TypeError, OSError) as err:
                raise ValueError(f"Failed to save to file: {err}") from err

    def delete(self) -> bool:
        """Delete the metadata from storage (memory and file).

        Returns:
            True if the data was deleted, False if it didn't exist.
        """

        deleted = False

        # Delete from memory
        if self.id in _standalone_storage:
            del _standalone_storage[self.id]
            deleted = True

        # Delete file if exists
        if _file_storage_dir is not None:
            file_path = _file_storage_dir / f"{self.id}.json"
            if file_path.exists():
                file_path.unlink()
                deleted = True

        return deleted


def clear_all_standalone_storage() -> None:
    """Clear all data from standalone storage (memory and files).

    This is useful for testing or when you want to reset all metadata.
    """

    _standalone_storage.clear()

    # Also clear files if file storage is enabled
    if _file_storage_dir is not None and _file_storage_dir.exists():
        for file_path in _file_storage_dir.glob("*.json"):
            file_path.unlink()


def list_stored_identifiers() -> list[str]:
    """List all stored metadata identifiers.

    Returns:
        List of identifier strings.
    """

    identifiers = set(_standalone_storage.keys())

    # Also check file storage
    if _file_storage_dir is not None and _file_storage_dir.exists():
        for file_path in _file_storage_dir.glob("*.json"):
            identifiers.add(file_path.stem)

    return sorted(identifiers)
