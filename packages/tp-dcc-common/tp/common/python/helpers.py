#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modules that contains utility functions related with Python
"""

from __future__ import annotations

import os
import re
import sys
import ast
import uuid
import time
import types
import inspect
import traceback
import collections
from typing import Any
from itertools import groupby
from operator import itemgetter
from collections import OrderedDict
from collections.abc import Sequence, Iterator

from tp.common.python import strings, osplatform


def is_null_or_empty(value: Any) -> bool:
    """
    Returns whether given value is null or empty.

    :param Any value: value to check.
    :return: True if given value is null or empty; False otherwise.
    :rtype: bool
    """

    if isinstance(value, Sequence):
        return len(value) == 0
    else:
        return value is None


def add_to_python_path(path: str, check: bool = True, insert: bool = True) -> bool:
    """
    Adds a path to the Python path, only if it is not present in the Python path.

    :param str path: path to add to the Python path.
    :param bool check: whether to check path existence before adding it.
    :param bool insert: whether to insert path at the beginning or append it at the end.
    :returns: True if path was added to PYTHONPATH successfully; False otherwise.
    :rtype: bool
    """

    if not path:
        return False

    if check:
        if not os.path.exists(path):
            return False

    if path in sys.path:
        return False

    if insert:
        sys.path.insert(0, path)
    else:
        sys.path.append(path)

    return True


def add_to_environment(env, new_paths):
    """
    Adds given paths into the given environment variable
    :param env: str
    :param new_paths: list(str)
    """

    paths = [i for i in os.environ.get(env, '').split(os.pathsep) if i]

    for p in new_paths:
        if p not in paths:
            paths.append(p)

    os.environ[env] = os.pathsep.join(paths) + os.pathsep


def load_python_module(module_name, directory):
    """
    Loads a given module name located in the given directory
    NOTE: After loading a module you can access programmatically to all functions and attributes of the module
    :param module_name: str, name of the module we want to load
    :param directory: str, directory path where the module is located
    :return: mod, loaded module
    """

    import imp
    from tp.common.python import path

    if not path.is_dir(directory):
        return None

    full_path = path.join_path(directory, module_name)
    if not path.is_file(full_path):
        return None

    split_name = module_name.split('.')
    file_path, path_name, description = imp.find_module(split_name[0], [directory])
    try:
        module = imp.load_module(module_name, file_path, path_name, description)
    except Exception:
        file_path.close()
        return traceback.format_exc()
    finally:
        if file_path:
            file_path.close()

    return module


def import_python_module(module_name, directory):
    """
    Imports the given module
    :param module_name: str, name of the module
    :param directory: str, path where the module is located
    :return: mod, imported module
    """

    from tp.common.python import path, fileio

    if not path.is_dir(directory=directory):
        return

    module = None
    full_path = path.join_path(directory, module_name)
    if path.is_file(full_path):
        if directory not in sys.path:
            sys.path.append(directory)

        split_name = module_name.split('.')
        script_name = split_name[0]

        exec('import {}'.format(script_name))
        exec('reload({})'.format(script_name))

        module = eval(script_name)
        sys.path.remove(directory)

    return module


def source_python_module(module_file):
    """
    Sources the python module located in the given directory
    :param module_file: str
    :return: variant, sourced module || None
    """

    osplatform.get_permission(module_file)

    try:
        try:
            delete_source_code_from_sys_modules(module_file)
            module_in = open(module_file, 'r')
            if is_python2():
                import md5
                import imp
                return imp.load_source(md5.new(module_file).hexdigest(), module_file, module_in)
            else:
                import hashlib
                from importlib.machinery import SourceFileLoader
                return SourceFileLoader(hashlib.md5(module_file.encode()).hexdigest(), module_file).load_module()
        except Exception:
            return traceback.format_exc()
        finally:
            try:
                module_in.close()
            except Exception:
                pass
    except ImportError:
        traceback.print_exc(file=sys.stderr)
        return None


def get_version():
    """
    Return current Python version used
    :return: SemanticVersion, python version
    """

    from tp.common.python import version

    py_version = sys.version_info
    current_version = version.SemanticVersion(
        major=py_version.major,
        minor=py_version.minor,
        patch=py_version.micro
    )

    return current_version


def is_python2():
    """
    Returns whether current version is Python 2
    :return: bool
    """

    return get_version().major == 2


def is_python3():
    """
    Returns whether current version is Python 3
    :return: bool
    """

    return get_version().major == 3


def clear_list(list_to_clear):
    """
    Clears given Python list
    :param list_to_clear: list
    """

    if is_python2():
        del list_to_clear[:]
    else:
        list_to_clear.clear()


def list_diff(list1, list2):
    """
    Returns a a list with all the elements of second list that are not contained in the first list
    :param list1: list
    :param list2: list
    :return: list
    """

    return [i for i in list1 if i not in list2]


def list_to_string(list_):
    """
    Returns a string from the given list
    >>> list_to_string(['1,', '2', '3'])
    >>> # 1, 2, 3
    :param list_: list
    :return:str
    """

    list_ = [str(item) for item in list_]
    list_ = str(list_).replace("[", "").replace("]", "")
    list_ = list_.replace("'", "").replace('"', "")

    return list_


def string_to_list(str_):
    """
    Returns a list from the given string
    >>> string_to_list(['1', '2', '3'])
    >>> # ['1', '2', '3']
    :param str_:
    :return: list
    """

    str_ = '["' + str(str_) + '"]'
    str_ = str_.replace(' ', '')
    str_ = str_.replace(',', '","')

    return eval(str_)


def force_list(var):
    """
    Returns the given variable as list.

    :param var: variant
    :return: variable as a list.
    :rtype: list
    """

    if var is None:
        return []

    if type(var) is not list:
        if type(var) in [tuple]:
            var = list(var)
        else:
            var = [var]

    return var


def force_tuple(var):
    """
    Returns the given variable as tuple.

    :param var: variant
    :return: variable as a tuple.
    :rtype: tuple
    """

    if var is None:
        return ()

    if type(var) is not tuple:
        var = tuple(var)

    return var


def force_sequence(var, sequence_type=list):
    """
    Returns the given variable as sequence.

    If the given variable is list or tuple and sequence_type is different, a conversion will be forced
    :param var: variant
    :return: sequence.
    :rtype: tuple or list
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


