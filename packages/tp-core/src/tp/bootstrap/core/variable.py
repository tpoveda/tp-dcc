from __future__ import annotations

import os
import re

from . import constants


class Variable:
    """Represents an environment variable in a package environment."""

    def __init__(self, key: str, values: list[str]):
        """Initializes the variable.

        Args:
            key: The key of the variable.
            values: The values of the variable.
        """

        self._key = key
        self._values = values
        self._original_values = values.copy()
        env_var = os.getenv(key)
        if env_var:
            self._values.extend([i for i in env_var.split(os.pathsep) if i])

    @property
    def values(self) -> list[str]:
        """The values of the variable."""

        return self._values

    def __str__(self) -> str:
        """Returns the string representation of the variable."""

        return (
            os.pathsep.join(self._values) if len(self._values) > 1 else self._values[0]
        )

    def split(self, separator: str) -> list[str]:
        """Splits the variable values by the given separator.

        Args:
            separator: The separator to split the values by.

        Returns:
            The list of split values.
        """

        return str(self).split(separator)

    def dependencies(self) -> set[str]:
        """Returns the dependencies of the variable.

        Returns:
            A set of dependencies found in the variable values.
        """

        results = set()

        for i in self._values:
            results.update(re.findall(constants.PACKAGE_DEPENDENCIES_FILTER, i))

        return results

    def solve(self, tokens: dict[str, str]) -> list[str]:
        """Solves the variable values by replacing the tokens with their values.

        Args:
            tokens: The tokens to replace in the variable values.

        Returns:
            The solved variable values.
        """

        solved: list[str] = []
        for value in self._values:
            for token, replacement in tokens.items():
                value = value.replace(f"{{{token}}}", replacement)
            solved.append(value)

        self._values = solved

        return solved

    def reset(self):
        """Resets the variable values to their original state (before solve/modify)."""

        self._values = self._original_values.copy()
