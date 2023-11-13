from __future__ import annotations

import abc
import inspect
import weakref
from typing import Iterator
from types import ModuleType

from tp.common.python import decorators, modules


class _SingletonMeta(abc.ABCMeta):

    __instances__: dict[str, _SingletonMeta] = {}

    def __call__(self, *args, **kwargs):
        """
        Private method that is called each time this class is evoked.
        """

        return self.instance(*args, **kwargs)

    def creator(cls, *args, **kwargs) -> _SingletonMeta:
        """
        Returns a new instance of this class.

        :return: new class instance.
        :rtype: SingletonMeta
        """

        instance = super().__call__(*args, **kwargs)
        cls.__instances__[cls.__name__] = instance

        return instance

    def has_instance(cls) -> bool:
        """
        Returns whether an instance of this class already exist.

        :return: True if instance of this class already exist; False otherwise.
        :rtype: bool
        """

        return cls.__instances__.get(cls.__name__, None) is not None

    def instance(cls, as_weak_reference: bool = False) -> Singleton:
        """
        Returns an instance of this class.

        :param bool as_weak_reference: whether to return instance as weak reference.
        :return: instance of this class.
        :rtype: Singleton
        """

        found_instance: Singleton | None = None
        if cls.has_instance():
            found_instance = cls.__instances__[cls.__name__]
        else:
            found_instance = cls.creator()

        return found_instance.weak_reference() if as_weak_reference else found_instance


class Singleton(object, metaclass=_SingletonMeta):

    __slots__ = ('__weakref__')

    @decorators.classproperty
    def class_name(cls) -> str:
        """
        Returns the name of this class.

        :return: class name.
        :rtype: str
        """

        return cls.__name__

    @decorators.classproperty
    def null_weak_reference(self):
        """
        Returns a null weak reference this is still callable.

        :return: lambda.
        """

        return lambda: None

    def weak_reference(self) -> weakref.ReferenceType[Singleton]:
        """
        Returns a weak reference to this instance.

        :return: instance weak reference.
        :rtype: weakref.ReferenceType[Singleton]
        """

        return weakref.ref(self)


class ProxyFactory(Singleton):
    """
    Overload of Singleton that handles the behaviour for factory interfaces.
    """

    __slots__ = ('__classes__')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__classes__ = dict(self.iterate_packages(*self.packages()))

    def __iter__(self) -> Iterator[tuple[str, type]]:
        """
        Private method that returns a generator that yields all available classes.

        :return: iterated classes.
        :rtype: Iterator[tuple[str, type]]
        """

        return self.iterate_packages(*self.packages())

    def __getitem__(self, item: int | str) -> type:
        """
         Private method that returns an indexed item.

        :param str or int item: key.
        :return: found type.
        :rtype: type
        """

        return self.get_class(item)

    def __len__(self) -> int:
        """
        Private method that returns the number of classes belonging to this factory.

        :return: factory number of classes.
        :rtype: int
        """

        pass

    @abc.abstractmethod
    def packages(self) -> list[ModuleType]:
        """
        Returns a list of packages to be inspected for classes.

        :return: list of packages to be inspected.
        :rtype: list[ModuleType]
        """

        pass

    @abc.abstractmethod
    def class_filter(self) -> type:
        """
        Returns the base class used to filter out objects when searching for classes.

        :return: base class.
        :rtype: type
        """

        pass

    def class_attr(self) -> str:
        """
        Returns the attribute name to be used to organize the class dictionary.

        :return: attribute name.
        """

        return __name__

    def classes(self) -> dict[str, type]:
        """
        Returns a dictionary of classes that can be instantiated.

        :return: dictionary of classes.
        :rtype: dict[str, type]
        """

        return self.__classes__

    def get_class(self, key: str | int) -> type | None:
        """
        Returns a class constructor based on given key.

        :param str or int key: key to get class from.
        :return: found class.
        :rtype: type or None
        """

        return self.__classes__.get(key, None)

    def iterate_modules(self, *args, **kwargs) -> Iterator[tuple[str, type]]:
        """
        Returns a generator that yields the classes from the given modules.

        :param args:
        :key str class_attr: class attribute.
        :key type class_filter: class to filter by.
        :return: iterated modules.
        :rtype: Iterator[tuple[str, type]]
        """

        class_attr = kwargs.get('class_attr', self.class_attr())
        class_filter = kwargs.get('class_filter', self.class_filter())

        for arg in args:
            if not inspect.ismodule(arg):
                continue
            for _, cls in modules.iterate_module(arg, class_filter=class_filter):
                if not hasattr(cls, class_attr):
                    continue
                key = getattr(cls, class_attr)
                if isinstance(key, (tuple, list)):
                    for item in key:
                        yield item, cls
                else:
                    yield key, cls

    def iterate_packages(self, *args, **kwargs) -> Iterator[tuple[str, type]]:
        """
        Returns a generator that yields the classes from the given packages.

        :return: iterated classes.
        :rtype: Iterator[tuple[str, type]]
        """

        for arg in args:
            if not inspect.ismodule(arg):
                continue
            found_modules = list(modules.iterate_package(arg.__file__))
            for key, cls in self.iterate_modules(*found_modules, **kwargs):
                yield key, cls
