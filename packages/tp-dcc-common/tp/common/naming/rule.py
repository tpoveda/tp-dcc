#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains naming rule implementation
"""


class Rule(object):
	"""
	Class that encapsulates a rule expression.
	"""

	def __init__(self, name, creator, description, expression, example_fields):
		"""
		Constructor.

		:param str name: rule name.
		:param str creator: person who created the rule.
		:param str description: description of what the expression represents.
		:param str expression: expression to use which con contain tokens using the format, "{token1}_{token2}
		:param dict example_fields: example fields for the expression.
		"""

		self._name = name
		self._creator = creator
		self._description = description
		self._expression = expression
		self._example_fields = example_fields

	def __repr__(self):
		"""
		Overrides __repr__ function to return a custom display name.

		:return: display name.
		:rtype: str
		"""

		return '<{}(name={}, expression={}) object at {}>'.format(
			self.__class__.__name__, self._name, self._expression, hex(id(self)))

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

	# =================================================================================================================
	# CLASS METHODS
	# =================================================================================================================

	@classmethod
	def from_dict(cls, data):
		"""
		Creates a new Rule instance from the given JSON serialized dictionary.

		:param dict data: rule data.
		:return: newly rule instance.
		:rtype: Rule
		"""

		return cls(
			data['name'], data.get('creator', ''), data.get('description', ''), data.get('expression', ''),
			data.get('exampleFields')
		)

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def name(self):
		return self._name

	@property
	def creator(self):
		return self._creator

	@property
	def description(self):
		return self._description

	@property
	def expression(self):
		return self._expression

	@property
	def example_fields(self):
		return self._example_fields
