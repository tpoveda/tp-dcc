"""Rule class for naming conventions."""

from __future__ import annotations

import re
from typing import Any

from tp.libs.templating import consts, validation


class Rule:
    """Class that encapsulates a rule expression."""

    def __init__(
        self,
        name: str,
        creator: str,
        description: str,
        expression: str,
        example_tokens: dict,
    ):
        """Rule constructor.

        Args:
            name (str): rule name.
            creator (str): person who created the rule.
            description (str): description of what the expression represents.
            expression (str): expression to use which con contain tokens using the format, "{token1}_{token2}
            example_tokens (dict): example tokens for the expression.
        """

        self._name = name
        self._creator = creator
        self._description = description
        self._expression = expression
        self._example_tokens = example_tokens

    def __repr__(self) -> str:
        """Overrides __repr__ function to return a custom display name.

        Returns:
            str: rule display name.
        """

        return (
            f"<{self.__class__.__name__}(name={self._name}, expression={self._expression}) object "
            f"at {hex(id(self))}>"
        )

    def __hash__(self) -> int:
        """Overrides __hash__ function to return a hash based on the rule name.

        Returns:
            int: rule hash.
        """

        return hash(self._name)

    def __eq__(self, other: Any) -> bool:
        """Overrides __eq__ function to check whether other object is equal to this one.

        Args:
            other (Any): object instance to check.

        Returns:
            bool: True if given object and current rule are equal; False otherwise.
        """

        if not isinstance(other, Rule):
            return False

        return self.name == other.name

    def __ne__(self, other: Any) -> bool:
        """Overrides __ne__ function to check whether other object is not equal to this one.

        Args:
            other (Any): object instance to check.

        Returns:
            bool: True if given object and current rule are not equal; False otherwise.
        """

        if not isinstance(other, Rule):
            return True

        return self.name != other.name

    @classmethod
    def from_dict(cls, data: dict) -> Rule | None:
        """Creates a new Rule instance from the given JSON serialized dictionary.

        Args:
            data (dict): rule data.

        Returns:
            Rule: newly created rule instance.
        """

        if not validation.can_be_serialized(cls.__name__, data):
            return None

        return cls(
            data["name"],
            data.get("creator", ""),
            data.get("description", ""),
            data.get("expression", ""),
            data.get("exampleFields", {}),
        )

    @property
    def name(self) -> str:
        """Getter method that returns name of the rule.

        Returns:
            str: rule name.
        """

        return self._name

    @property
    def creator(self) -> str:
        """Getter method that returns the creator of the rule.

        Returns:
            str: rule creator.
        """

        return self._creator

    @property
    def description(self) -> str:
        """Getter method that returns the short description of the rule.

        Returns:
            str: rule description.
        """

        return self._description

    @property
    def expression(self) -> str:
        """Getter method that returns the expression of the rule.

        Returns:
            str: rule expression.
        """

        return self._expression

    @expression.setter
    def expression(self, value: str):
        """Setter method that sets the expression of the rule.

        Args:
            value (str): rule expression.
        """

        self._expression = value

    @property
    def example_tokens(self) -> dict[str, str]:
        """Getter method that returns dictionary containing token keys as keys and example token values as values.

        Returns:
            dict[str, str]: example rule tokens.
        """

        return self._example_tokens

    def tokens(self) -> list[str]:
        """Returns list of tokens found within the current expression.

        Returns:
            list[str]: list of token names.
        """

        return re.findall(consts.REGEX_FILTER, self._expression)

    def to_dict(self) -> dict:
        """Returns this rule instance as a valid JSON dictionary.

        Returns:
            dict: rule dictionary.
        """

        data = {
            consts.CLASS_NAME_ATTR: type(self).__name__,
            consts.CLASS_VERSION_ATTR: "1.0",
            "name": self.name,
            "creator": self.creator,
            "description": self.description,
            "expression": self.expression,
            "exampleFields": self.example_tokens,
        }

        return data
