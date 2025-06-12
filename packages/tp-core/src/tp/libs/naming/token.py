from __future__ import annotations

from typing import Iterator


class KeyValue:
    """
    Class that handles single key/value pair within a naming token. A KeyValue instance can also be set as protected,
    in which ase the value can still change, but it cannot be renamed or deleted.
    """

    def __init__(self, name: str, value: str, protected: bool = False):
        """
        Constructor.

        :param name: name of the KeyValue.
        :param value: value for the keyValue
        :param protected: whether KeyValue cannot be deleted or renamed, but it's value can change.
        """

        super(KeyValue, self).__init__()

        self._name = name
        self._value = value
        self._protected = protected

    def __repr__(self) -> str:
        """
        Overrides __repr__ function to return a custom display name.

        :return: display name.
        """

        return "<{}(name={}, value={}) object at {}>".format(
            self.__class__.__name__, self._name, self._value, hex(id(self))
        )

    def __str__(self) -> str:
        """
        Overrides __str__ function to return a string representation of this KeyValue by returning
        its value as a string.

        :return: KeyValue representation as a string.
        """

        return str(self._value)

    def __hash__(self):
        """
        Overrides __hash__ function to return a hash based on the KeyValue name.

        :return: key value hash.
        """

        return hash(self._name)

    def __eq__(self, other: KeyValue) -> bool:
        """
        Overrides __eq__ function to check whether other object is equal to this one.

        :param other: object instance to check.
        :return: True if given object and current KeyValue are equal; False otherwise.
        """

        if not isinstance(other, KeyValue):
            return False

        return self.name == other.name and self.value == other.value

    def __ne__(self, other: KeyValue) -> bool:
        """
        Overrides __ne__ function to check whether other object is not equal to this one.

        :param other: object instance to check.
        :return: True if given object and current KeyValue are not equal; False otherwise.
        """

        if not isinstance(other, KeyValue):
            return True

        return self.name != other.name and self.value != other.value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if self._protected:
            return
        self._name = value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str):
        self._value = new_value

    @property
    def protected(self) -> bool:
        return self._protected

    def serialize(self) -> dict:
        """
        Serializes current KeyValue as a dictionary.

        :return: serialized dictionary.
        """

        return {"name": self.name, "value": self.value}


class Token:
    def __init__(
        self, name: str, description: str, permissions: list, key_values: list[KeyValue]
    ):
        super(Token, self).__init__()

        self._token_values = set(key_values)
        self._name = name
        self._description = description
        self._permissions = {i["name"]: i for i in permissions}

    def __repr__(self) -> str:
        """
        Overrides __repr__ function to return a custom display name.

        :return: display name.
        """

        return (
            f"<{self.__class__.__name__}(name={self._name}) object at {hex(id(self))}>"
        )

    def __iter__(self) -> Iterator[KeyValue]:
        """
        Overrides __iter__ function that allow the iteration of all the token values for this field.

        :return: generator of iterated token values.
        """

        return iter(self._token_values)

    def __len__(self) -> int:
        """
        Overrides __len__ function to return the total number of token values for this field.

        :return: total number of token values.
        """

        return len(self._token_values)

    @classmethod
    def from_dict(cls, data: dict) -> Token:
        """
        Creates a new Token instance from the given JSON serialized dictionary.

        :param data: token data.
        :return: newly token instance.
        """

        permissions = {i["name"]: i for i in data.get("permissions", [])}
        key_values = [
            KeyValue(k, v, protected=k in permissions)
            for k, v in data.get("table", dict()).items()
        ]
        new_token = cls(
            data["name"],
            data.get("description", ""),
            data.get("permissions", []),
            key_values,
        )

        return new_token

    @property
    def name(self) -> str:
        """
        Returns the name for this token instance.

        :return: token name.
        """

        return self._name

    @property
    def description(self) -> str:
        """
        Returns the description for this token instance.

        :return: token description.
        """

        return self._description

    def count(self) -> int:
        """
        Returns the number of KeyValue instances for this token.

        :return: total number of KeyValue instances.
        """

        return len(self._token_values)

    def has_key(self, key: str) -> bool:
        """
        Returns whether the given Key exists within this token instance.

        :param key: Key to check for.
        :return: True if given key exits within this token; False otherwise.
        """

        return self.key_value(key) is not None

    def add(self, name: str, value: str, protected: bool = False) -> KeyValue:
        """
        Adds a new KeyValue into this token instance.

        :param name: name for the KeyValue.
        :param value: new KeyValue value.
        :param protected: whether this KeyValue instance should be protected from deletion and renaming.
        :return: newly created KeyValue instance.
        """

        unique_name = name
        existing_names = set(token_value.name for token_value in self._token_values)
        index = 1
        while unique_name in existing_names:
            unique_name = "".join((unique_name, str(index).zfill(1)))

        key_value = KeyValue(unique_name, value, protected=protected)
        self._token_values.add(key_value)

        return key_value

    def update(self, token: Token):
        """
        Updates/Merges the token KeyValues with this instance KeyValues.

        :param token: token instance to update with this Token.
        """

        self._token_values.update(set(token))

    def remove(self, key: str) -> bool:
        """
        Removes the KeyValue instance from this token by the given key.

        :param key: KeyValue name to remove.
        :return: True if the remove operation was successful; False otherwise.
        """

        found_token = self.key_value(key)
        if found_token is not None and not found_token.protected:
            self._token_values = self._token_values - {found_token}
            return True

        return False

    def serialize(self) -> dict:
        """
        Serializes current token into a JSON format dictionary.

        :return: token serialized data.
        """

        token_values = {
            token_value.name: token_value.value for token_value in self._token_values
        }
        permissions = [
            {"name": token_value.name}
            for token_value in self._token_values
            if token_value.protected
        ]
        return {
            "name": self.name,
            "description": self.description,
            "permissions": permissions,
            "table": token_values,
        }

    def value_for_key(self, key) -> str:
        """
        Returns the token value for the key within the token table.

        :param key: key to search for.
        :return: value for the matching key.
        """

        for token in self._token_values:
            if token.name == key:
                return token.value

        return ""

    def key_for_value(self, value: str) -> str:
        """
        Returns the token key from the table based on the given value.

        :param value: value to search from the table.
        :return: key for the matching value.
        """

        for token in self._token_values:
            if token.value == value:
                return token.name

        return ""

    def iterate_key_values(self) -> Iterator[KeyValue]:
        """
        Generator function that iterates over all KeyValue instances within this token.

        :return: iterated KeyValue instances.
        """

        for key_value in self._token_values:
            yield key_value

    def key_value(self, key: str) -> KeyValue | None:
        """
        Returns the KeyValue instance for the given key.

        :param key: key to get value of.
        :return: KeyValue instance for the matching key.
        """

        for key_value in self._token_values:
            if key_value.name == key:
                return key_value

        return None