def index_in_list(list_arg, index, default=None):
    """
    Returns the item at given index. If item does not exist, returns default value.

    :param list(any) list_arg: list of objects to get from.
    :param int index: index to get object at.
    :param any default: any value to return as default.
    :return: any
    """

    return list_arg[index] if list_arg and len(list_arg) > abs(index) else default


def first_in_list(list_arg, default=None):
    """
    Returns the first element of the list. If list is empty, returns default value.

    :param list(any) list_arg: An empty or not empty list.
    :param any default: If list is empty, something to return.
    :return: Returns the first element of the list.  If list is empty, returns default value.
    :rtype: any
    """

    return index_in_list(list_arg, 0, default=default)


def last_in_list(list_arg, default=None):
    """
    Returns the last element of the list. If list is empty, returns default value.

    :param list(any) list_arg: An empty or not empty list.
    :param any default: If list is empty, something to return.
    :return: Returns the last element of the list.  If list is empty, returns default value.
    :rtype: any
    """

    return index_in_list(list_arg, -1, default=default)


def flatten_list(list_arg):
    """
    Returns a flattened list that has nested lists.

    :param list(Any) list_arg: A list with nested lists.
    :return: Returns a flattened list that has nested lists.
    :rtype: List(Any)
    """

    result = lambda *n: (e for a in n for e in (result(*a) if isinstance(a, (tuple, list)) else (a,)))
    return list(result(list_arg))


def set_list_value_at(initial_list, index, value, buffer_value=None):
    """
    Sets a value into a list at an arbitrary index, buffering the list size until it meets that length.
    If the index value is negative it will buffer the start of the list until it could set a value at that index.

    :param list initial_list: The list to set the value into.
    :param int index: The index at which to set that value.
    :param any value: The value to set into the list at that index
    :param any buffer_value: The value which should be used to buffer the list entries if it is not long enough.
    :return: The modified list.
    :raises IndexList: if given index is not an integer.
    :rtype: list
    """

    if not isinstance(index, int):
        raise IndexError('Index must be an int')

    if index < 0:
        buffer_length = abs(index)
        index = 0
        buffer_list = [buffer_value for x in range(buffer_length)]
        initial_list = buffer_list + initial_list
    elif len(initial_list) <= index:
        buffer_length = index + 1 - len(initial_list)
        buffer_list = [buffer_value for x in range(buffer_length)]
        initial_list = initial_list + buffer_list

    initial_list[index] = value

    return initial_list


