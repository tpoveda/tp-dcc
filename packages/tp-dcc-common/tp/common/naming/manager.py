#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains naming manager implementation
"""

import re

from tp.common.python import path, jsonio
from tp.common.naming import token, rule


class NameManager(object):
	"""
	Class that deals with the manipulation of a string based on an expression allowing for a formatted naming
	convention through the usage of rules and tokens:
		* Rule: basic expression like {side}_{area}_{type}.
		* Token: characters within the curly brackets in an expression, which are replaced when the rule is solved.
	"""

	REGEX_FILTER = '(?<={)[^}]*'

	def __init__(self, config=None, config_path=None):
		self._original_config = config or None					# type: dict or None
		self._parent_manager = None								# type: NameManager or None
		self._config_path = config_path or ''					# type: str
		self._rules = set()										# type: set[tp.common.naming.rule.Rule]
		self._tokens = list()									# type: list[tp.common.naming.rule.Token]
		self._name = ''
		self._description = ''

		if config is not None:
			self._parse_config(config)

	def __repr__(self):
		return '<{}(name={}, path={}) object at {}>'.format(
			self.__class__.__name__, self._name, self._config_path, hex(id(self)))

	# =================================================================================================================
	# CLASS METHODS
	# =================================================================================================================

	@classmethod
	def from_path(cls, config_path):
		"""
		Loads the given configuration file and resets this instance with those paths.

		:param str config_path: absolute configuration path to a valid JSON file to load.
		:return: new name manager instance with the paths from the configuration file loaded.
		:rtype: NameManager or None
		"""

		if not path.exists(config_path):
			return None

		config = jsonio.read_file(config_path)
		return cls(config, config_path)

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def name(self):
		"""
		Returns name manager name.

		:return: name manager name.
		:rtype: str
		"""

		return self._name

	@property
	def description(self):
		"""
		Returns name manager description.

		:return: name manager description.
		:rtype: str
		"""

		return self._description

	@property
	def parent_manager(self):
		"""
		Returns this name manager parent manager.

		:return: parent manager.
		:rtype: NameManager or None
		"""

		return self._parent_manager

	@parent_manager.setter
	def parent_manager(self, value):
		"""
		Sets parent manager for this name manager instance.

		:param NameManager or None value: current parent manager.
		"""

		self._parent_manager = value

	# =================================================================================================================
	# BASER
	# =================================================================================================================

	def rule_count(self, recursive=False):
		"""
		Returns the total count of rules within this manager.

		:param bool recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
		:return: total rule count.
		:rtype: int
		"""

		count = len(self._rules)
		if recursive and self._parent_manager is not None:
			count += self._parent_manager.rule_count()

		return count

	def iterate_rules(self, recursive=True):
		"""
		Generator function that iterates over all current active rules.

		:param bool recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
		:return: list of active rules.
		:rtype: collections.Iterator[:class:[`tp.common.naming.rule.Rule`]
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

	def rule(self, rule_name, recursive=True):
		"""
		Returns the rule instance for the given name.

		:param str rule_name: name of the rule to get instance of.
		:param bool recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
		:return: found rule instance with given name.
		:rtype: :class:`tp.common.naming.rule.Rule` or None
		"""

		for rule_found in self.iterate_rules(recursive):
			if rule_found.name == rule_name:
				return rule_found

		return None

	def has_rule(self, rule_name, recursive=True):
		"""
		Returns whether a rule with given name exists within this instance.

		:param str rule_name: name of the rule to find.
		:param bool recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
		:return: True if a rule with given name was found; False otherwise.
		:rtype: bool
		"""

		return self.rule(rule_name, recursive=recursive) is not None

	def iterate_tokens(self, recursive=True):
		"""
		Generator function that iterates over all current active tokens.

		:param bool recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
		:return: list of active tokens.
		:rtype: collections.Iterator[:class:[`tp.common.naming.token.Token`]
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

	def token(self, name, recursive=True):
		"""
		Returns the token instance for the given name.

		:param str name: name of the token to find.
		:param bool recursive: whether to recursively search the parent manager hierarchy if the parent is valid.
		:return: found token instance with given name.
		:rtype: :class:`tp.common.token.Token` or None
		"""

		for found_token in self.iterate_tokens(recursive):
			if found_token.name == name:
				return found_token

		return None

	def resolve(self, rule_name, tokens):
		"""
		Resolves the given rule expression using the given tokens as values.

		:param  str rule_name: name of the rule.
		:param dict tokens: token keys and values to set for the rule expression.
		:return: formatted resolved string.
		:rtype: str
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
				remapped_value = token_key_value.value_for_key(token_value) or token_value
			except AttributeError:
				# if the token does not exist, we use the given value
				remapped_value = token_value
			new_str = re.sub('{' + token_found + '}', remapped_value, new_str)

		if missing_keys:
			raise ValueError('Missing expression tokens, rule: {}, tokens: {}'.format(rule_name, missing_keys))

		return new_str

	# =================================================================================================================
	# INTERNAL
	# =================================================================================================================

	def _parse_config(self, config_data):
		"""
		Internal function that parses given config dictionary and updates this name manager internal data.

		:param dict config_data: naming configuration data.
		"""

		self._tokens = [token.Token.from_dict(token_map) for token_map in config_data.get('tokens', list())]
		self._rules = [rule.Rule.from_dict(rule_data) for rule_data in config_data.get('rules', list())]
		self._name = config_data.get('name', '')

