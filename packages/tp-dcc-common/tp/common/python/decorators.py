#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utility functions decorators
"""

from __future__ import annotations

import os
import abc
import time
import inspect
import traceback
import threading
from typing import Any, Callable
from functools import wraps, update_wrapper

from overrides import override

from tp.core import log
from tp.common.python import debug

logger = log.tpLogger


def abstractmethod(fn):
    """
    The decorated function should be overridden by a software specific module.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        msg = 'Abstract implementation has not been overridden.'
        mode = os.getenv('ABSTRACT_METHOD_MODE')
        if not mode or mode == 'raise':
            raise NotImplementedError(debug.debug_object_string(fn, msg))
        elif mode == 'warn':
            logger.warning(debug.debug_object_string(fn, msg))
        return fn(*args, **kwargs)

    return wrapper


def abstractproperty(func):
    """
    Abstract property decorated function.

    :param callable func: decorated function.
    """

    return property(abc.abstractmethod(func))


def accepts(*types, **kw):
    """
    Function decorator that checks if decorated function arguments are of the expected types.
    :param types: Expected types of the inputs to the decorated function. Must specify a type for each parameter
    :param kw: (optional) Specification of 'debug' level ( 0 | 1 | 2 )
    """

    if not kw:
        is_debug = 1
    else:
        is_debug = kw['debug']
    try:
        def decorator(f):
            def new_fn(*args):
                if debug == 0:
                    return f(*args)
                args = list(args)
                if not (len(args[1:]) == len(types)):
                    raise AssertionError
                arg_types = tuple(map(type, args[1:]))
                if arg_types != types:
                    msg = debug.format_message(f.__name__, types, arg_types, 0)
                    if is_debug == 1:
                        try:
                            for i in range(1, len(args)):
                                args[i] = types[i - 1](args[i])
                        except ValueError:
                            raise ValueError(msg)
                        except TypeError:
                            raise TypeError(msg)
                    elif is_debug == 2:
                        raise TypeError(msg)
                return f(*args)
            new_fn.__name__ = f.__name__
            return new_fn
        return decorator
    except KeyError as key:
        raise KeyError(key + 'is not a valid keyword argument')
    except TypeError as msg:
        raise TypeError(msg)


def returns(ret_type, **kw):
    """
    Function decorator that checks if decorated function return value is of the expected type
    :param retType: Excepted type of the decorated function return value. Must specify type for each parameter
    :param kwargs: (optional) Specification of 'debug' level (0 | 1 | 2)
    """

    try:
        if not kw:
            is_debug = 1
        else:
            is_debug = kw['debug']

        def decorator(f):
            def newf(*args):
                result = f(*args)
                if is_debug == 0:
                    return result
                res_type = type(result)
                if res_type != ret_type:
                    msg = debug.format_message(f.__name__, (ret_type,), (res_type,), 1)
                    if is_debug == 1:
                        try:
                            result = ret_type(result)
                        except ValueError:
                            raise ValueError
                    elif is_debug == 2:
                        raise TypeError(msg)
                return result
            newf.__name__ = f.__name__
            return newf
        return decorator
    except KeyError as key:
        raise KeyError(key + 'is not a valid keyword argument')
    except TypeError as msg:
        raise TypeError(msg)


def timer(fn):
    """
    Function decorator for simple timer
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if logger.getEffectiveLevel() == 20:
            # If we are in info mode we disable timers
            res = fn(*args, **kwargs)
        else:
            t1 = time.time()
            res = fn(*args, **kwargs)
            t2 = time.time()

            trace = ''
            try:
                mod = inspect.getmodule(args[0])
                trace += '{0} >>'.format(mod.__name__.split('.')[-1])
            except Exception:
                logger.debug('function module inspect failure')

            try:
                trace += '{0}.'.format(args[0].__class__.__name__)
            except Exception:
                logger.debug('function class inspect failure')

            trace += fn.__name__
            logger.debug('Timer : %s: took %0.3f ms' % (trace, (t2 - t1) * 1000.0))
        return res
    return wrapper


def print_elapsed_time(f):
    """
    Function decorator that gets the elapsed time
    :param f: fn, function
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        t = time.time()
        res = f(*args, **kwargs)
        print(f.__name__, time.time() - t)
        return res
    return wrapper


