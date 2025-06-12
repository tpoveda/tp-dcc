from __future__ import annotations

from typing import Iterator, Any

from .plugin import Plugin


# noinspection PyUnresolvedReferences
class DictPlugin(Plugin):
    """Base class for dictionary plugins."""

    def initialize(self):
        """Initializes the plugin."""

        pass

    def __getitem__(self, key: str) -> Any:
        """Gets the value associated with the given key.

        Args:
            key: The key to retrieve the value for.

        Returns:
            The value associated with the key.
        """

        return self.data[key]  # type: ignore

    def __setitem__(self, key: str, value: Any):
        """Sets the value associated with the given key.

        Args:
            key: The key to set the value for.
            value: The value to set.
        """

        self.data[key] = value  # type: ignore

    def __delitem__(self, key: str):
        """Deletes the value associated with the given key.

        Args:
            key: The key to delete the value for.
        """

        del self.data[key]  # type: ignore

    def __iter__(self) -> Iterator:
        """Returns an iterator over the keys of the plugin data.

        Returns:
            An iterator over the keys of the plugin data.
        """

        return iter(self.data)  # type: ignore

    def __len__(self) -> int:
        """Returns the number of items in the plugin data.

        Returns:
            The number of items in the plugin data.
        """

        return len(self.data)  # type: ignore

    def __contains__(self, key) -> bool:
        """Checks if the given key is in the plugin data.

        Args:
            key: The key to check for.

        Returns:
            True if the key is in the plugin data, False otherwise.
        """

        return key in self.data  # type: ignore

    def get(self, key: str, default: Any = None) -> Any:
        """Gets the value associated with the given key, returning a default
        value if the key is not found.

        Args:
            key: The key to retrieve the value for.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value if the
            key is not found.
        """

        return self.data.get(key, default)  # type: ignore

    def keys(self) -> Iterator:
        """Returns an iterator over the keys of the plugin data.

        Returns:
            An iterator over the keys of the plugin data.
        """

        return self.data.keys()  # type: ignore

    def values(self) -> Iterator:
        """Returns an iterator over the values of the plugin data.

        Returns:
            An iterator over the values of the plugin data.
        """

        return self.data.values()  # type: ignore

    def items(self) -> Iterator:
        """Returns an iterator over the items (key-value pairs) of the plugin
        data.

        Returns:
            An iterator over the items (key-value pairs) of the plugin data.
        """

        return self.data.items()  # type: ignore