def rotate_sequence(seq, current):
    """
    Rotates sequence in given index
    :param seq: list
    :param current: int
    :return: list
    """

    n = len(seq)
    for i in range(n):
        yield seq[(i + current) % n]


def index_of(obj, seq):
    """
    Returns the index of the first occurrence of obj in seq
    """

    try:
        if get_version() < 2.6:
            for index in (i for i in range(len(seq)) if seq[i] == obj):
                return index
            else:
                return next((i for i in range(len(seq)) if seq[i] == obj), None)
    except Exception:
        raise


def last_index_of(obj, seq):
    """
    Returns the index of the last occurrence of obj in seq
    """

    try:
        if get_version() < 2.6:
            for index in (i for i in range(len(seq) - 1, -1, -1) if seq[i] == obj):
                return index
        else:
            return next((i for i in range(len(seq) - 1, -1, -1) if seq[i] == obj), None)
    except Exception:
        raise


def zip_dict(*dcts):
    """
    Custom zip for dictionaries
    """

    for i in set(dcts[0]).intersection(*dcts[1:]):
        yield (i,) + tuple(d[i] for d in dcts)


def module_exists(moduleName):
    """
    Checks if a Python module exists (passing module name)
    :param moduleName: str, Name of module to be checked
    """

    import imp

    try:
        module_info = imp.find_module(moduleName)
        module = imp.load_module(moduleName, *module_info)
        imp.find_module('__init__', module.__path__)
        has_module = True
    except Exception:
        has_module = False
    return has_module


def find_missing_items(intList):
    """
    Returns missing integers numbers from a list of integers
    :param intList: list(int), list of integers
    :return: list(int),  sorted list of missing integers numbers of the original list
    """

    original_set = set(intList)
    smallest_item = min(original_set)
    largest_item = max(original_set)
    full_set = set(range(smallest_item, largest_item + 1))
    return sorted(list(full_set - original_set))


def safe_code_exec(cmd, env=dict()):
    """
    Safely execute code with specified dictionary
    """

    try:
        exec(cmd in env)
    except Exception:
        raise (sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])


def remove_dupes(iterable):
    """
    Removes duplicate items from iterable object preserving original iterable order
    :param iterable: iterable
    :return: iterable
    """

    unique = set()
    new_iter = iterable.__class__()
    for item in iterable:
        if item not in unique:
            new_iter.append(item)
        unique.add(item)
    return new_iter


def iter_by(iterable, count):
    """
    Returns a generator which will yield certain elements of the iterable. This elements are defined
    by the count steps
    for obj in iter_by(range(7), 3):
        print(obj)
    [0, 1, 2]
    [3, 4, 5]
    [6]
    :param iterable: iterable
    :param count: int, num of
    :return: generator
    """

    i = iter(iterable)
    while True:
        to_yield = list()
        try:
            for n in range(count):
                to_yield.append(i.next())
                yield to_yield
        except StopIteration:
            if to_yield:
                yield to_yield
            break


def enum(*sequential, **named):
    """
    Enum implementation that supports automatic generation and also supports converting the values
    of the enum back to names
    >>> nums = enum('ZERO', 'ONE', THREE='three')
    >>> nums.ZERO
    # 0
    >>> nums.reverse_mapping['three']
    # 'THREE'
    """

    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums['reverse_mapping'] = reverse
    return type(str('Enum'), (), enums)


def generate_uuid():
    """
    Returns a unique UUID
    :return: str
    """

    return str(uuid.uuid4().upper())


def itersubclasses(cls, _seen=None):
    """
    http://code.activestate.com/recipes/576949-find-all-subclasses-of-a-given-class/
    Iterator to yield full inheritance from a given class, including subclasses. This
    """

    if _seen is None:
        _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError:
        subs = cls.__subclasses__(cls)

    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for sub in itersubclasses(sub, _seen):
                yield sub


def get_inheritance_map(class_to_process):
    """
    Return the inheritance mapping of the given class
    :param class_to_process: class
    """

    return inspect.getmro(class_to_process)


def get_instance_user_attributes(cls):
    """
    Returns user attributes defined in a class or instance of a class
    :param cls:
    :return: list
    """

    _def_attrs = dir(type('dummy', (object,), {}))
    _def_attrs.extend(['staticMetaObject'])

    attributes = inspect.getmembers(cls, lambda a: not (inspect.isroutine(a)))
    attributes = [
        a for a in attributes if not (a[0].startswith('__') and a[0].endswith('__')) and a[0] not in _def_attrs]

    return attributes


