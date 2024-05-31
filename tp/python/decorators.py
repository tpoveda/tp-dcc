from __future__ import annotations

from typing import Callable, Optional, Any, Type


def classproperty(func: Callable) -> ClassProperty:
    """
    Custom decorator that returns a class property object to be used as a decorator.

    :param func: decorated function.
    :return: class property.
    """

    return ClassProperty(func)


# noinspection SpellCheckingInspection
class ClassProperty:
    """
    A decorator that combines the behavior of @classmethod and @property.
    This allows you to define properties that are accessible at the class level.
    """

    def __init__(
            self, fget: Optional[Callable[[Type[Any]], Any]] = None,
            fset: Optional[Callable[[Type[Any], Any], None]] = None):
        """
        Initialize the classproperty with an optional getter and setter.

        :param fget: The getter function.
        :type fget: Optional[Callable[[Type[Any]], Any]]
        :param fset: The setter function.
        :type fset: Optional[Callable[[Type[Any], Any], None]]
        """
        self.fget = fget
        self.fset = fset

    def __get__(self, instance: Any, owner: Type[Any]) -> Any:
        """
        Called to get the attribute of the owner class.

        :param instance: The instance accessing the property (ignored).
        :type instance: object
        :param owner: The owner class accessing the property.
        :type owner: type
        :return: The result of the getter function.
        :raises AttributeError: If the getter function is not defined.
        """

        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget(owner)

    def __set__(self, instance: Any, value: Any):
        """
        Called to set the attribute of the owner class.

        :param instance: The instance setting the property (ignored).
        :type instance: object
        :param value: The value to set.
        :type value: Any
        :raises AttributeError: If the setter function is not defined.
        """

        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(type(instance), value)

    def getter(self, fget: Callable[[Type[Any]], Any]) -> ClassProperty:
        """
        Set the getter function of the property.

        :param fget: The getter function.
        :type fget: Callable[[Type[Any]], Any]
        :return: A new classproperty instance with the updated getter.
        """

        return type(self)(fget, self.fset)

    def setter(self, fset: Callable[[Type[Any], Any], None]) -> ClassProperty:
        """
        Set the setter function of the property.

        :param fset: The setter function.
        :type fset: Callable[[Type[Any], Any], None]
        :return: A new classproperty instance with the updated setter.
        """
        return type(self)(self.fget, fset)
