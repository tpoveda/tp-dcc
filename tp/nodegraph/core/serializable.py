from __future__ import annotations

import uuid
from abc import ABC, abstractmethod


class Serializable(ABC):
    """
    Class that defines a serializable object.
    """

    def __init__(self):
        super().__init__()

        self.id = str(uuid.uuid4())

    @classmethod
    def as_str(cls, name_only: bool = False):
        """
        Returns the class path as a string.

        :param name_only: bool, Whether to return only the class name.
        :return: str
        """

        return cls.__name__ if name_only else ".".join([cls.__module__, cls.__name__])

    @abstractmethod
    def serialize(self) -> dict:
        """
        Serializes the object into a dictionary.

        :return: dict
        """

        raise NotImplementedError

    @abstractmethod
    def deserialize(self, data: dict):
        """
        Deserializes the object from a dictionary.

        :param data: dict
        :return: Serializable
        """

        raise NotImplementedError