def user_message(message, prefix='message'):
    """
    Writes teh given prefix + message in the Python output
    :param message: str
    :param prefix: str
    """
    sys.stdout.write(prefix + ': ' + message + '\n')


def is_none(s):
    """
    Returns True if the given object has None type or False otherwise
    :param s: object
    :return: bool
    """

    return type(s).__name__ == 'NoneType'


def is_string(s):
    """
    Returns True if the given object has None type or False otherwise
    :param s: object
    :return: bool
    """

    return isinstance(s, str)


def is_number(s):
    """
    Returns True if given string is int or float, False otherwise
    :param s: object
    :return: bool
    """
    if is_bool(s):
        return False
    return isinstance(s, int) or isinstance(s, float)


def is_int(s):
    """
    Returns True if the given string is an integer, False otherwise
    :param s: str
    :return: bool
    """

    try:
        a = float(s)
        b = int(a)
    except (TypeError, ValueError):
        return False
    else:
        return a == b


def is_float(s):
    """
    Returns True if the given string is a float, False otherwise
    :param s: str
    :return: bool
    """

    try:
        a = float(s)
    except (TypeError, ValueError):
        return False
    else:
        return True


def is_bool(s):
    """
    Returns True if the given object has None type or False otherwise
    :param s: object
    :return: bool
    """
    return isinstance(s, bool) or str(s).lower() in ['true', 'false']


def is_list(s):
    """
    Returns True if the given object has list type or False otherwise
    :param s: object
    :return: bool
    """
    return type(s) in [list, tuple]


def is_dict(s):
    """
    Returns True if the given object has dict type or False otherwise
    :param s: object
    :return: bool
    """
    from collections import OrderedDict
    return type(s) in [dict, OrderedDict]


def return_list_without_duplicates(lst):
    """
    Removes duplicates from a list and return the new ilst
    :param lst: list
    :return: list
    """

    new_list = list()
    for item in lst:
        if item not in new_list:
            new_list.append(item)

    return new_list


def delete_pyc_file(python_script):
    """
    Deletes the .pyc file that corresponds to the given .py file
    :param python_script: str
    """

    from tp.common.python import path, fileio

    script_name = path.basename(python_script)
    if not python_script.endswith('.py'):
        print('WARNING: Could not delete .pyc file for {}!'.format(script_name))
        return

    compile_script = python_script + 'c'
    if path.is_file(compile_script):
        compile_name = path.basename(compile_script)
        compile_dir_name = path.dirname(compile_script)
        if not compile_name.endswith('.pyc'):
            return

        fileio.delete_file(name=compile_name, directory=compile_dir_name)


def delete_source_code_from_sys_modules(code_file):
    """
    Remove all modules from sys.modules that are pointing to the given code file
    :param code_file: str
    """

    found = list()
    keys = list(sys.modules.keys())

    for key in keys:
        if key not in sys.modules:
            continue
        if sys.modules[key] and hasattr(sys.modules[key], '__file__'):
            if sys.modules[key].__file__ == code_file:
                found.append(key)
                break

    for key in found:
        if key in sys.modules:
            sys.modules.pop(key)


def convert_list_to_string(*args):
    """
    Given a list returns a string
    :param args:
    :return: str
    """

    try:
        if args is None:
            return 'None'
        if not args:
            return ''
        new_args = list()
        for arg in args:
            if arg is not None:
                new_args.append(str(arg))
        args = new_args
        if not args:
            return ''
        string_value = strings.join(args)
        string_value = string_value.replace('\n', '\t\n')
        if string_value.endswith('\t\n'):
            string_value = string_value[:-2]

        return string_value
    except Exception:
        raise(RuntimeError)


def get_class_parent_classes(base_class=None, parent_class=None):
    """
    Returns all base class parent classes
    :param base_class: obj, Base class
    :param parent_class: obj, Parent class
    :return: list<str>, parent class names
    """

    base_classes = list()
    cl = parent_class if parent_class is not None else base_class
    for b in cl.__bases__:
        if b.__name__ not in ['object']:
            base_classes.append(b)
            base_classes.extend(get_class_parent_classes(parent_class=b))

    return base_classes


