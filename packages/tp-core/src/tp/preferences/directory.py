from __future__ import annotations

import uuid
from pathlib import Path


class DirectoryPath:
    """Represents a normalized directory path with optional unique identifier and alias.

    This class is used to manage and encapsulate the representation of a
    directory path, along with providing an optional unique identifier and a
    human-readable alias.

    It allows comparison, dictionary representation, string formatting, and
    hashing based on the normalized directory path.
    """

    # noinspection PyShadowingBuiltins
    def __init__(self, path: str, id: str | None = None, alias: str = None):
        """Initialize DirectoryPath.

        Args:
            path: Directory path string.
            id: Unique identifier.
            alias: Human-readable name.
        """

        self._id = id or str(uuid.uuid4())[:6]
        self._path = str(Path(path).resolve())
        self._alias = alias or Path(path).name

    def __hash__(self) -> int:
        """Return hash based on the normalized path.

        Returns:
            Hash value of the normalized directory path.
        """

        return hash(self.path)

    def __repr__(self) -> str:
        """Return detailed string representation.

        Returns:
            String representation of the DirectoryPath instance.
        """

        return f"{self.__class__.__name__}(id='{self.id}', path='{self.path}', alias='{self.alias}')"

    def __str__(self) -> str:
        """Return the path as a string.

        Returns:
            The normalized directory path as a string.
        """

        return self.path

    @property
    def id(self) -> str:
        """The unique identifier."""

        return self._id

    @property
    def path(self) -> str:
        """The normalized directory path."""
        return self._path

    @property
    def alias(self) -> str:
        """The human-readable alias."""
        return self._alias

    @alias.setter
    def alias(self, value: str) -> None:
        """Set the alias."""
        self._alias = value

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with `id`, `path`, and `alias` keys.
        """

        return {"id": self.id, "path": self.path, "alias": self.alias}

    def __eq__(self, other: str | DirectoryPath) -> bool:
        """Compare paths after normalization.

        Args:
            other: String path or DirectoryPath instance to compare

        Returns:
            True if normalized paths are equal
        """

        if isinstance(other, str):
            return str(Path(other).resolve()) == self.path
        elif isinstance(other, DirectoryPath):
            return other.path == self.path

        return False
