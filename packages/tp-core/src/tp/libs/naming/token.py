from __future__ import annotations

from typing import Any, Iterator

from . import consts, validation


class KeyValue:
    """Class that handles a single key/value pair within a naming token.
    A KeyValue instance can be set as protected, in which case the value can still be changed, but it cannot be
    renamed or deleted.
    """

    def __init__(self, name: str, value: str, protected: bool = False):
        """KeyValue constructor.

        Args:
            name (str): name of the KeyValue.
            value (str): value for the keyValue
            protected (bool): whether KeyValue cannot be deleted or renamed, but it's value can change.
        """

        super().__init__()

        self._name = name
        self._value = value
        self._protected = protected

    def __repr__(self) -> str:
        """Overrides __repr__ function to return a custom display name.

        Returns:
            str: key value display name.
        """

        return f"<{self.__class__.__name__}(name={self._name}, value={self._value}) object at {hex(id(self))}>"

    def __str__(self) -> str:
        """Overrides __str__ function to return a string representation of this KeyValue by returning its value as a
        string.

        Returns:
            str: KeyValue representation as a string.
        """

        return str(self._value)

    def __hash__(self):
        """Overrides __hash__ function to return a hash based on the KeyValue name.

        Returns:
            str: key value hash.
        """

        return hash(self._name)

    def __eq__(self, other: Any) -> bool:
        """Overrides __eq__ function to check whether other object is equal to this one.

        Args:
            other (Any): object instance to check.

        Returns:
            bool: True if given object and current KeyValue are equal; False otherwise.
        """

        if not isinstance(other, KeyValue):
            return False

        return self.name == other.name and self.value == other.value

    def __ne__(self, other: Any) -> bool:
        """Overrides __ne__ function to check whether other object is not equal to this one.

        Args:
            other (Any): object instance to check.

        Returns:
            bool: True if given object and current KeyValue are not equal; False otherwise.
        """

        if not isinstance(other, KeyValue):
            return True

        return self.name != other.name and self.value != other.value

    @property
    def name(self) -> str:
        """Getter method that returns name of the KeyValue.

        Returns:
            str: KeyValue name.
        """

        return self._name

    @name.setter
    def name(self, value: str):
        """Setter method that sets the name of the KeyValue. Name only can be changed if KeyValue is not protected.

        Args:
            value (str): KeyValue new name.
        """

        if self._protected:
            return
        self._name = value

    @property
    def value(self) -> str:
        """Getter method that returns value of the KeyValue.

        Returns:
            str: KeyValue value.
        """

        return self._value

    @value.setter
    def value(self, new_value: str):
        """Setter method that sets the value of the KeyValue.

        Args:
            new_value (str): KeyValue new value.
        """

        self._value = new_value

    @property
    def protected(self) -> bool:
        """Getter method that returns whether KeyValue can be renamed or deleted.

        Returns:
            bool: True if KeyValue cannot be deleted or renamed; False otherwise.
        """

        return self._protected

    def to_dict(self) -> dict:
        """Converts KeyValue as a dictionary into a valid JSON dictionary.

        :return: serialized dictionary.
        :rtype: dict
        """

        return {"name": self.name, "value": self.value}