def get_dict_ordered_keys_from_values(d):
    """
    Returns a list of keys from dict, ordered based on their values
    :param d: dict, dictionary to construct list from
    :return: list<variant>
    """

    return [i[0] for i in sorted(list(d.items()), key=lambda k, v: v)]


def get_dict_ordered_values_from_keys(d):
    """
    Returns a list of dictionary values, ordered based on their keys
    :param d: dict, dictionary to construct list from
    :return: list<variant>
    """

    return [d[key] for key in sorted(list(d.keys()))]


def flatten_list(list_to_flatten):
    """
    Returns a flattened version of the given list
    :param list_to_flatten: list, list to flatten
    :return: list
    """

    elems = list()
    for i in list_to_flatten:
        if isinstance(i, types.ListType):
            elems.extend(i)
        else:
            elems.append(i)

    return elems


def string_to_dictionary(string):
    """
    Converts a dictionary string representation into a dictionary
    :param string: str
    :return: dict
    """

    return ast.literal_eval(string)


def path_to_dictionary(path):
    """
    Returns the tree hierarchy of the given path as a Python dictionary
    :param path: str
    :return: dict
    """

    d = {'name': os.path.basename(path)}
    if os.path.isdir(path):
        d['type'] = 'directory'
        d['children'] = [path_to_dictionary(os.path.join(path, x)) for x in os.listdir(path)]
    else:
        d['type'] = 'file'

    return d


def to_3_list(item):
    """
    Converts item into a 3 item list
    :param item: var
    :return: list<var, var, var>
    """

    if not isinstance(item, list):
        item = [item] * 3

    return item


def u_print(msg, **kwargs):
    """
    `print` with encoded unicode.
    `print` unicode may cause UnicodeEncodeError
    or non-readable result when `PYTHONIOENCODING` is not set.
    this will fix it.
    :param msg: unicode, message to print
    :param kwargs: dict
    """

    if isinstance(msg, strings.text_type):
        encoding = None
        try:
            encoding = os.getenv('PYTHONIOENCODING', sys.stdout.encoding)
        except AttributeError:
            # `sys.stdout.encoding` may not exists.
            pass
        msg = msg.encode(encoding or 'utf-8', 'replace')
    print(msg, **kwargs)


def dict_merge(dict, merge_dict):
    """
    Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.

    :param dict: dict onto which the merge is executed
    :param merge_dict: dct merged into dct
    :return: None
    """

    for k, v in merge_dict.iteritems():
        if (k in dict and isinstance(dict[k], dict) and isinstance(merge_dict[k], collections.Mapping)):
            dict_merge(dict[k], merge_dict[k])
        else:
            dict[k] = merge_dict[k]


def current_processor_time():
    """
    Retunrs the current processor time
    :return: float
    """

    if is_python2():
        return time.clock()
    else:
        return time.process_time()


def is_iterable(obj):
    """
    Returns whether or not given Python object is iterable
    :param obj: object
    :return: bool
    """

    try:
        it = iter(obj)
    except TypeError:
        return False

    return True


def chunk(iterable, size, overlap=0):
    """
    Yield successive sized chunks from the given iterable.

    :param list or tuple iterable: iterable to chunk.
    :param int size: chunk size.
    :param bool overlap: overlap size.
    :return: generator(any)
    """

    for i in range(0, len(iterable) - overlap, size - overlap):
        yield iterable[i:i + size]


def uniqify(list_to_make_unqiue):
    """
    Makes list unique, and preserves it order.

    :param list list_to_make_unqiue: list to unique
    :return: unique list.
    :rtype: list
    """

    if is_python2():
        return list(OrderedDict.fromkeys(list_to_make_unqiue))

    return list(dict.fromkeys(list_to_make_unqiue))


def group_consecutive_items(list_of_items):
    """
    From a list of non grouped consecutive items, returns a list of grouped consecutive frames
    :param list_of_items: list(int), list of frames. For example, [1, 2, 5, 7, 8, 9, 11, 12, 13, 15]
    :return: list(list(int)), list of frames. For example, [[1, 2,], [5], [7, 8, 9], [11, 12, 13], [15]]
    """

    list_of_frames = list()
    for k, g in groupby(enumerate(list_of_items), lambda i, x: i - x):
        list_of_frames.append(map(itemgetter(1), g))

    return list_of_frames


