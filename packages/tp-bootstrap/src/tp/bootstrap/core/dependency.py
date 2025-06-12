from __future__ import annotations

import re
from typing import Any

DEPENDENCY_VERSION_FILTER = re.compile("(.*)==(.*)")


class Dependency:
    """Object that represents a package dependency/requirements in this format:
    `package==0.1.0` or `package`.
    """

    def __init__(self, dependency_string: str):
        self._dependency_string = dependency_string
        self._name = ""
        self._version = ""
        self._valid = False

    def __hash__(self) -> int:
        """Returns the hash of the dependency.

        Returns:
            Hash of the dependency.
        """

        return hash(f"{self._name}=={self._version}")

    def __repr__(self) -> str:
        """Returns a string representation of the dependency.

        Returns:
            String representation of the dependency.
        """

        return f"<Dependency: {self._dependency_string}>"

    def __str__(self) -> str:
        """Returns a string representation of the dependency.

        Returns:
            String representation of the dependency.
        """

        return self._dependency_string

    def __eq__(self, other: Any):
        """Checks if two dependencies are equal.

        Args:
            other: The other dependency to compare to.

        Returns:
            True if the dependencies are equal, False otherwise.
        """

        if not isinstance(other, Dependency):
            return False

        return self._dependency_string == other._dependency_string

    @property
    def name(self) -> str:
        """The name of the dependency."""

        return self._name

    @name.setter
    def name(self, value: str):
        """Sets the name of the dependency."""

        self._name = value

    @property
    def version(self) -> str:
        """The version of the dependency."""

        return self.version

    @version.setter
    def version(self, value: str):
        """Sets the version of the dependency."""

        self.version = value

    @property
    def valid(self) -> bool:
        """Whether the dependency is valid or not."""

        return self._valid

    @valid.setter
    def valid(self, value: bool):
        """Sets the validity of the dependency."""

        self._valid = value

    @classmethod
    def from_string(cls, dependency_string: str) -> Dependency:
        """Creates a Dependency object from a string.

        Args:
            dependency_string: The dependency string.

        Returns:
            Dependency object.
        """

        dependency = cls(dependency_string)
        has_version = DEPENDENCY_VERSION_FILTER.match(dependency_string)
        if has_version:
            dependency.name, dependency.version = list(has_version.groups())
        else:
            dependency.name = dependency_string

        dependency.valid = True

        return dependency
