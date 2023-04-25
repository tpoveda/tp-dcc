#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility module that contains functions related with formatters
"""

try:
    from functools import singledispatch
except ImportError:
    from singledispatch import singledispatch


def apply_formatter(formatter, *args, **kwargs):
    """
    Used by QAbstractModel data method
    Configures a formatter for one field, apply the formatter with the new index data
    :param formatter: formatter. If can be None/dict/callback or just any type of value
    :param args:
    :param kwargs:
    :return:
    """

    if formatter is None:
        return args[0]
    elif isinstance(formatter, dict):
        return formatter.get(args[0], None)
    elif callable(formatter):
        return formatter(*args, **kwargs)

    return formatter


def overflow_format(num, overflow):
    """
    Returns string of the given integer. If the integer is large than given overflow, '{overflow}+' is returned
    :param num: int
    :param overflow: int
    :return: str
    """

    if not isinstance(num, int):
        raise ValueError('Input argument "num" should be int type, but get "{}"'.format(type(num)))
    if not isinstance(overflow, int):
        raise ValueError('Input argument "overflow" should be int type, but get "{}"'.format(type(num)))

    return str(num) if num <= overflow else '{}+'.format(overflow)


@singledispatch
def display_formatter(input_other_type):
    """
    Used by QAbstractItemModel data method for Qt.DisplayRole
    Format any input value to a string
    :param input_other_type:
    :return: str
    """

    return str(input_other_type)


@display_formatter.register(type(None))
def _(input_none):
    return '--'


@display_formatter.register(int)
def _(input_int):
    return str(input_int)


@display_formatter.register(float)
def _(input_float):
    return '{:.2f}'.format(round(input_float, 2))


@display_formatter.register(dict)
def _(input_dict):
    if 'name' in input_dict.keys():
        return display_formatter(input_dict.get('name'))
    elif 'code' in input_dict.keys():
        return display_formatter(input_dict.get('code'))
    return str(input_dict)


@display_formatter.register(list)
def _(input_list):
    result = list()
    for i in input_list:
        result.append(display_formatter(i))
    return '.'.join(result)
