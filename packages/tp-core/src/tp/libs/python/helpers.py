from __future__ import annotations


from collections.abc import Sequence
from typing import Type, Iterator, Iterable, Any


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

    if isinstance(var, list) and sequence_type is tuple:
        var = tuple(var)
    if isinstance(var, tuple) and sequence_type is list:
        var = list(var)

    return sequence_type(var) if not isinstance(var, sequence_type) else var


def index_in_list(list_arg: list, index: int, default: Any = None) -> Any:
    """
    Returns the item at given index. If item does not exist, returns default value.

    :param list_arg: list of objects to get from.
    :param index: index to get object at.
    :param default: any value to return as default.
    :return: item at given index.
    """

    return list_arg[index] if list_arg and len(list_arg) > abs(index) else default


def first_in_list(list_arg: list, default: Any = None) -> Any:
    """
    Returns the first element of the list. If list is empty, returns default value.

    :param list_arg: An empty or not empty list.
    :param default: If list is empty, something to return.
    :return: Returns the first element of the list.  If list is empty, returns default value.
    """

    return index_in_list(list_arg, 0, default=default)


def last_in_list(list_arg: list, default: Any = None):
    """
    Returns the last element of the list. If list is empty, returns default value.

    :param list_arg: An empty or not empty list.
    :param default: If list is empty, something to return.
    :return: Returns the last element of the list.  If list is empty, returns default value.
    """

    return index_in_list(list_arg, -1, default=default)


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


def duplicates_in_list(seq: Iterable) -> list[Any]:
    """
    Returns all duplicates items in given list or tuple.

    :param seq: iterable object.
    :return: duplicated elements in given iterable.
    """

    seen = set()
    duplicates: list[Any] = []
    for obj in seq:
        if obj in seen:
            duplicates.append(obj)
        seen.add(obj)

    return duplicates


def iterate_chunks(iterable: Iterable, size: int, overlap: int = 0) -> Iterator[Any]:
    """
    Yield successive sized chunks from the given iterable.

    :param iterable: iterable to chunk.
    :param size: chunk size.
    :param overlap: overlap size.
    """

    # noinspection PyTypeChecker
    for i in range(0, len(iterable) - overlap, size - overlap):
        yield iterable[i : i + size]


def merge_dictionaries(a: dict, b: dict, only_missing_keys: bool = False, path: str | None = None) -> dict:
    """
    Recursive function that allows to merge two dictionaries.

    :param a: dictionary to merge into.
    :param b: dictionary to merge from.
    :param only_missing_keys: If True, only missing keys will be merged.
    :param path: current path in the dictionary.
    :return: merged dictionary.
    """

    if path is None:
        path = []

    for key in b:
        if key not in a:
            a[key] = b[key]
            continue

        base_key = a[key]
        merge_key = b[key]
        if isinstance(base_key, dict) and isinstance(merge_key, dict):
            merge_dictionaries(base_key, merge_key, only_missing_keys, path + [str(key)])
        elif only_missing_keys:
            continue
        elif base_key == merge_key:
            pass
        elif isinstance(a[key], list) and isinstance(merge_key, list):
            base_key += [i for i in merge_key if i not in base_key]
        else:
            raise Exception(f'Conflict at {".".join(path + [str(key)])}')

    return a


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
            return super().__getattribute__(item)

    def __setattr__(self, key, value):
        property_object = getattr(self.__class__, key, None)
        if isinstance(property_object, property):
            if property_object.fset is None:
                raise AttributeError("can't set attribute")
            property_object.fset(self, value)
        else:
            self[key] = value

    def __delattr__(self, item):
        if item in self:
            del self[item]
            return
        super().__delattr__(item)


class UniqueDict(dict):
    """
    Wrapper of a standard Python dict that ensures that dictionary keys are unique
    """

    def __setitem__(self, key, value):
        if key not in self:
            dict.__setitem__(self, key, value)
        else:
            raise KeyError("Key already exists")
