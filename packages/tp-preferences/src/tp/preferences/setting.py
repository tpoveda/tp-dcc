from __future__ import annotations

import os
import stat
import typing
from typing import Any
from pathlib import Path

import yaml

if typing.TYPE_CHECKING:
    from .manager import PreferencesManager


class SettingObject(dict):
    """Represents a YAML preference setting."""

    def __init__(
        self,
        relative_path: str | None = None,
        root_paths: dict[str, str] | None = None,
        active_root: str | None = None,
        **kwargs: Any,
    ):
        """Initialize the SettingObject.

        Args:
            relative_path: The relative path to the setting file.
            root_paths: A dictionary of root paths for the setting.
            active_root: The name of the active root.
            kwargs: Additional keyword arguments.
        """

        relative_path = relative_path or ""
        ext = Path(relative_path).suffixes
        if not ext:
            relative_path = os.path.extsep.join((relative_path, "yaml"))

        kwargs["relativePath"] = relative_path
        kwargs["rootPaths"] = root_paths or {}
        kwargs["activeRoot"] = active_root or ""

        super().__init__(**kwargs)

    def __getattr__(self, item: str) -> Any:
        """Override the __getattr__ method to allow access to dictionary keys
        as attributes.

        This method is called when an attribute is not found in the instance
        dictionary. It tries to access the attribute as a key in the
        dictionary. If the key is not found, it falls back to the default
        behavior of __getattribute__.

        Args:
            item: The name of the attribute to access.

        Returns:
            The value associated with the attribute if it exists, or raises
            AttributeError if the attribute does not exist.

        Raises:
            AttributeError: If the attribute does not exist in the instance
                dictionary or the parent class.
        """

        try:
            return self[item]
        except KeyError:
            return super().__getattribute__(item)

    def __setattr__(self, key: str, value: Any):
        """Override the __setattr__ method to allow setting dictionary keys
        as attributes.

        This method is called when an attribute is set on the instance. It
        tries to set the attribute as a key in the dictionary. If the key
        already exists, it updates its value.

        Args:
            key: The name of the attribute to set.
            value: The value to set for the attribute.
        """

        self[key] = value

    def __cmp__(self, other: SettingObject) -> bool:
        """Compare two SettingObject instances.

        Args:
            other: The other SettingObject to compare with.

        Returns:
            True if the two SettingObjects are equal, False otherwise.
        """

        return self.get("name") == other.get("name") and self.get(
            "version"
        ) == other.get("version")

    def __repr__(self) -> str:
        """Return a string representation of the SettingObject.

        Returns:
            A string representation of the SettingObject.
        """
        roots = list(self.get("rootPaths", {}).keys())
        return (
            f"<{self.__class__.__name__} roots='{roots}' "
            f"path='{self['relativePath']}, active_root={self['activeRoot']}'>"
        )

    def root_path(self) -> str | None:
        """Return the root path of the top-most source setting file.

        Returns:
            The root path of the setting.
        """

        root_paths: dict[str, str] = self.get("rootPaths", {})
        if not root_paths:
            return None

        return root_paths.get(self.get("activeRoot")) or str(next(iter(root_paths.values())))

    def path(self) -> str:
        """Return the path of the setting.

        Returns:
            The path of the setting.
        """

        return str(Path(self.root_path()) / self.get("relativePath", ""))

    def is_valid(self) -> bool:
        """Return True if the setting exists on disk.

        Returns:
            True if the setting exists on disk, False otherwise.
        """

        if not self.get("rootPaths"):
            return False

        return True if self.path() and Path(self.path()).exists() else False

    def diff(self) -> dict[str, str]:
        """Returns a dictionary showing where each key came from.

        Returns:
            Mapping of top-level keys → root_name
        """

        key_sources = {}
        root_paths = self.get("rootPaths", {})
        for root_name, path in root_paths.items():
            # noinspection PyBroadException
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                for k in data:
                    if k not in key_sources:
                        key_sources[k] = root_name
            except Exception:
                continue

        return key_sources

    def save(
        self, root_path: str | None = None, indent: bool = True, sort: bool = False
    ) -> str:
        """Save this setting to a specific root path (manual control).

        Args:
            root_path: Absolute root path to save to.
            indent: Whether to indent the YAML file.
            sort: Whether to sort the keys in the YAML file.

        Returns:
            Path to the saved file.

        Raises:
            ValueError: If the root path is not specified and not set in the
                setting.
        """

        root_path = root_path or self.root_path()
        if not root_path:
            raise ValueError(
                "Root path must be specified or set in the setting before saving."
            )

        file_path = Path(root_path) / self.get("relativePath", "")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        kwargs: dict[str, Any] = {"sort_keys": sort}
        if indent:
            kwargs["indent"] = 2

        parent_dir = Path(file_path).parent
        parent_dir.mkdir(parents=True, exist_ok=True)
        if not os.access(parent_dir, os.W_OK):
            raise PermissionError(
                f"Cannot write settings: directory is not writable: '{parent_dir}'"
            )

        output = self.copy()
        output.pop("rootPaths", None)
        output.pop("relativePath", None)
        output.pop("activeRoot", None)

        with self._open_writable_once(str(file_path)) as f:
            yaml.safe_dump(output, f, **kwargs)

        return str(file_path)

    @staticmethod
    def _open_writable_once(path: str):
        """Open a file for writing, attempting to change permissions if
        necessary.
        """

        try:
            return open(path, "w", encoding="utf-8")
        except PermissionError:
            if os.path.exists(path):
                # noinspection PyBroadException
                try:
                    current_mode = os.stat(path).st_mode
                    os.chmod(path, current_mode | stat.S_IWUSR)
                except Exception:
                    # If chmod fails, re-raise the original error on the next
                    # open
                    pass

            # Retry once; if it still fails, let the error propagate
            return open(path, "w", encoding="utf-8")

    def save_to_active_root(
        self, preferences_manager: PreferencesManager
    ) -> str | None:
        """Save the setting to the currently active writable root.

        Args:
            preferences_manager: A PreferencesManager instance.

        Returns:
            Path to the saved file, or None if no writable root is set.
        """

        if not self.active_root:
            return None

        root_path = preferences_manager.root(self.active_root)
        return self.save(root_path)
