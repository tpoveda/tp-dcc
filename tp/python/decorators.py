from __future__ import annotations

from tp.core.consts import ENV_VAR, EnvironmentMode

import os
import abc
import logging
from functools import wraps
from typing import Callable, Optional, Type, Any


def classproperty(func: Callable) -> ClassProperty:
    """
    Custom decorator that returns a class property object to be used as a decorator.

    :param func: decorated function.
    :return: class property.
    """

    return ClassProperty(func)


def log_arguments(level: int = logging.DEBUG):
    """
    Decorator that logs the arguments and return value of a function.

    :param level: logging level to use.
    """

    is_dev_environment = (
        os.getenv(ENV_VAR, EnvironmentMode.Production.value).lower()
        == EnvironmentMode.Development.value
    )

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if is_dev_environment:
                logger = logging.getLogger(func.__module__)
                level_to_use = level if logger.isEnabledFor(level) else logging.DEBUG
                logger.log(
                    level_to_use,
                    f"Calling {func.__name__} with args: {args} and kwargs: {kwargs}",
                    stacklevel=2,
                )

            result = func(*args, **kwargs)

            if is_dev_environment:
                # noinspection PyUnboundLocalVariable
                logger.log(level, f"{func.__name__} returned {result}", stacklevel=2)
            return result

        return wrapper

    return decorator


# noinspection SpellCheckingInspection
class ClassProperty:
    """
    A decorator that combines the behavior of @classmethod and @property.
    This allows you to define properties that are accessible at the class level.
    """

    def __init__(
        self,
        fget: Optional[Callable[[Type[Any]], Any]] = None,
        fset: Optional[Callable[[Type[Any], Any], None]] = None,
    ):
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


class Singleton(type):
    """
    A metaclass that enforces the singleton pattern. Classes using this metaclass can only have one instance.
    Attempting to subclass a singleton class will raise a TypeError.
    """

    # noinspection PyMethodParameters,SpellCheckingInspection
    def __new__(
        meta: Type[Singleton], name: str, bases: tuple, clsdict: dict[str, Any]
    ) -> Type[Singleton]:
        """
        Creates a new singleton class. Ensures that the class cannot be subclassed.

        :param meta: The metaclass itself (Singleton).
        :param name: The name of the class being created.
        :param bases: A tuple of base classes for the class being created.
        :param clsdict: The class dictionary containing attributes and methods.
        :return: The newly created class object.
        :raises TypeError: If an attempt is made to inherit from a singleton class.
        """

        if any(isinstance(cls, meta) for cls in bases):
            raise TypeError("Cannot inherit from singleton class")
        clsdict["_instance"] = None

        # noinspection PyTypeChecker
        return super(Singleton, meta).__new__(meta, name, bases, clsdict)

    # noinspection PyUnresolvedReferences
    def __call__(cls: Type[Singleton], *args: Any, **kwargs: Any) -> Type[Singleton]:
        """
        Creates or returns the existing instance of the singleton class.

        :param cls: the class being instantiated.
        :param args: positional arguments to pass to the class constructor.
        :param kwargs: keyword arguments to pass to the class constructor.
        :return: the single instance of the class.
        """

        if not isinstance(cls._instance, cls):
            cls._instance = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instance


class AbstractDecorator(abc.ABC):
    """
    Abstract base class used to standardize decorator behaviour.
    This pattern can also be used alongside 'with' statements.
    """

    __slots__ = ("_instance", "_owner", "_func")

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._instance: object | None = None
        self._owner: type[AbstractDecorator] | None = None
        # noinspection PyUnresolvedReferences
        self._func: Callable | None = None

        num_args = len(args)
        if num_args == 1:
            self._func = args[0]

    def __get__(
        self, instance: object, owner: type[AbstractDecorator]
    ) -> AbstractDecorator:
        """
        Private method called whenever this object is accessed via attribute lookup.

        :param object instance: object instance.
        :param type[AbstractDecorator] owner: decorator type.
        :return: abstract decorator instance.
        :rtype: AbstractDecorator
        """

        self._instance = instance
        self._owner = owner

        return self

    def __call__(self, *args, **kwargs) -> Any:
        """
        Private method that is called whenever this instance is evoked.

        :return: call result.
        :rtype: Any
        """

        self.__enter__(*args, **kwargs)
        results = self.func(*args, **kwargs)
        self.__exit__(None, None, None)

        return results

    @abc.abstractmethod
    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.
        """

        pass

    @abc.abstractmethod
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        """
        Private method that is called when this instance is exited using a with statement.

        :param Any exc_type: exception type.
        :param Any exc_val: exception value.
        :param Any exc_tb: exception traceback.
        """

        pass

    @property
    def instance(self) -> object:
        """
        Returns the instance currently bound to this decorator.

        :return: instance currently bound to this decorator.
        :rtype: object
        """

        return self._instance

    @property
    def owner(self) -> type[AbstractDecorator]:
        """
        Getter method that returns the class associated with the bound instance.

        :return: class associated with the bound instance.
        :rtype: type[AbstractDecorator]
        """

        return self._owner

    @property
    def func(self) -> callable:
        """
        Getter method used to return the wrapped function.

        :return: wrapped function.
        .note:: If this is a descriptor object then the function will be bound to the instance.
        """

        return (
            self._func.__get__(self._instance, self._owner)
            if self._instance is not None
            else self._func
        )
