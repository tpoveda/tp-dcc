from __future__ import annotations

import uuid

from tp.common.python import decorators


class Serializable:

    @classmethod
    def as_str(cls, name_only: bool = False) -> str:
        """
        Returns a string representation of the class.

        :param bool name_only: whether to return the name of the class only.
        :return: class as a string.
        """

        return cls.__name__ if name_only else '.'.join([cls.__module__, cls.__name__])

    def __init__(self):
        self.uid = str(uuid.uuid4())

    @decorators.abstractmethod
    def serialize(self) -> dict:
        """
        Serializes current object instance as a JSON valid dictionary.

        :return: serialized data.
        :rtype: dict
        """

        raise NotImplementedError

    @decorators.abstractmethod
    def deserialize(self, data: dict, hashmap: dict | None = None):
        """
        Deserializes instance from data.

        :param dict data: serialized data.
        :param dict or None hashmap: optional hash map.
        """

        raise NotImplementedError
