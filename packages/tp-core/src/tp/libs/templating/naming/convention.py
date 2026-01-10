"""NamingConvention class for managing naming rules and tokens."""

from __future__ import annotations

import logging
import os
import re
import typing
from typing import Iterator, Sequence

from tp.libs.python import yamlio
from tp.libs.templating import consts
from tp.libs.templating.naming import rule, token

if typing.TYPE_CHECKING:
    from tp.libs.templating.naming.rule import Rule
    from tp.libs.templating.naming.token import Token

logger = logging.getLogger(__name__)


class NamingConvention:
    """Class that deals with the manipulation of a string based on an expression allowing for a standard naming
    convention through the usage of rules and tokens:
        * Rule: basic expression like {side}_{area}_{type}.
        * Token: characters within the curly brackets in an expression, which are replaced when the rule is solved.

    Also, a naming convention can define a child-parent relationship that allow child naming conventions to inherit
    the tokens and rules of its parent naming convention.
    """

    def __init__(
        self,
        naming_data: dict | None = None,
        file_path: str = "",
        parent: NamingConvention | None = None,
    ):
        """Naming convention constructor.

        Args:
            naming_data (dict or None): optional naming convention configuration keywords. If given, expected keywords:
                - name (str): name of the naming convention.
                - description (str): description of the naming convention.
                - tokens (list[dict]): list of tokens as dictionaries.
                - rules: (list[dict]): list of rules as dictionaries.
            file_path (str): optional path pointing to a JSON file where naming convention configuration for this
                instance is stored.
            parent (NamingConvention or None): optional parent naming convention.
        """

        self._original_naming_data = naming_data
        self._config_path = file_path

        self._name = ""
        self._description = ""
        self._tokens: list[token.Token] = []
        self._rules: set[Rule] = set()
        self._parent: NamingConvention | None = parent
        self._active_rule: Rule | None = None

        if naming_data is not None:
            self._parse_naming_data(naming_data)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, path={self.config_path}) object at {hex(id(self))}>"

    @classmethod
    def from_path(
        cls, file_path: str, parent: NamingConvention | None = None
    ) -> NamingConvention | None:
        """Loads given naming convention file.

        Args:
            file_path (str): absolute file path pointing to a valid naming convention file.
            parent (NamingConvention or None): optional parent naming convention.

        Returns:
            NamingConvention or NOne: naming convention instance read from given file; None if naming convention file
                does not exist or naming convention does not contain valid data.
        """

        if not os.path.exists(file_path):
            return None

        data = yamlio.read_file(file_path)
        return cls(data, file_path, parent=parent)

    @classmethod
    def flatten(cls, naming_convention: NamingConvention):
        """Function that merges all parent naming convention tokens into given child naming convention.

        Args:
            naming_convention (NamingConvention): naming convention we want to flatten parent naming convention tokens
                of.
        """

        parent_naming_convention = naming_convention.parent
        tokens: dict[str, Token] = {
            _token.name: _token
            for _token in naming_convention.iterate_tokens(recursive=True)
        }
        for _token in parent_naming_convention.iterate_tokens(recursive=True):
            match = tokens.get(_token.name)
            match.update(_token)

    @property
    def name(self) -> str:
        """Getter method that returns the name of the naming convention.

        Returns:
            str: naming convention name.
        """

        return self._name

    @name.setter
    def name(self, value: str):
        """Setter method that sets the name of the naming convention.

        Args:
            value (str): naming convention name.
        """

        self._name = value

    @property
    def description(self) -> str:
        """Getter method that returns the description of the naming convention.

        Returns:
            str: naming convention description.
        """

        return self._description

    @description.setter
    def description(self, value: str):
        """Setter method that sets the description of the naming convention.

        Args:
            value (str): naming convention description.
        """

        self._description = value

    @property
    def config_path(self) -> str:
        """Getter method that returns the absolute file path in disk pointing to a JSON file where naming convention
        configuration is stored.

        Returns:
            str: absolute file path in disk.

        Notes:
            Configuration path can be set as an empty string if Naming instance has been initialized directly
            passing a config dictionary.
        """

        return self._config_path

    @config_path.setter
    def config_path(self, value: str):
        """Setter method that sets the absolute file path in disk pointing to a JSON file where naming convention
        configuration is stored.

        Args:
            value (str): absolute file path in disk.
        """

        self._config_path = value

    @property
    def original_naming_data(self) -> dict:
        """Getter method that returns the original naming data read from naming convention file.

        Returns:
            dict: original naming convention data.
        """

        return self._original_naming_data

    @property
    def parent(self) -> NamingConvention | None:
        """Getter method that returns parent naming convention.

        Returns:
            NamingConvention or None: parent naming convention.
        """

        return self._parent

    @parent.setter
    def parent(self, value: NamingConvention | None):
        """Setter method that sets current parent naming convention.

        Args:
            value (NamingConvention or None): parent naming convention.
        """

        self._parent = value

    def active_rule(self) -> Rule | None:
        """Returns active rule for this naming convention.

        Returns:
            Rule or None: active rule instance.
        """

        return self._active_rule

    def set_active_rule(
        self, active_rule: Rule | None, recursive: bool = True
    ) -> bool:
        """Sets active rule.

        Args:
            active_rule (Rule or None): active rule instance.
            recursive (bool): whether to check parent naming convention rules.

        Returns:
            bool: True if active rule was set; False otherwise.
        """

        if active_rule is None:
            self._active_rule = None
            return True

        if not self.has_rule(active_rule.name, recursive=recursive):
            return False

        self._active_rule = active_rule

        return True

    def set_active_rule_by_name(
        self, name: str, recursive: bool = True
    ) -> bool:
        """Sets active rule by name.

        Args:
            name (str): active rule name.
            recursive (bool): whether to check parent naming convention rules.

        Returns:
            bool: True if active rule was set; False otherwise.
        """

        if not self.has_rule(name, recursive=recursive):
            return False

        self._active_rule = self.rule(name, recursive=recursive)

        return True

    def has_rule(self, name: str, recursive: bool = True) -> bool:
        """Returns whether naming convention contains a rule with given name.

        Args:
            name (str): rule name.
            recursive (bool): whether to check parent naming convention rules.

        Returns:
            bool: True if rule with given name exists; False otherwise.
        """

        return self.rule(name, recursive=recursive) is not None

    def rule(self, name: str, recursive: bool = True) -> Rule | None:
        """Returns the rule instance with given name.

        Args:
            name (str): rule name.
            recursive (bool): whether to check parent naming convention rules.

        Returns:
            Rule or None: rule instance with given name or None if rule with given name does not exist.
        """

        found_rule: Rule | None = None
        for _rule in self.iterate_rules(recursive=recursive):
            if _rule.name == name:
                found_rule = _rule
                break

        return found_rule

    def rule_from_expression(
        self, expression: str, recursive: bool = True
    ) -> Rule | None:
        """Returns the rule that matches given expression.

        Args:
            expression (str): expression to check (i.e: "{test}_{expression}".
            recursive (bool): whether to check parent naming convention rules.

        Returns:
            Rule or None: found rule that matches given expression.
        """

        found_rule: Rule | None = None
        for _rule in self.iterate_rules(recursive=recursive):
            if _rule.expression == expression:
                found_rule = _rule
                break

        return found_rule

    def add_rule(
        self,
        name: str,
        expression: str,
        example_tokens: dict[str, str] | None = None,
        description: str | None = None,
        creator: str | None = None,
        set_as_active: bool = False,
        recursive: bool = True,
    ) -> Rule | None:
        """Adds a new rule into the naming convention.

        Args:
            name (str): rule name to add.
            expression (str): new rule expression.
            example_tokens (dict): dictionary containing an example KeyValue for the expression tokens.
            description (str or None): rule description.
            creator (str or None): optional rule creator name.
            set_as_active (bool): whether to set rule as new active rule.
            recursive (bool): Whether to check rule existing within parent naming convention.

        Returns:
            Rule or None: newly added rule.
        """

        if self.has_rule(name, recursive=recursive):
            return None

        logger.debug(f"Adding new rule: {name}")
        new_rule = rule.Rule(
            name=name,
            creator=creator,
            description=description,
            expression=expression,
            example_tokens=example_tokens or {},
        )
        self._rules.add(new_rule)

        if set_as_active:
            self.set_active_rule(new_rule)

        return new_rule

    def add_rule_from_tokens(
        self,
        name: str,
        *tokens: str,
        example_tokens: dict[str, str] | None = None,
        description: str | None = None,
        creator: str | None = None,
        set_as_active: bool = False,
        recursive: bool = True,
    ):
        """Adds a new rule into the naming convention from given tokens.

        Args:
            name (str): rule name to add.
            tokens (str): new rule tokens.
            example_tokens (dict): dictionary containing an example KeyValue for the expression tokens.
            description (str or None): rule description.
            creator (str or None): optional rule creator name.
            set_as_active (bool): whether to set rule as new active rule.
            recursive (bool): Whether to check rule existing within parent naming convention.

        Returns:
            Rule or None: newly added rule.
        """

        expression = ""
        for i, _token in enumerate(tokens):
            expression += "_{" + _token + "}" if i > 0 else "{" + _token + "}"

        return self.add_rule(
            name,
            expression,
            example_tokens=example_tokens,
            description=description,
            creator=creator,
            set_as_active=set_as_active,
            recursive=recursive,
        )

    def set_rules(self, rules: Sequence[Rule]):
        """Sets the rules for this naming convention.

        Args:
            rules (Sequence[Rule]): rules to set.
        """

        self._rules = set(rules)

    def update_rules(self, rules: Sequence[Rule]):
        """Updates current naming convention rules with the given ones.

        Args:
            rules Sequence[Rule]: rules to update current ones from.
        """

        self._rules.update(set(rules))

    def iterate_rules(self, recursive: bool = True) -> Iterator[Rule]:
        """Generator function that yields the currently active rules.

        Args:
            recursive (bool): whether to iterate parent naming convention rules recursively.

        Returns:
            Iterator[Rule]: iterated rules.
        """

        visited: set[str] = set()
        for found_rule in self._rules:
            visited.add(found_rule.name)
            yield found_rule
        if not recursive or not self._parent:
            return
        for parent_rule in self._parent.iterate_rules(recursive=recursive):
            if parent_rule.name in visited:
                continue
            visited.add(parent_rule.name)
            yield parent_rule

    def rules(self, recursive: bool = True) -> list[Rule]:
        """Returns all the currently active rules.

        Args:
            recursive (bool): whether to iterate parent naming convention rules recursively.

        Returns:
            Iterator[Rule]: list of rules.
        """

        return list(self.iterate_rules(recursive=recursive))

    def rule_count(self, recursive: bool = False) -> int:
        """Returns the total number of rules defined within this naming convention.

        Args:
            recursive (bool): whether to iterate parent naming convention rules recursively.

        Returns:
            int: total number of rules.
        """

        count = len(self._rules)
        if recursive and self._parent is not None:
            count += self._parent.rule_count(recursive=recursive)

        return count

    def delete_rule(self, rule_to_delete: Rule) -> bool:
        """Deletes the given rule from the naming convention.

        Args:
            rule_to_delete (Rule): rule to delete.

        Returns:
            bool: True if the rule was deleted successfully; False otherwise.
        """

        try:
            self._rules.remove(rule_to_delete)
            logger.debug(f"Rule deleted: {rule_to_delete.name}")
        except ValueError:
            return False

        return True

    def delete_rule_by_name(self, name: str) -> bool:
        """Deletes the rule with given name from the naming convention.

        Args:
            name (str): name of the rule to delete.

        Returns:
            bool: True if the rule was deleted successfully; False otherwise.
        """

        rule_to_remove: Rule | None = None
        for found_rule in self.iterate_rules(recursive=False):
            if found_rule.name == name:
                rule_to_remove = found_rule
                break
        if rule_to_remove is None:
            return False

        return self.delete_rule(rule_to_remove)

    def clear_rules(self):
        """Clears all current rules from the naming convention."""

        self._rules.clear()

    def has_token(self, name: str, recursive: bool = True) -> bool:
        """Returns whether naming convention contains a token with given name.

        Args:
            name (str): token name.
            recursive (bool): whether to check parent naming convention tokens.

        Returns:
            bool: True if token with given name exists; False otherwise.
        """

        return self.token(name, recursive=recursive) is not None

    def has_field_key(self, name: str, value: str, recursive: bool = True):
        """Returns whether given value exists within KeyValue table of the token with given name.

        Args:
            name (str): toke nanem.
            value (str): token table value to check existence of.
            recursive (bool): whether to check parent naming convention tokens.

        Returns:
            bool: True if value exists within KeyValue table of the token; False otherwise.
        """

        found_token = self.token(name, recursive=recursive)
        return True if found_token.parse(value) else False

    def token(self, name: str, recursive: bool = True) -> Token | None:
        """Returns the token instance for the given name.

        Args:
            name (str): token name.
            recursive (bool): whether to check parent naming convention tokens.

        Returns:
            Token or None: token instance with given name or None if token with given name does not exist.
        """

        found_token: Token | None = None
        for _token in self.iterate_tokens(recursive=recursive):
            if _token.name == name:
                found_token = _token
                break

        return found_token

    def add_token(
        self,
        name: str,
        description: str = "",
        recursive: bool = True,
        padding: int = 0,
        **key_values,
    ) -> Token | None:
        """Adds a new token into the naming convention.

        Args:
            name (str): token name to add.
            description (str): optional token description.
            recursive (bool): Whether to check token existing within parent naming convention.
            padding (int): number of digits for zero-padding numeric values. If 0 (default), no padding is applied.
                For example, padding=3 would format value "1" as "001", "42" as "042", etc.

        Returns:
            Token or None: newly added token.
        """

        if self.has_token(name, recursive=recursive):
            return None

        logger.debug(f"Adding new token: {name}")
        new_token = token.Token.from_dict(
            {"name": name, "description": description, "padding": padding}
        )
        for k, v in key_values.items():
            if k == "default":
                new_token.default = token.KeyValue(k, v)
                continue
            new_token.add(k, v)
        self._tokens.append(new_token)

        return new_token

    def set_tokens(self, tokens: Sequence[Token]):
        """Sets the tokens for this naming convention.

        Args:
            tokens (Sequence[Token]): tokens to set.
        """

        self._tokens = list(tokens)

    def iterate_tokens(self, recursive: bool = True) -> Iterator[Token]:
        """Generator function that yields the currently active tokens.

        Args:
            recursive (bool): whether to iterate parent naming convention tokens recursively.

        Returns:
            Iterator[Token]: iterated tokens.
        """

        visited: set[str] = set()
        for found_token in self._tokens:
            visited.add(found_token.name)
            yield found_token
        if not recursive or not self._parent:
            return
        for parent_token in self._parent.iterate_tokens(recursive=recursive):
            if parent_token.name in visited:
                continue
            visited.add(parent_token.name)
            yield parent_token

    def tokens(self, recursive: bool = True) -> list[Token]:
        """Returns all the currently active tokens.

        Args:
            recursive (bool): whether to iterate parent naming convention tokens recursively.

        Returns:
            Iterator[Token]: list of tokens.
        """

        return list(self.iterate_tokens(recursive=recursive))

    def token_count(self, recursive: bool = False) -> int:
        """Returns the total number of tokens defined within this naming convention.

        Args:
            recursive (bool): whether to iterate parent naming convention tokens recursively.

        Returns:
            int: total number of tokens.
        """

        count = len(self._tokens)
        if recursive and self._parent is not None:
            count += self._parent.token_count(recursive=recursive)

        return count

    def delete_token(self, token_to_delete: Token) -> bool:
        """Deletes the given token from the naming convention.

        Args:
            token_to_delete (Token): token to delete.

        Returns:
            bool: T rue if the token was deleted successfully; False otherwise.
        """

        try:
            self._tokens.remove(token_to_delete)
            logger.debug(f"Token deleted: {token_to_delete.name}")
        except ValueError:
            return False

        return True

    def delete_token_by_name(self, name: str) -> bool:
        """Deletes the token with given name from the naming convention.

        Args:
            name (str): name of the token to delete.

        Returns:
            bool: True if the token was deleted successfully; False otherwise.
        """

        token_to_remove: Token | None = None
        for found_token in self.iterate_tokens(recursive=False):
            if found_token.name == name:
                token_to_remove = found_token
                break
        if token_to_remove is None:
            return False

        return self.delete_token(token_to_remove)

    def clear_tokens(self):
        """Clears all current tokens from the naming convention."""

        self._tokens.clear()

    def solve(
        self,
        *args,
        rule_name: str | None = None,
        recursive: bool = True,
        **key_values,
    ) -> str:
        """Resolves the given rule expression using the given tokens as values.
        Each token value will be converted using naming convention token table. If a token or a token key-value
        does not exist, given value will be used instead.

        Args:
            rule_name (str or None): optional name of the rule to resolve. If None, active rule will be used to solve
                the name.
            recursive (bool): whether solve will be used taking into consideration rules and tokens of the parent
                naming convention.

        Returns:
            str: resolved rule expression.

        Raises:
            AttributeError: if rule with given name does not exist.
            RuntimeError: if no active rule set to solve name with.
            RuntimeError: if the total amount of rule tokens and the total amount of rule expression tokens do not
                match.
        """

        def _surround_token_expression(_token_value: str) -> str:
            """Internal function that given a token value, returns the expression format for the token.

            Args:
                _token_value (str): token value to surround with the expression format.

            Returns:
                str: field value surrounded by "{}".
            """

            return "{" + _token_value + "}"

        if rule_name:
            try:
                expression = self.rule(
                    rule_name, recursive=recursive
                ).expression
            except AttributeError:
                raise ValueError(
                    f'Rule "{rule_name}" is not a valid registered rule!'
                )
        else:
            active_rule = self.active_rule()
            if not active_rule:
                raise RuntimeError("No active rule set to solve name with!")
            expression = (
                active_rule.expression if active_rule is not None else None
            )
            if not expression:
                raise RuntimeError(
                    f"No expression to solve name with using rule: {active_rule}!"
                )

        expression_tokens = re.findall(consts.REGEX_FILTER, expression)
        solved_str = expression
        missing_keys: set[str] = set()

        i = 0
        for token_name in expression_tokens:
            token_value = key_values.get(token_name)
            found_token = self.token(token_name, recursive=True)
            token_default_value = (
                found_token.default.value
                if found_token and found_token.default
                else None
            )
            if token_value is None:
                # If the token is required, user must pass a valid key for it and the resolve process will fail.
                if found_token.is_required():
                    # We try to get token value from given arguments
                    try:
                        remapped_value = args[i]
                        pattern = _surround_token_expression(token_name)
                        i += 1
                    except IndexError:
                        # If token is not strict we just replace it using an empty string.
                        if not found_token.strict:
                            remapped_value = "_"
                            pattern = consts.REGEX_TOKEN_RESOLVER.format(
                                token=_surround_token_expression(token_name)
                            )
                        else:
                            missing_keys.add(token_name)
                            continue
                else:
                    # Otherwise, the token will be solved using an empty string.
                    if token_default_value:
                        remapped_value = token_default_value
                        pattern = _surround_token_expression(token_name)
                    else:
                        remapped_value = "_"
                        pattern = consts.REGEX_TOKEN_RESOLVER.format(
                            token=_surround_token_expression(token_name)
                        )
            else:
                try:
                    remapped_value = found_token.solve(
                        token_value,
                        default_value=token_default_value or token_value,
                    )
                except AttributeError:
                    # If the token does not exist, we use the given value.
                    remapped_value = token_value
                if not remapped_value:
                    # If no valid value can be retrieved from token, we just solved it using an empty string.
                    pattern = consts.REGEX_TOKEN_RESOLVER.format(
                        token=_surround_token_expression(token_name)
                    )
                    remapped_value = "_"
                else:
                    pattern = _surround_token_expression(token_name)

            solved_str = re.sub(pattern, remapped_value, solved_str)

        if missing_keys:
            raise ValueError(
                f"Missing Expression tokens, rule: {rule_name}, missing tokens: {missing_keys}"
            )

        return solved_str

    def parse_by_rule(
        self, rule_to_use: Rule | str, solved_name: str
    ) -> dict[str, str]:
        """Parses given solved name using the given rule from the naming convention.

        Args:
            rule_to_use (Rule): rule to use to parse the given solved name.
            solved_name (str): solved name.

        Returns:
            dict[str, str]: dictionary containing each one of the solved name token keys and solved values.

        Raises:
            ValueError: if given rule does not exist in naming convention.
            ValueError: if the amount of tokens does not match the expression.
        """

        result: dict[str, str] = {}

        if isinstance(rule_to_use, str):
            rule_to_use = self.rule(rule_to_use)
        if rule_to_use is None:
            raise ValueError(
                f"Rule {rule_to_use} does not exist in naming convention."
            )

        expression = rule_to_use.expression
        expression_tokens = re.findall(consts.REGEX_FILTER, expression)
        split_name = solved_name.split("_")

        if len(split_name) != len(expression_tokens):
            raise ValueError(
                f"Could not resolve name: {solved_name}, because the amount of tokens does not match the expression."
            )

        for i, token_name in enumerate(expression_tokens):
            token_value = split_name[i]
            found_token = self.token(token_name, recursive=True)
            if found_token is None:
                continue
            if found_token.is_required():
                result[token_name] = token_value
                continue
            token_key = found_token.parse(token_value)
            result[token_name] = token_key or token_value

        return result

    def parse_by_active_rule(self, solved_name: str) -> dict[str, str]:
        """Parses given solved name using current naming convention active rule.

        Args:
            solved_name (str): solved name.

        Returns:
            dict[str, str]: dictionary containing each one of the solved name token keys and solved values.
        """

        active_rule = self.active_rule()
        if active_rule is None:
            return {}

        return self.parse_by_rule(active_rule, solved_name)

    def parse(
        self, solved_name: str, recursive: bool = True
    ) -> dict[str, str]:
        """Parses given solved name taking into account all available rules within the naming convention.

        Args:
            solved_name (str): resolved name to get expression from.
            recursive (bool): whether to iterate parent naming convention tokens recursively.

        Returns:
            dict[str, str]: dictionary containing each one of the solved name token keys and solved values.

        Raises:
            ValueError: if expression to resolve given name cannot be found.
        """

        # We do not have an exact match, so let's find which expression is the most probable
        possibles = self._filter_possible_expressions(
            solved_name, recursive=recursive
        )
        if len(possibles) > 1:
            raise ValueError(
                f"Could not resolve name: {solved_name}, because too many possible expressions found."
            )

        _, _, _rule = possibles[0]
        return self.parse_by_rule(_rule, solved_name)

    def expression_from_string(
        self, solved_name: str, recursive: bool = True
    ) -> str:
        """Returns the expression used to resolve the given name.

        Args:
            solved_name (str): resolved name to get expression from.
            recursive (bool): whether to iterate parent naming convention tokens recursively.

        Returns:
            str: naming convention expression.

        Raises:
            ValueError: if multiple expressions are found that can resolve the given name.

        Notes:
            To resolve a name, all tokens must exist within the naming convention, and we must be able to resolve more
            than 50% for an expression for it to be viable.
        """

        # We do not have an exact match, so let's find which expression is the most probable
        possibles = self._filter_possible_expressions(
            solved_name, recursive=recursive
        )
        if len(possibles) > 1:
            raise ValueError(
                f"Could not resolve name: {solved_name}, because too many possible expressions found."
            )

        return possibles[0][0]

    def to_dict(self) -> dict:
        """Returns this naming convention instance as a valid JSON dictionary.

        Returns:
            dict: naming convention dictionary.
        """

        active_rule = self.active_rule()
        data = {
            consts.CLASS_NAME_ATTR: type(self).__name__,
            consts.CLASS_VERSION_ATTR: "1.0",
            "name": self.name,
            "description": self.description,
            "rules": [_rule.to_dict() for _rule in self._rules],
            "tokens": [_token.to_dict() for _token in self._tokens],
        }
        if active_rule is not None:
            data["active_rule"] = active_rule.name

        return data

    def save_to_file(self, file_path: str) -> bool:
        """Saves naming convention into a file in disk.

        Args:
            file_path (str): file path to store naming convention into.

        Returns:
             bool: True if naming convention was saved to file successfully; False otherwise.
        """

        try:
            yamlio.write_to_file(self.to_dict(), file_path)
        except Exception as err:
            logger.exception(
                f'Something went wrong while saving naming convention file into "{file_path}": {err}',
                exc_info=True,
            )
            return False

        return True

    def refresh(self, file_path: str | None = None):
        """Loads a fresh version of the naming convention based on the given naming convention file path.
        If no file path is given, original naming convention file path will be used.

        Args:
            file_path (str or None): valid naming convention file path to load.
        """

        file_path = (
            file_path
            if file_path and os.path.isfile(file_path)
            else self._config_path
        )
        if not os.path.exists(file_path) or not file_path.endswith(
            f".{consts.NAMING_CONVENTION_EXTENSION}"
        ):
            logger.warning(
                f'Naming Convention file path "{file_path}" is not valid!'
            )
            return

        self._config_path = file_path
        self._original_naming_data = yamlio.read_file(file_path)
        self._parse_naming_data(self._original_naming_data)

    def changes(
        self, target: NamingConvention | None = None
    ) -> NamingConventionChanges | None:
        """Returns a new naming convention instance that contains the different between this naming convention and the
        given one.

        Args:
            target (NamingConvention or None): naming convention to compute diff against. If not given, current parent
                naming convention will be used.

        Returns:
            NamingConventionChanges or None: naming convention changes instance.
        """

        target = target or self.parent
        if target is None:
            logger.warning(
                "Target naming convention must be given. Aborting diff process."
            )
            return None
        if target == self:
            logger.warning(
                "Target and Source naming conventions cannot be the same. Aborting diff process."
            )
            return None

        changes = NamingConventionChanges(self, target)
        changes.compute()

        return changes

    def _filter_possible_expressions(
        self, solved_name: str, recursive: bool = True
    ) -> list[tuple[str, int, Rule]]:
        """Internal function that filter possible expressions based on given solved names and current rules.

        Args:
            solved_name (str): resolved name to get expression from.
            recursive (bool): whether to iterate parent naming convention tokens recursively.

        Returns:
            list[tuple[str, int, Rule]]: set with the expression, the total token matches in given solved name and the
                rule that token is linked to.

        Raises:
            ValueError: if expression to resolve given name cannot be found.
        """

        expressed_name: list[str] = []
        for _token in self.iterate_tokens(recursive=recursive):
            token_name = _token.name
            for key_value in _token.key_values():
                if (
                    token_name not in expressed_name
                    and key_value.value in solved_name
                ):
                    expressed_name.append(token_name)
                    break

        # We do not have an exact match, so let's find which expression is the most probable
        possibles: set[tuple[str, int, Rule]] = set()
        tokenized_length = len(expressed_name)
        for _rule in self.iterate_rules(recursive=True):
            expression = _rule.expression
            expression_tokens = re.findall(consts.REGEX_FILTER, expression)
            total_count = 0
            for token_name in expressed_name:
                if token_name in expression_tokens:
                    total_count += 1
            if total_count > tokenized_length / 2:
                possibles.add((expression, total_count, _rule))

        if not possibles:
            raise ValueError(
                f"Could not resolved name: {solved_name} to an existing expression."
            )

        # Filter out the possibles down to just the best resolved.
        max_possible = max([i[1] for i in possibles])
        true_possibles: list[tuple[str, int, Rule]] = []
        for i, (possible, token_count, _rule) in enumerate(iter(possibles)):
            if token_count == max_possible:
                true_possibles.append(list(possibles)[i])

        return true_possibles

    def _parse_naming_data(self, naming_data: dict):
        """Internal function that parses given config dictionary and updates this name manager internal data.

        Args:
            naming_data (dict): naming configuration data.
        """

        self._tokens = [
            token.Token.from_dict(token_map)
            for token_map in naming_data.get("tokens", [])
        ]
        self._rules = set(
            [
                rule.Rule.from_dict(rule_data)
                for rule_data in naming_data.get("rules", [])
            ]
        )
        self._name = naming_data.get("name", "")
        self._description = naming_data.get("description", "")
        active_rule_name = naming_data.get("active_rule")
        if active_rule_name:
            self.set_active_rule(self.rule(active_rule_name))


