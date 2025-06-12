from __future__ import annotations

import os
import re
import logging
from typing import Iterator

from .rule import Rule
from .token import Token
from ..python import jsonio

logger = logging.getLogger(__name__)


class NameManager:
    """
    Class that deals with the manipulation of a string based on an expression allowing for a formatted naming
    convention through the usage of rules and tokens:
        * Rule: basic expression like {side}_{area}_{type}.
        * Token: characters within the curly brackets in an expression, which are replaced when the rule is solved.
    """

    REGEX_FILTER = "(?<={)[^}]*"

    def __init__(self, config=None, config_path=None):
        self._original_config: dict | None = config or None
        self._parent_manager: NameManager | None = None
        self._config_path: str = config_path or ""
        self._rules: set[Rule] = set()
        self._tokens: list[Token] = []
        self._name: str = ""
        self._description: str = ""

        if config is not None:
            self._parse_config(config)

    def __repr__(self) -> str:
        """
        Returns a string representation of this instance.

        :return: string representation.
        """

        return f"<{self.__class__.__name__}(name={self._name}, path={self._config_path}) object at {hex(id(self))}>"

    @classmethod
    def from_path(cls, config_path: str) -> NameManager | None:
        """
        Loads the given configuration file and resets this instance with those paths.

        :param str config_path: absolute configuration path to a valid JSON file to load.
        :return: new name manager instance with the paths from the configuration file loaded.
        :rtype: NameManager or None
        """

        if not config_path or not os.path.exists(config_path):
            return None

        config = jsonio.read_file(config_path)
        return cls(config, config_path)

    @property
    def name(self) -> str:
        """
        Getter method taht returns name manager name.

        :return: name manager name.
        """

        return self._name

    @property
    def description(self) -> str:
        """
        Getter method that returns name manager description.

        :return: name manager description.
        """

        return self._description

    @property
    def config_path(self) -> str:
        """
        Getter method that returns path where configuration data was retrieved from.

        :return: absolute file path.
        """

        return self._config_path

    @config_path.setter
    def config_path(self, value: str):
        """
        Setter method that sets path where configuration data is stored.

        :param value: absolute file path.
        """

        self._config_path = value

    @property
    def parent_manager(self) -> NameManager | None:
        """
        Getter method that returns this name manager parent manager.

        :return: parent manager.
        """

        return self._parent_manager

    @parent_manager.setter
    def parent_manager(self, value: NameManager | None):
        """
        Setter method that sets parent manager for this name manager instance.

        :param value: current parent manager.
        """

        self._parent_manager = value

    def refresh(self):
        """
        Loads a fresh version of this manager instance based on the original config paths.
        """

        self._load(self._config_path)

    def rule_count(self, recursive: bool = False) -> int:
        """
        Returns the total count of rules within this manager.

        :param recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
        :return: total rule count.
        """

        count = len(self._rules)
        if recursive and self._parent_manager is not None:
            count += self._parent_manager.rule_count()

        return count

    def iterate_rules(self, recursive: bool = True) -> Iterator[Rule]:
        """
        Generator function that iterates over all current active rules.

        :param recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
        :return: list of active rules.
        """

        visited = set()
        for rule_found in self._rules:
            visited.add(rule_found.name)
            yield rule_found
        if not recursive or not self._parent_manager:
            return
        for parent_rule in self._parent_manager.iterate_rules():
            if parent_rule.name in visited:
                continue
            visited.add(parent_rule.name)
            yield parent_rule

    def rule(self, rule_name: str, recursive: bool = True) -> Rule | None:
        """
        Returns the rule instance for the given name.

        :param rule_name: name of the rule to get instance of.
        :param recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
        :return: found rule instance with given name.
        """

        for rule_found in self.iterate_rules(recursive):
            if rule_found.name == rule_name:
                return rule_found

        return None

    def rule_from_expression(
        self, expression: str, recursive: bool = True
    ) -> Rule | None:
        """
        Given the expression returns the matching rule instance.

        :param expression: expression format.
        :param recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
        :return: found rule instance with matching expression.
        """

        for found_rule in self.iterate_rules(recursive=recursive):
            if found_rule.expression == expression:
                return found_rule

        return None

    def has_rule(self, rule_name: str, recursive: bool = True) -> bool:
        """
        Returns whether a rule with given name exists within this instance.

        :param rule_name: name of the rule to find.
        :param recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
        :return: True if a rule with given name was found; False otherwise.
        """

        return self.rule(rule_name, recursive=recursive) is not None

    def add_rule(
        self,
        name: str,
        expression: str,
        description: str,
        example_fields: dict,
        creator: str | None = None,
        recursive: bool = True,
    ) -> Rule or None:
        """
        Adds the given rule into this manager instance.

        :param name: rule name ot add.
        :param expression: rule expression.
        :param description: rule description.
        :param example_fields: dictionary containing an example KeyValues for the expression fields.
        :param or None creator: optional rule creator name.
        :param recursive: whether the parent manager will be searched as the fallback.
        :return: newly created rule instance.
        """

        if not self.has_rule(name, recursive=recursive):
            logger.debug(f"Adding new rule: {name}")
            new_rule = Rule(name, creator, description, expression, example_fields)
            self._rules.add(new_rule)
            return new_rule

        return None

    def delete_rule(self, rule_to_delete: Rule) -> bool:
        """
        Deletes the given rule instance from this manager instance, ignoring the parent hierarchy.

        :param rule_to_delete: rule instance to delete.
        :return: True if the delete rule operation was successful; False otherwise.
        """

        try:
            self._rules.remove(rule_to_delete)
            logger.debug(f"Rule deleted: {rule_to_delete.name}")
        except ValueError:
            return False

        return True

    def delete_rule_by_name(self, name: str) -> bool:
        """
        Deletes the given rule by name from this manager instance, ignoring the parent hierarchy.

        :param name: name of the rule to delete.
        :return: True if the delete rule operation was successful; False otherwise.
        """

        rule_to_remove = None
        for found_rule in self.iterate_rules(recursive=False):
            if found_rule.name == name:
                rule_to_remove = found_rule
                break

        return self.delete_rule(rule_to_remove)

    def set_rules(self, rules: set[Rule]):
        """
        Overrides current rules with the given ones.

        :param rules: rules to override.
        """

        self._rules = rules

    def update_rules(self, rules: list[Rule]):
        """
        Updates this manager instance rules list with the given rules.

        :param rules: list of rules.
        """

        self._rules.update(set(rules))

    def clear_rules(self):
        """
        Clears all current rules for this manager instance.
        """

        self._rules.clear()

    def token_count(self, recursive: bool = False) -> int:
        """
        Returns the total count of tokens within this manager.

        :param recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
        :return: total token count.
        """

        count = len(self._tokens)
        if recursive and self._parent_manager is not None:
            count += self._parent_manager.token_count()

        return count

    def iterate_tokens(self, recursive: bool = True) -> Iterator[Token]:
        """
        Generator function that iterates over all current active tokens.

        :param recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
        :return: list of active tokens.
        """

        visited = set()
        for token_found in self._tokens:
            visited.add(token_found.name)
            yield token_found
        if not recursive or not self._parent_manager:
            return
        for parent_token in self._parent_manager.iterate_tokens():
            if parent_token.name in visited:
                continue
            visited.add(parent_token.name)
            yield parent_token

    def token(self, name: str, recursive: bool = True) -> Token | None:
        """
        Returns the token instance for the given name.

        :param name: name of the token to find.
        :param recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
        :return: found token instance with given name.
        """

        for found_token in self.iterate_tokens(recursive):
            if found_token.name == name:
                return found_token

        return None

    def has_token(self, name: str, recursive: bool = True) -> bool:
        """
        Checks whether given token exists within this manager instance.

        :param name: name of the token to check.
        :param recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
        :return: True if token with given name already exists within this manager instance; False otherwise.
        """

        return self.token(name, recursive=recursive) is not None

    def add_token(self, name: str, fields: dict[str, str]) -> Token | None:
        """
        Adds the token with given value.

        :param name: name of the token.
        :param fields: fields for the token.
        :return: newly added token instance.
        """

        if self.has_token(name):
            return None

        new_token = Token.from_dict({"name": name, "description": "", "table": fields})
        self._tokens.append(new_token)
        logger.debug(f"Added token: {name}")

        return new_token

    def has_token_key(self, name: str, value: str, recursive: bool = True) -> bool:
        """
        Checks whether a value exists withing the token table.

        :param name: name of the token to check.
        :param value: value to check.
        :param recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
        :return: True if token with given key exists; False otherwise.
        """

        found_token = self.token(name, recursive=recursive) or list()
        return value in found_token

    def set_tokens(self, tokens: set[Token]):
        """
        Overrides current tokens with the given ones.

        :param tokens: set of tokens.
        """

        self._tokens = tokens

    def clear_tokens(self):
        """
        Clears all current tokens from this manager instance.
        """

        self._tokens.clear()

    def expression_from_string(self, name: str) -> str:
        """
        Returns the expression from the name. To resolve an expression, all tokens must exist within this manager
        instance, and we must be able to resolve more than 50% for an expression to be viable.

        :param name: string to resolve.
        :return: manager instance expression. Eg: {name}_{side}_{type}
        :raises ValueError: if is not possible to resolve name to an existing expression.
        :raises ValueError: if is not possible to resolve name because there are too numerous matching expressions.
        """

        expressed_name = list()
        for found_token in self.iterate_tokens():
            token_name = found_token.name
            for key_value in found_token.iterate_key_values():
                if token_name not in expressed_name and key_value.name in name:
                    expressed_name.append(token_name)
                    break

        # we do not have an exact match, so let's find which expression is the most probable
        possibles = set()
        tokenized_length = len(expressed_name)
        for found_rule in self.iterate_rules(recursive=True):
            expression = found_rule.expression
            expression_fields = re.findall(NameManager.REGEX_FILTER, expression)
            total_count = 0
            for token_name in expressed_name:
                if token_name in expression_fields:
                    total_count += 1
            if total_count > tokenized_length / 2:
                possibles.add((expression, total_count))
        if not possibles:
            raise ValueError(
                f"Could not resolve name: {name} to an existing expression!"
            )

        max_possibles = max([i[1] for i in possibles])
        true_possibles = list()
        for possible, total_count in iter(possibles):
            if total_count == max_possibles:
                true_possibles.append(possible)
        if len(true_possibles) > 1:
            raise ValueError(
                f"Could not resolve name {name}, due too many possible expressions"
            )

        return true_possibles[0]

    def resolve(self, rule_name: str, tokens: dict) -> str:
        """
        Resolves the given rule expression using the given tokens as values.

        :param  rule_name: name of the rule.
        :param tokens: token keys and values to set for the rule expression.
        :return: formatted resolved string.
        :raises ValueError: if missing tokens are detected within the given rule.
        """

        expression = self.rule(rule_name).expression
        expression_tokens = set(re.findall(NameManager.REGEX_FILTER, expression))
        new_str = expression
        missing_keys = set()

        for token_found in expression_tokens:
            token_value = tokens.get(token_found)
            if token_value is None:
                missing_keys.add(token_found)
                continue
            token_key_value = self.token(token_found, recursive=True)
            try:
                remapped_value = (
                    token_key_value.value_for_key(token_value) or token_value
                )
            except AttributeError:
                # if the token does not exist, we use the given value
                remapped_value = token_value
            new_str = re.sub("{" + token_found + "}", remapped_value, new_str)

        if missing_keys:
            raise ValueError(
                "Missing expression tokens, rule: {}, tokens: {}".format(
                    rule_name, missing_keys
                )
            )

        return new_str

    def serialize(self) -> dict:
        """
        Serializes current naming manager instance data as a dictionary.

        :return: serialized data.
        """

        return {
            "name": self.name,
            "description": self.description,
            "rules": [rule_found.serialize() for rule_found in self._rules],
            "tokens": [token_found.serialize() for token_found in self._tokens],
        }

    def _load(self, config_path: str):
        """
        Internal function that lads manager instance initial data based on given config path.

        :param config_path: absolute path to a naming manager config file.
        """

        if (
            not config_path
            or not os.path.isfile(config_path)
            or not config_path.endswith(".json")
        ):
            return
        self._config_path = config_path
        self._original_config = jsonio.read_file(config_path)
        self._parse_config(self._original_config)

    def _parse_config(self, config_data: dict):
        """
        Internal function that parses given config dictionary and updates this name manager internal data.

        :param config_data: naming configuration data.
        """

        self._tokens = [
            Token.from_dict(token_map)
            for token_map in config_data.get("tokens", list())
        ]
        self._rules = [
            Rule.from_dict(rule_data) for rule_data in config_data.get("rules", list())
        ]
        self._name = config_data.get("name", "")