def from_list_to_nested_dict(input_arg, separator='/'):
    """
    Function that converts a list of strings to a nested dict
    :param input_arg: a list/tuple/set of strings
    :param separator: separator split input string
    :return: list of nested dict
    """

    if not isinstance(input_arg, (list, tuple, set)):
        raise TypeError('Input argument "input_arg" should be a list or tuple or set, but get {}'.format(
            type(input_arg)))
    if not is_string(separator):
        raise TypeError('Input argument "separator" should be str or unicode but get {}'.format(type(separator)))

    result = list()

    for item in input_arg:
        components = item.strip(separator).split(separator)
        component_count = len(components)
        current = result
        for i, comp in enumerate(components):
            action_comp = next((x for x in current if x['value'] == comp), None)
            if action_comp is None:
                action_comp = {'value': comp, 'label': comp, 'children': list()}
                current.append(action_comp)
            current = action_comp['children']
            if i == component_count - 1:
                action_comp.pop('children')

    return result


def float_range(start, stop=None, step=None):
    """
    Function that returns a generator that allow us to do a range using float numbers
    :param start: float
    :param stop: float
    :param step: float
    :return: generator
    """

    start = float(start)
    if stop is None:
        stop = start + 0.0
        start = 0.0
    if step is None:
        step = 1.0

    count = 0
    while True:
        temp = float(start + count * step)
        if step > 0 and temp >= stop:
            break
        elif step < 0 and temp <= stop:
            break
        yield temp
        count += 1


def order_dict_by_list_of_keys(dict_to_order, keys):
    """
    Order dictionary taking into account the order of the keys in a list
    :param dict_to_order: dict
    :param keys: list(str)
    :return: dict
    """

    return OrderedDict([(key, dict_to_order[key]) for key in keys if key in dict_to_order])


def merge_dicts(dict_a, dict_b, path=None):
    """
    Merges to given dictionaries
    :param dict_a: dict
    :param dict_b: dict
    :param path:
    :return:
    """

    path = path or list()
    for key in dict_b:
        if key not in dict_a:
            dict_a[key] = dict_b[key]
            continue
        if isinstance(dict_a[key], dict) and isinstance(dict_b[key], dict):
            merge_dicts(dict_a[key], dict_b[key], path + [str(key)])
        elif dict_a[key] == dict_b[key]:
            pass
        else:
            raise Exception('Conflict at {}'.format('.'.join(path + [str(key)])))

    return dict_a


def compare_and_update_dicts(source_dict, target_dict):
    """
    Compares two dictionaries and updates target dict with entries that where located in source_dict but not in
    the target dictionary.

    :param source_dict: dict, source dictionary with original entries
    :param target_dict: dict, target dictionary that will get the new changes from source
    :return:
    """

    msg_log = ''
    for k, v in source_dict.items():
        existing = target_dict.get(k)
        if existing is None:
            msg_log += 'New key found while comparing user to default dictionary. ' \
                       'Copying over [\"{}\": \"{}\"] \n'.format(k, v)
            target_dict[k] = v
            existing = v
        if isinstance(v, dict):
            t, m = compare_and_update_dicts(v, existing)
            msg_log += m

    return target_dict, msg_log


def get_dict_slice(starting_dict, index, default_value=None):
    """
    For each value list in a dictionary return the index value with the corresponding key.

    :param dict starting_dict: A dictionary of keys with list values.
    :param int index: The slice value to return from each list.
    :param Any default_value: If the length of the value isn't long enough, return a default value.
    :return: modified dictionary of sliced values.
    :rtype: dict
    """

    result = dict()
    for key, values in starting_dict.items():
        result[key] = values[index] if len(values) >= index+ 1 else default_value

    return result


def duplicates_in_list(seq):
    """
    Returns all duplicates items in given list or tuple.

    :param seq: list or tuple
    :return: list
    """

    seen = set()
    duplicates = list()
    for obj in seq:
        if obj in seen:
            duplicates.append(obj)
        seen.add(obj)

    return duplicates


def order_list_numerically(list_to_order):
    """
    Numerically sorts a list of strings that may have integers within
    :param list_to_order: list(str) or tuple(str)
    :return: list(str)
    """

    return sorted(list_to_order, key=lambda key: [int(c) if c.isdigit() else c for c in re.split('([0-9]+)', key)])


def index_exists_in_list(items_list, index):
    """
    Returns whether given index exists in given list
    :param items_list: list or tuple
    :param index: int
    :return: bool
    """

    return (0 <= index < len(items_list)) or (-len(items_list) <= index < 0)


