#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains naming token implementation
"""


class KeyValue(object):
	"""
	Class that handles single key/value pair within a naming token. A KeyValue instance can also be set as protected,
	in which ase the value can still change, but it cannot be renamed or deleted.
	"""

	def __init__(self, name, value, protected=False):
		"""
		Constructor.

		:param str name: name of the KeyValue.
		:param str value: value for the keyValue
		:param bool protected: whether KeyValue cannot be deleted or renamed, but it's value can change.
		"""

		super(KeyValue, self).__init__()

		self._name = name
		self._value = value
		self._protected = protected

	def __repr__(self):
		"""
		Overrides __repr__ function to return a custom display name.

		:return: display name.
		:rtype: str
		"""

		return '<{}(name={}, value={}) object at {}>'.format(
			self.__class__.__name__, self._name, self._value, hex(id(self)))

	def __str__(self):
		"""
		Overrides __str__ function to return a string representation of this KeyValue by returning its value as a string.

		:return: KeyValue representation as a string.
		:rtype: str
		"""

		return str(self._value)

	def __hash__(self):
		"""
		Overrides __hash__ function to return a hash based on the KeyValue name.

		:return: key value hash.
		:rtype: str
		"""

		return hash(self._name)

	def __eq__(self, other):
		"""
		Overrides __eq__ function to check whether other object is equal to this one.

		:param object other: object instance to check.
		:return: True if given object and current KeyValue are equal; False otherwise.
		:rtype: bool
		"""

		if not isinstance(other, KeyValue):
			return False

		return self.name == other.name and self.value == other.value

	def __ne__(self, other):
		"""
		Overrides __ne__ function to check whether other object is not equal to this one.

		:param object other: object instance to check.
		:return: True if given object and current KeyValue are not equal; False otherwise.
		:rtype: bool
		"""

		if not isinstance(other, KeyValue):
			return True

		return self.name != other.name and self.value != other.value

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, value):
		if self._protected:
			return
		self._name = value

	@property
	def value(self):
		return self._value

	@value.setter
	def value(self, new_value):
		self._value = new_value

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def serialize(self):
		"""
		Serializes current KeyValue as a dictionary.

		:return: serialized dictionary.
		:rtype: dict
		"""

		return {
			'name': self.name,
			'value': self.value
		}


class Token(object):

	def __init__(self, name, description, permissions, key_values):
		super(Token, self).__init__()

		self._token_values = set(key_values)
		self._name = name
		self._description = description
		self._permissions = {i['name']: i for i in permissions}

	def __repr__(self):
		"""
		Overrides __repr__ function to return a custom display name.

		:return: display name.
		:rtype: str
		"""

		return '<{}(name={}) object at {}>'.format(self.__class__.__name__, self._name, hex(id(self)))

	def __iter__(self):
		"""
		Overrides __iter__ function that allow the iteration of all the token values for this field.

		:return: generator of iterated token values.
		:rtype: collections.Iterator[str]
		"""

	def __len__(self):
		"""
		Overrides __len__ function to return the total number of token values for this field.

		:return: total number of token values.
		:rtype: int
		"""

		return len(self._token_values)

	# =================================================================================================================
	# CLASS METHODS
	# =================================================================================================================

	@classmethod
	def from_dict(cls, data):
		"""
		Creates a new Token instance from the given JSON serialized dictionary.

		:param dict data: token data.
		:return: newly token instance.
		:rtype: Token
		"""

		permissions = {i['name']: i for i in data.get('permissions', list())}
		key_values = [KeyValue(k, v, protected=k in permissions) for k, v in data.get('table', dict()).items()]
		new_token = cls(data['name'], data.get('description', ''), data.get('permissions', list()), key_values)

		return new_token

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def name(self):
		"""
		Returns the name for this token instance.

		:return: token name.
		:rtype: str
		"""

		return self._name

	@property
	def description(self):
		"""
		Returns the description for this token instance.

		:return: token description.
		:rtype: str
		"""

		return self._description