def timestamp(f):
    """
    Function decorator that gets the elapsed time with a more descriptive output
    :param f: fn, function
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        res = f(*args, **kwargs)
        function_name = f.__name__
        logger.info('<{}> Elapsed time : {}'.format(function_name, time.time() - start_time))
        return res
    return wrapper


def try_pass(fn):
    """
    Function decorator that tries a function and if it fails pass.

    :param fn: function
    """

    def wrapper(*args, **kwargs):
        return_value = None
        try:
            return_value = fn(*args, **kwargs)
        except Exception:
            logger.error(traceback.format_exc())
        return return_value
    return wrapper


def empty_decorator(fn):
    """
    Empty decorator implementation.

    :param callable fn: decorated function.
    :return: function result.
    :rtype: any
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper


def repeater(interval, limit=-1):
    """!
    A function interval decorator based on
    http://stackoverflow.com/questions/5179467/equivalent-of-setinterval-in-python

    Infinite Example Usage:
        @repeater(.05)
        def infinite():
            print "Executing infinity."

        import time
        print "Starting Infinite Repeating Function"
        token = infinite()
        time.sleep(1)
        print "Stopping: infinite"
        token.stop()

    Limited Example Usage:
        @repeater(.05, 5)
        def x5():
            print "Executing x5"

        import time
        print "Starting Limited Repeating Function"
        token = x5()
        while not token.isSet():
            time.sleep(1)
        print "Expired: x5"

    @param interval      The interval (in seconds) between function invocations.
    @param limit         The limit to the number of function invocations; -1 represents infinity.
    @return              A new decorator with a closure around the original function and the Python threading.
                         Thread used to invoke it.
    """

    def actual_decorator(fn):

        def wrapper(*args, **kwargs):

            class RepeaterTimerThread(threading.Thread):
                def __init__(self):
                    threading.Thread.__init__(self)
                    self._event = threading.Event()

                def run(self):
                    i = 0
                    while i != limit and not self._event.is_set():
                        self._event.wait(interval)
                        fn(*args, **kwargs)
                        i += 1
                    else:
                        if self._event:
                            self._event.set()

                def stopped(self):
                    return not self._event or self._event.is_set()

                def pause(self):
                    self._event.set()

                def resume(self):
                    self._event.clear()

                def stop(self):
                    self._event.set()
                    self.join()

            token = RepeaterTimerThread()
            token.daemon = True
            token.start()
            return token

        return wrapper

    return actual_decorator


def cached(fn):
    cache = {}

    @wraps(fn)
    def wrapper(*args):
        try:
            return cache[args]
        except KeyError:
            rv = fn(*args)
            cache[args] = rv
            return rv

    return wrapper