class Token:
    """Class that represents a token within a rule (collection of tokens)."""

    def __init__(
        self,
        name: str,
        description: str,
        permissions: dict,
        key_values: list[KeyValue],
        strict: bool = False,
    ):
        """Token constructor.

        Args:
            name (str): name for the token.
            description (str): short description of the token.
            permissions (dict):
            key_values (list[KeyValue]):
            strict (bool): if True, if a rule is token without this token defined, the solve process will fail.
                If False, the token will be removed from the string with an empty string.
        """

        super(Token, self).__init__()

        self._token_values: set[KeyValue] = set(key_values)
        self._name = name
        self._description = description
        self._default: KeyValue | None = None
        self._permissions = {i["name"]: i for i in permissions}
        self._strict = strict

    def __repr__(self) -> str:
        """Overrides __repr__ function to return a custom display name.

        Returns:
            str: display name.
        """

        return f"<{self.__class__.__name__}(name={self._name}) object at {hex(id(self))}>"

    def __iter__(self) -> Iterator[KeyValue]:
        """Overrides __iter__ function that allow the iteration of all the token values for this field.

        Returns:
            Iterator[KeyValue]: generator of iterated token key values.
        """

        return iter(self._token_values)

    def __len__(self) -> int:
        """Overrides __len__ function to return the total number of token values for this field.

        Returns:
            int: total number of token values.
        """

        return len(self._token_values)

    @property
    def name(self) -> str:
        """Getter method that returns the name for this token instance.

        Returns:
            str: token name.
        """

        return self._name

    @property
    def description(self) -> str:
        """Getter method that returns the description for this token instance.

        Returns:
            str: token description.
        """

        return self._description

    @property
    def strict(self) -> bool:
        """Returns whether token can be resolved using an empty string.

        Returns:
            bool: If True, token must need to have a value to be resolved; False otherwise.
        """

        return self._strict

    @property
    def default(self) -> KeyValue | None:
        """Getter method that returns the default KeyValue to use.

        Returns:
            KeyValue or None: default key value.
        """

        if self._default is None and len(self._token_values):
            self._default = list(self._token_values)[0]

        return self._default

    @default.setter
    def default(self, value: KeyValue | None):
        """Setter method that sets the default KeyValue to use.

        Args:
            value (KeyValue or None): default key value.
        """

        self._default = value

    @classmethod
    def from_dict(cls, data: dict) -> Token | None:
        """Creates a new Token instance from the given JSON serialized dictionary.

        Args:
            data (dict): token data.

        Returns:
            Token: newly token instance.
        """

        if not validation.can_be_serialized(cls.__name__, data):
            return None

        permissions = {i["name"]: i for i in data.get("permissions", [])}
        key_values = [
            KeyValue(k, v, protected=k in permissions)
            for k, v in data.get("table", {}).items()
        ]
        new_token = cls(
            data["name"],
            data.get("description", ""),
            data.get("permissions", []),
            key_values,
        )

        return new_token

    def count(self) -> int:
        """Returns the number of KeyValue instances for this token.

        Returns:
            int: total number of KeyValue instances.
        """

        return len(self._token_values)

    def is_required(self) -> bool:
        """Returns whether this token is required for names to be solved.

        Returns:
            bool: True if token is required; False otherwise.
        """

        return self.default is None

    def has_key(self, key: str) -> bool:
        """Returns whether the given Key exists within this token instance.

        Args:
            key (str): Key to check for.

        Returns:
            bool: True if given key exits within this token; False otherwise.
        """

        return self.key_value(key) is not None

    def add(self, name: str, value: str, protected: bool = False) -> KeyValue:
        """Adds a new KeyValue into this token instance.

        Args:
            name (str): name for the KeyValue.
            value (str): new KeyValue value.
            protected (bool): whether this KeyValue instance should be protected from deletion and renaming.

        Returns:
            KeyValue: newly created KeyValue instance.
        """

        unique_name = name
        existing_names = set(
            token_value.name for token_value in self._token_values
        )
        index = 1
        while unique_name in existing_names:
            unique_name = "".join((unique_name, str(index).zfill(1)))

        key_value = KeyValue(unique_name, value, protected=protected)
        self._token_values.add(key_value)

        return key_value

    def update(self, token: Token):
        """Updates/Merges the token KeyValues with this instance KeyValues.

        Args:
            token (Token): token instance to update with this Token.
        """

        self._token_values.update(set(token))

    def remove(self, key: str) -> bool:
        """Removes the KeyValue instance from this token by the given key.

        Args:
            key (str): KeyValue name to remove.

        Returns:
            bool: True if the remove operation was successful; False otherwise.
        """

        found_token = self.key_value(key)
        if found_token is not None and not found_token.protected:
            if self._default == found_token:
                self.default = None
            self._token_values = self._token_values - {found_token}
            return True

        return False

    def solve(self, key: str | None, default_value: str | None = None) -> str:
        """Returns the token value for the key within the token table.

        Args:
            key (str or None): key to search for. If None, default KeyValue will be used.
            default_value (str or None): default value to return when given key does not exist.

        Returns:
            str: value for the matching key.
        """

        # If no key is given, default KeyValue instance will be used.
        if not key:
            token = self.default
            return token.value if token else default_value

        for token in self._token_values:
            if token.name == key:
                return token.value

        return default_value

    def parse(self, value: str) -> str:
        """Returns the token key from the table based on the given token value.

        Args:
            value (str): value to search from the table.

        Returns:
            str: key for the matching value.
        """

        found_token_name: str = ""
        for token in self._token_values:
            if token.value == value:
                found_token_name = token.name
                break

        return found_token_name

    def iterate_key_values(self) -> Iterator[KeyValue]:
        """Generator function that iterates over all KeyValue instances within this token.

        Returns:
            Iterator[KeyValue]: iterated KeyValue instances.
        """

        for key_value in self._token_values:
            yield key_value

    def key_values(self) -> list[KeyValue]:
        """Returns all KeyValue instances within this token.

        Returns:
            list[KeyValue]: list of key values.
        """

        return list(self.iterate_key_values())

    def key_value(self, key: str) -> KeyValue | None:
        """Returns the KeyValue instance for the given key.

        Args:
            key (str): key to get key value of.

        Returns:
            KeyValue or None: KeyValue instance for the matching key.
        """

        for key_value in self._token_values:
            if key_value.name == key:
                return key_value

        return None

    def to_dict(self) -> dict:
        """Converts current token instance into a JSON valid dictionary.

        Returns:
            dict: token serialized data.
        """

        token_values = {
            token_value.name: token_value.value
            for token_value in self._token_values
        }
        permissions = [
            {"name": token_value.name}
            for token_value in self._token_values
            if token_value.protected
        ]
        return {
            consts.CLASS_NAME_ATTR: type(self).__name__,
            consts.CLASS_VERSION_ATTR: "1.0",
            "name": self.name,
            "description": self.description,
            "permissions": permissions,
            "table": token_values,
        }
