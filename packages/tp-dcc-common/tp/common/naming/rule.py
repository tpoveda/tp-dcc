#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains naming rule implementation
"""

from __future__ import annotations

import re
from typing import List, Dict


class Rule:
    """
    Class that encapsulates a rule expression.
    """

    def __init__(self, name: str, creator: str, description: str, expression, example_tokens: Dict):
        """
        Constructor.

        :param str name: rule name.
        :param str creator: person who created the rule.
        :param str description: description of what the expression represents.
        :param str expression: expression to use which con contain tokens using the format, "{token1}_{token2}
        :param dict example_tokens: example tokens for the expression.
        """

        self._name = name
        self._creator = creator
        self._description = description
        self._expression = expression
        self._example_tokens = example_tokens

    def __repr__(self):
        """
        Overrides __repr__ function to return a custom display name.

        :return: display name.
        :rtype: str
        """

        return f'<{self.__class__.__name__}(name={self._name}, expression={self._expression}) object at {hex(id(self))}>'

    def __hash__(self):
        """
        Overrides __hash__ function to return a hash based on the rule name.

        :return: rule hash.
        :rtype: str
        """

        return hash(self._name)

    def __eq__(self, other):
        """
        Overrides __eq__ function to check whether other object is equal to this one.

        :param object other: object instance to check.
        :return: True if given object and current rule are equal; False otherwise.
        :rtype: bool
        """

        if not isinstance(other, Rule):
            return False

        return self.name == other.name

    def __ne__(self, other):
        """
        Overrides __ne__ function to check whether other object is not equal to this one.

        :param object other: object instance to check.
        :return: True if given object and current rule are not equal; False otherwise.
        :rtype: bool
        """

        if not isinstance(other, Rule):
            return True

        return self.name != other.name

    @classmethod
    def from_dict(cls, data: Dict) -> Rule:
        """
        Creates a new Rule instance from the given JSON serialized dictionary.

        :param Dict data: rule data.
        :return: newly rule instance.
        :rtype: Rule
        """

        return cls(
            data['name'], data.get('creator', ''), data.get('description', ''), data.get('expression', ''),
            data.get('exampleFields')
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def creator(self) -> str:
        return self._creator

    @property
    def description(self) -> str:
        return self._description

    @property
    def expression(self) -> str:
        return self._expression

    @expression.setter
    def expression(self, value: str):
        self._expression = value

    @property
    def example_tokens(self) -> Dict[str, List[str]]:
        return self._example_tokens

    def tokens(self) -> List[str]:
        """
        List of tokens found within the current expression.

        :return: list of token names.
        :rtype: List[str]
        """

        from tp.common.naming import manager
        return re.findall(manager.NameManager.REGEX_FILTER, self._expression)

    def serialize(self) -> Dict[str, str]:
        """
        Returns the raw data for the rule.

        :return: rule data.
        :rtype: Dict[str, str]

        ..code-block:: python
            new_rule = Rule.from_data({
                'name': 'ruleName',
                'description': 'My description',
                'expression': '{side}_{index}'
            }
            data = new_rule.serialize()
            # {
            # 	'name': 'ruleName',
            # 	'description': 'My description',
            # 	'expression': '{side}_{index}'
            # }
        """

        return {
            'name': self.name,
            'creator': self.creator,
            'description': self.description,
            'expression': self.expression,
            'exampleFields': self.example_tokens
        }