def add_method(cls):
    """
    This decorator adds a function to given class instance
    https://medium.com/@mgarod/dynamically-add-a-method-to-a-class-in-python-c49204b85bd6
    :param cls: class instance
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        setattr(cls, func.__name__, wrapper)
        # Note we are not binding func, but wrapper which accepts self but does exactly the same as func
        return func     # returning func means func can still be used normally
    return decorator


def add_metaclass(metaclass):
    """
    Decorators that allows to create a class using a metaclass
    https://github.com/benjaminp/six/blob/master/six.py
    :param metaclass:
    :return:
    """

    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        slots = orig_vars.get('__slots__')
        if slots is not None:
            if isinstance(slots, str):
                slots = [slots]
            for slots_var in slots:
                orig_vars.pop(slots_var)
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        if hasattr(cls, '__qualname__'):
            orig_vars['__qualname__'] = cls.__qualname__
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper


def classproperty(func: Callable) -> ClassProperty:
    """
    Custom decorator that returns a class property object to be used as a decorator.

    :param callable func: decorated function.
    :return: class property.
    :rtype: ClassProperty
    """

    func = classmethod(func) if not isinstance(func, classmethod) else func
    return ClassProperty(func)


class Singleton(type):

    """
    Singleton decorator as metaclass. Should be used in conjunction with add_metaclass function of this module
    @add_metaclass(Singleton)
    class MyClass(BaseClass, object):
        ...
    """

    def __new__(meta, name, bases, clsdict):
        if any(isinstance(cls, meta) for cls in bases):
            raise TypeError('Cannot inherit from singleton class')
        clsdict['_instance'] = None
        return super(Singleton, meta).__new__(meta, name, bases, clsdict)

    def __call__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance


class HybridMethod:
    """
    Merges a normal method with a classmethod
    First two arguments are (cls, self), where self will match cls if it is a classmethod
    https://stackoverflow.com/a/18078819/2403000
    """

    def __init__(self, fn):
        self._fn = fn

    def __get__(self, obj, cls):
        context = obj if obj is not None else cls

        @wraps(self._fn)
        def hybrid(*args, **kwargs):
            return self._fn(cls, context, *args, **kwargs)

        # Mimic method attributes (not required)
        hybrid.__func__ = hybrid.im_func = self._fn
        hybrid.__self__ = hybrid.im_self = context

        return hybrid


class LazyProperty(property):
    """
    https://github.com/jackmaney/lazy-property/blob/master/lazy_property/__init__.py

    Allow us to initialize an attribute only once. Conerting this:
    class SomeOtherClass(object):
        @property
        def calculation_value(self):
        if not hasattr(self, "_calculation_value"):
            self._calculation_value = do_some_big_calculation()
        return self._calculation_value

    into this:

    class YetAnotherClass(object):
        @lazy_property.LazyProperty
        def calculation_value(self):
            return do_some_big_calculation()
    """

    def __init__(self, method, fget=None, fset=None, fdel=None, doc=None):

        self.method = method
        self.cache_name = "_{}".format(self.method.__name__)

        doc = doc or method.__doc__
        super(LazyProperty, self).__init__(fget=fget, fset=fset, fdel=fdel, doc=doc)

        update_wrapper(self, method)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if hasattr(instance, self.cache_name):
            result = getattr(instance, self.cache_name)
        else:
            if self.fget is not None:
                result = self.fget(instance)
            else:
                result = self.method(instance)
            setattr(instance, self.cache_name, result)
        return result


class LazyWritableProperty(LazyProperty):
    """
    https://github.com/jackmaney/lazy-property/blob/master/lazy_property/__init__.py
    """

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError
        if self.fset is None:
            setattr(instance, self.cache_name, value)
        else:
            self.fset(instance, value)


class ClassProperty:
    """
    Class used to decorate class properties
    https://stackoverflow.com/questions/5189699/how-to-make-a-class-property
    """

    __slots__ = ('fget', 'fset', 'fdel')

    def __init__(self, fget: classmethod, fset: classmethod | None = None, fdel: classmethod | None = None):
        super().__init__()

        self.fget = fget
        self.fset = fset
        self.fdel = fdel

    @override(check_signature=False)
    def __get__(self, instance: object, owner: type) -> Any:
        owner = type(instance) if owner is None else owner
        return self.fget.__get__(instance, owner)

    @override(check_signature=False)
    def __set__(self, instance: object, value: Any):
        if not self.fset:
            raise AttributeError("can't set attribute")

        return self.fset.__get__(instance, type(instance))(value)

    @override(check_signature=False)
    def __delete__(self, instance: object):
        if not self.fdel:
            raise AttributeError("can't delete attribute")

        return self.fdel.__get__(instance, type(instance))()

    def setter(self, func: Callable) -> ClassProperty:
        """
        Decorator hook used to override setter function.

        :param Callable func: function.
        :return: class property instance
        :rtype: ClassProperty
        """

        func = classmethod(func) if not isinstance(func, classmethod) else func
        self.fset = func
        return self

    def deleter(self, func: Callable) -> ClassProperty:
        """
        Decorator hook used to override delete function.

        :param Callable func: function.
        :return: class property instance
        :rtype: ClassProperty
        """

        func = classmethod(func) if not isinstance(func, classmethod) else func
        self.fdel = func
        return self


class AbstractDecorator(abc.ABC):
    """
    Abstract base class used to standardize decorator behaviour.
    This pattern can also be used alongside 'with' statements.
    """

    __slots__ = ('_instance', '_owner', '_func')

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._instance: object | None = None
        self._owner: type[AbstractDecorator] | None = None
        self._func: Callable | None = None

        num_args = len(args)
        if num_args == 1:
            self._func = args[0]

    def __get__(self, instance: object, owner: type[AbstractDecorator]) -> AbstractDecorator:
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
        ..note:: If this is a descriptor object then the function will be bound to the instance.
        """

        return self._func.__get__(self._instance, self._owner) if self._instance is not None else self._func
