#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related to names
"""

from pymxs import runtime as rt

from tp.common.python import helpers, name as naming_utils
from tp.max.core import node as node_utils


class FindUniqueName(naming_utils.FindUniqueString, object):
    """
    This class allows to find a name that does not clash with other names in the Maya scene
    It will increment the last number in hte name
    If no number is found, it will append a 1 to the end of the name
    """

    def __init__(self, name):
        super(FindUniqueName, self).__init__(name)

        self.work_on_last_number = True

    def get_last_number(self, bool_value):
        """
        Sets to update last number to get unique name or not
        :param bool_value: bool
        """

        self.work_on_last_number = bool_value

    def _get_scope_list(self):
        """
        Internal function used to get the scope list for the increment string
        :return: list<str>
        """

        if node_utils.get_pymxs_node(self.increment_string):
            return [self.increment_string]

        return list()

    def _format_string(self, number):
        """
        Internal function to get the unique name format
        :param number: int
        """

        if number == 0:
            number = 1
            self.increment_string = '{}_{}'.format(self.test_string, number)

        if number > 1:
            if self.work_on_last_number:
                self.increment_string = naming_utils.increment_last_number(self.increment_string)
            else:
                self.increment_string = naming_utils.increment_first_number(self.increment_string)

    def _get_number(self):
        """
        Internal function to get the number on the string that we want to make unique
        :return: int
        """

        if self.work_on_last_number:
            number = naming_utils.get_last_number(self.test_string)
        else:
            number = naming_utils.get_first_number(self.test_string)
        if number is None:
            return 0

        return number


def find_unique_name(obj_names=None, include_last_number=True, do_rename=False):

    def _find_unique_name(obj_name):
        node = node_utils.get_pymxs_node(obj_name)
        if not node:
            return obj_name
        unique = FindUniqueName(obj_name)
        unique.get_last_number(include_last_number)
        unique_name = unique.get()
        unique_name = rt.uniquename(unique_name)
        if do_rename:
            node.name = unique_name
            return node.name
        else:
            return unique_name

    if not obj_names:
        obj_names = [obj.name for obj in list(rt.selection)]

    if isinstance(obj_names, (tuple, list)):
        unique_names = list()
        for obj in enumerate(obj_names):
            unique_names.append(_find_unique_name(obj))
        return helpers.remove_dupes(unique_names)
    else:
        return rt.uniquename(obj_names)
