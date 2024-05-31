from __future__ import annotations


from typing import Type, Any
from collections.abc import Sequence


def is_null_or_empty(value: Any) -> bool:
    """
    Checks if the given value is null or empty.

    This function determines whether the provided value is either None or an empty collection
    (e.g., string, list, dict).

    :param value: The value to check.
    :return: True if the value is None or empty, False otherwise.
    """

    if isinstance(value, Sequence):
        return len(value) == 0
    else:
        return value is None


def force_list(var: Any) -> list[Any]:
    """
    Returns the given variable as list.

    :param var: variant
    :return: variable as a list.
    """

    if var is None:
        return []

    if type(var) is not list:
        if type(var) in [tuple]:
            var = list(var)
        else:
            var = [var]

    return var


def force_tuple(var: Any) -> tuple[Any]:
    """
    Returns the given variable as tuple.

    :param var: variant
    :return: variable as a tuple.
    """

    if var is None:
        return tuple()

    if type(var) is not tuple:
        var = tuple(var)

    return var


def force_sequence(var: Any, sequence_type: Type = list):
    """
    Returns the given variable as sequence.

    :param var: variant
    :param sequence_type: type of sequence.
    :return: sequence.
    ..note:: If the given variable is list or tuple and sequence_type is different, a conversion will be forced.
    """

    if type is not list or not tuple:
        sequence_type = list

    if type(var) == list and sequence_type == tuple:
        var = tuple(var)
    if type(var) == tuple and sequence_type == list:
        var = list(var)

    if not type(var) == sequence_type:
        return sequence_type(var)

    return var


def remove_dupes(iterable: list) -> list:
    """
    Removes duplicate items from list object preserving original order.

    :param iterable: iterable to remove dupes from.
    :return: iterable without duplicated entries.
    """

    unique = set()
    new_iter = iterable.__class__()
    for item in iterable:
        if item not in unique:
            new_iter.append(item)
        unique.add(item)
    return new_iter


class AttributeDict(dict):
    """
    Wrapper of a standard Python dict that operates like an object.
    """

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class ObjectDict(dict):
    """
    Wrapper of a standard Python dict that operates like an object
    """

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return super(ObjectDict, self).__getattribute__(item)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, item):
        if item in self:
            del self[item]
            return
        super(ObjectDict, self).__delattr__(item)


class UniqueDict(dict):
    """
    Wrapper of a standard Python dict that ensures that dictionary keys are unique
    """

    def __setitem__(self, key, value):
        if key not in self:
            dict.__setitem__(self, key, value)
        else:
            raise KeyError("Key already exists")