def update_dictionaries(source, target):
    """
    Compares recursively the two given dictionary keys and values. target will get all the new changes from source.

    :param dict source: source dictionary with the original data.
    :param dict target: target dictionary that will get the new changes from source.
    :return: tuple with the new target dictionary and  a message log with all the changes that have occurred.
    :rtype: tuple(dict, str)
    """

    message_log = ''

    for key, value in source.items():
        existing = target.get(key, None)
        if existing is None:
            message_log += 'New key found while comparing dictionary. Copying over ["{}": "{}"]\n'.format(key, value)
            target[key] = value
            existing = value
        if isinstance(value, dict):
            t, m = update_dictionaries(value, existing)
            message_log += m

    return target, message_log


def merge_dictionaries(target, source, path=None, only_missing_keys=False, update=False):
    """
    Merges given dictionaries.

    :param dict target:  source dictionary.
    :param dict source: target dictionary.
    :param str path:
    """

    path = force_list(path)
    for key in source:
        if key not in target:
            target[key] = source[key]
            continue
        base_key = target[key]
        merge_key = source[key]
        if isinstance(base_key, dict) and isinstance(merge_key, dict):
            merge_dictionaries(base_key, merge_key, path + [str(key)])
        elif only_missing_keys:
            continue
        elif base_key == merge_key:
            pass
        elif isinstance(target[key], list) and isinstance(merge_key, list):
            base_key += [i for i in merge_key if i not in base_key]
        else:
            if update:
                target[key] = source[key]
            else:
                raise Exception('Conflict at {}'.format('.'.join(path + [str(key)])))

    return target


def get_args(local_dict):
    """
    Returns arguments from local function dict.

    :param dict local_dict: local dictionary.
    :return: arguments.
    :rtype: dict
    """

    local_dict.pop('self', None)
    local_dict.pop('__class__', None)

    return local_dict


def is_array(obj: Any) -> bool:
    """
    Returns whether given object is an array.

    :param Any obj: object to check.
    :return: True if given object is an array; False otherwise.
    :rtype: bool
    """

    return isinstance(obj, Sequence) and not isinstance(obj, str)


def is_array_like(obj: Any) -> bool:
    """
    Returns whether given object is like an array.
    This is useful for C++ array wrappers that aren't derived from the abstract sequence class.

    :param Any obj: object to check.
    :return: True if given object is like an array; False otherwise.
    :rtype: bool
    """

    return (hasattr(obj, '__getitem__') and hasattr(obj, '__len__')) and not isinstance(obj, str)


def is_iterator(obj: Any) -> bool:
    """
    Returns whether given object is an iterator.

    :param Any obj: object to check.
    :return: True if given object is an iterator; False otherwise.
    :rtype: bool
    """

    return isinstance(obj, Iterator) and not isinstance(obj, str)


def is_iterator_like(obj: Any) -> bool:
    """
    Returns whether given object is like an iterator.

    :param Any obj: object to check.
    :return: True if given object is like an iterator; False otherwise.
    :rtype: bool
    """

    return (hasattr(obj, '__iter__') and hasattr(obj, '__next__')) and not isinstance(obj, str)


class RollbackImporter(object):
    """
    This class is used to restore the loaded modules in a certain time after the rollback is instantiated
    It does by storing the list of loaded Python modules when rollback is initialized and if the rollback
    is uninstalled, the modules loaded after rollback creation will be deleted, forcing Python to reload
    them when the module is next imported
    """

    def __init__(self):
        """
        Creates an instance and installs and store the current imported modules list
        """

        self._prev_modules = set(sys.modules.keys())

    def uninstall(self):
        """
        Removes current loaded modules loaded after RollbackImporter was instantiated
        """

        sys_modules_copy = sys.modules.copy()
        for mod_name in sys_modules_copy:
            if mod_name not in self._prev_modules:
                del sys.modules[mod_name]


# Python 2 & 3 compatible implementation
# https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python

class _Singleton(type):
    _instances = dict()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Singleton(_Singleton('SingletonMeta', (object,), {})):
    pass


class classproperty(object):
    """
    Simplified way of creating getter and setters in Python
    """

    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


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


class UniqueOrderedDict(OrderedDict):
    """
    Wrapper of a standard Python dict that ensures that dictionary keys are unique
    """

    def __setitem__(self, key, value):
        if key not in self:
            OrderedDict.__setitem__(self, key, value)
        else:
            raise KeyError("Key already exists")