class NamingConventionChanges:
    """Helper class that allows to create a new naming convention based on the changes in the source naming convention
    and the target naming convention.
    """

    def __init__(self, source: NamingConvention, target: NamingConvention):
        """NamingConventionChanges constructor.

        Args:
            source (NamingConvention): source naming convention where its local rules/token are diffed against the
                given target naming convention.
            target (NamingConvention): naming convention used to check changes for the given source naming convention.
        """

        self._source = source
        self._target = target
        self._diff = NamingConvention()

    @property
    def diff(self) -> NamingConvention:
        """Getter method that returns diff naming convention.

        Returns:
            NamingConvention: dif naming convention instance.
        """

        return self._diff

    def has_changes(self) -> bool:
        """Returns whether there are any changes made on the source naming convention compared to the target naming
        convention.

        Returns:
            bool: True if source and target naming conventions are different; False otherwise.
        """

        return (
            self._diff.rule_count(recursive=False) != 0
            and self._diff.token_count() != 0
        )

    def to_dict(self) -> dict:
        """Returns this naming convention instance as a valid JSON dictionary.

        Returns:
            dict: naming convention dictionary.
        """

        return self._diff.to_dict()

    def compute(self) -> NamingConvention:
        """Computes the diff naming convention between the given source and target naming conventions and returns it.

        Returns:
            NamingConvention: diff naming convention.
        """

        diff_rules: list[Rule] = []
        diff_tokens: list[Token] = []
        target_rules: dict[str, Rule] = {
            _rule.name: _rule
            for _rule in self._target.iterate_rules(recursive=True)
        }
        target_tokens: dict[str, Token] = {
            _token.name: _token
            for _token in self._target.iterate_tokens(recursive=True)
        }

        for source_rule in self._source.iterate_rules(recursive=False):
            target_rule = target_rules.get(source_rule.name)
            if (
                target_rule is None
                or source_rule.expression == target_rule.expression
            ):
                continue
            diff_rules.append(source_rule)

        for source_token in self._source.iterate_tokens(recursive=False):
            target_token = target_tokens.get(source_token.name)
            if target_token is None:
                continue
            source_key_values = {
                key_value.name: key_value.value
                for key_value in source_token.iterate_key_values()
            }
            target_key_values = {
                key_value.name: key_value.value
                for key_value in target_token.iterate_key_values()
            }
            if source_key_values == target_key_values:
                continue
            diff_tokens.append(source_token)

        self._diff.set_tokens(diff_tokens)
        self._diff.set_rules(diff_rules)
        self._diff.name = self._source.name
        self._diff.description = self._source.description
        self._diff.config_path = self._source.config_path

        return self._diff
