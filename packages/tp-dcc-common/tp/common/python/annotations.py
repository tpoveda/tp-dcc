from __future__ import annotations

import re
import inspect
from typing import Callable, Any

from tp.core import log

logger = log.tpLogger

__type__ = re.compile(r'(?:(?::type\s)|(?::key\s))([a-zA-Z0-9_]+)(?:\:\s)([a-zA-Z._]+[\[a-zA-Z_.,\s\]]*)\n')
__rtype__ = re.compile(r'(?:\:rtype:\s)([a-zA-Z._]+[\[a-zA-Z_.,\s\]]*)\n')
__index__ = re.compile(r'([a-zA-Z._]+)(?:\[([a-zA-Z_.,\s]+)\])?')


def annotations(func: Callable) -> dict:
    """
    Returns a dictionary of annotations by parsing the given function docstring.

    :param Callable func: method to get annotations of.
    :return: found annotations.
    :rtype: dict
    :note: For optimization purposes, this dictionary will be cached inside the function.
    """

    def _type_from_string(_string, _globals: dict | None = None, _locals: dict | None = None) -> type:
        """
        Internal function that returns type from given string.
        :param str _string: type from given string.
        :param dict or None _globals: optional globals.
        :param dict or None _locals: optional locals.
        :return: type from string.
        :rtype: type
        """

        _globals = _globals or globals()
        _locals = _locals or locals()

        try:
            return eval(_string, _globals, _locals)
        except (NameError, TypeError):
            logger.error(f'Unable to parse type from string: {_string}')
            return object

    cached_annotations = func.__annotations__
    if cached_annotations or func.__doc__ is None:
        return func.__annotations__

    types = __type__.findall(func.__doc__)
    __locals__ = func.__globals__
    if types:
        cached_annotations.update({key: _type_from_string(value, _locals=__locals__) for (key, value) in types})

    return_type = __rtype__.findall(func.__doc__)
    if len(return_type) == 1:
        cached_annotations['return'] = _type_from_string(return_type[0], _locals=__locals__)

    return cached_annotations


def is_parametrized_alias(type_to_check: type) -> bool:
    """
    Returns whether if given type represents a parametrized alias.

    :param type type_to_check: type to check.
    :return: True if given type represents a parametrized alias; False otherwise.
    :rtype: bool
    """

    return hasattr(type_to_check, '__origin__') and hasattr(type_to_check, '__args__')


def decompose_alias(alias: Any) -> tuple[type, tuple]:
    """
    Breaks apart the given alias into its origin and parameter components.

    :param alias: alias to decompose.
    :return: decomposed alias.
    :rtype: tuple[type, tuple]
    """

    if is_parametrized_alias(alias):
        return alias.__origin__, alias.__args__
    elif inspect.isclass(alias):
        return alias, tuple()
    else:
        return type(alias), tuple()


def is_builtin_type(type_to_check: type) -> bool:
    """
    Returns whether given type is JSON compatible.

    :param type type_to_check: type to check.
    :return: True if given type is JSON compatible; False otherwise.
    :rtype: bool
    """

    if is_parametrized_alias(type_to_check):
        origin, parameters = decompose_alias(type_to_check)
        return is_builtin_type(origin) and all([is_builtin_type(x) for x in parameters])
    elif inspect.isclass(type_to_check):
        return issubclass(type_to_check, (bool, int, float, str, list, dict))

    return is_builtin_type(type(type_to_check))
