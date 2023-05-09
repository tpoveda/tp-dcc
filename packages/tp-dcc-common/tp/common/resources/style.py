#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom style implementation
This custom stylesheet allow us to easily define custom properties (without the hassle of using Qt properties)
"""

import re
import string

from tp.common.python import helpers, path
from tp.common.resources import theme


class StyleTemplate(string.Template):
    """
    Style template that useful to replace specific style code on runtime.
    """

    delimiter = '@'
    idpattern = r'[_a-z][_a-z0-9]*'


class StyleSheet(object):
    """
    Base style class
    Implements an include functionality, so in your style files you can use #include to include other style
    files. The path must be defined relative to the current style path.
    """

    EXTENSION = 'qss'

    def __init__(self, stylesheet=''):
        super(StyleSheet, self).__init__()

        self._data = ''                         # stores the style final format data as string
        self._original_data = stylesheet        # stores original stylesheet string (without formatting)

    def __repr__(self):
        return str(self.data)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = str(value)

    @classmethod
    def from_path(cls, style_path, **kwargs):
        """
        Returns stylesheet from given path.

        :param str style_path: style path
        :param dict, kwargs: extra arguments used to format the style read from path
        :return: StyleSheet instance object
        :rtype: StyleSheet
        """

        data = cls.read(style_path)
        stylesheet = cls(data)
        data = cls.include_paths(style_path, data)
        data = cls.format(data, **kwargs)
        stylesheet.data = data

        return stylesheet

    @classmethod
    def include_paths(cls, style_path, data):
        """
        Checks for #include directives in the style and replaces those includes with the contents of those included
        files.

        :param str style_path: style path.
        :param str data: str, data of the style.
        :return: data with the #include directives replaced.
        :rtype: str
        """

        if not path.is_file(style_path):
            return data

        file_dir = path.dirname(style_path)
        included_data = list()
        for line in data.split('\n'):
            if not line.startswith('#include '):
                included_data.append(line)
                continue
            file_name_to_include = line.replace('#include ', '').replace('\r', '')
            file_to_include = path.get_absolute_path(file_name_to_include, file_dir)
            if not path.is_file(file_to_include):
                continue

            load_data = cls.read(file_to_include)
            new_data = cls.include_paths(file_to_include, load_data)

            if new_data:
                included_data.append('\n/*Included from: {}*/'.format(file_to_include))
            for load_line in new_data.split('\n'):
                included_data.append(load_line)

        return '\n'.join(included_data)

    @classmethod
    def format(cls, data=None, dpi_value=1, **kwargs):
        """
        Returns style with proper format. Replaces all user defined attributes with the attributes from theme.

        :param str data: style data.
        :param dict attributes: dictionary that contains all user attributes defined by style theme.
        :param float dpi_value: dpi value defined in theme.
        :return: stylesheet data ready to be applied.
        :rtype: str
        """

        keys = list(kwargs.keys())
        if helpers.is_python2():
            keys.sort(key=len, reverse=True)
        else:
            keys = sorted(keys, key=len, reverse=True)

        for key in keys:
            option_value = theme.solve_value(kwargs, key)
            option_key = (key if key.startswith('@') else '@{}'.format(key)).upper()
            data = data.replace(str(option_key), str(option_value))

        # dpi replacement
        re_dpi = re.compile('[0-9]+[*]DPI')
        new_data = list()
        for line in data.split('\n'):
            dpi_ = re_dpi.search(line)
            if dpi_:
                new = dpi_.group().replace('DPI', str(dpi_value))
                val = int(eval(new))
                line = line.replace(dpi_.group(), str(val))
            new_data.append(line)

        # each line of the style ends with end of line
        data = '\n'.join(new_data)

        return data

    @staticmethod
    def read(style_path):
        """
        Reads style data from given path.
        :param str style_path: style path
        :return: data contained in the style file
        :rtype: str
        """

        data = ''
        if path.is_file(style_path):
            with open(style_path, 'r') as f:
                data = f.read()

        return data
