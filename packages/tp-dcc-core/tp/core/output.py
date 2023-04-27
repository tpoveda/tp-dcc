#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains class implementations related with DCC outputs
"""

from tp.core import dcc
from tp.common.python import decorators


class _MetaOutput(type):
    def __call__(cls, *args, **kwargs):
        if dcc.is_maya():
            from tp.maya.api import output as maya_output
            return maya_output.MayaOutput
        else:
            return BaseOutput


class BaseOutput(object):

    @staticmethod
    def display_info(text):
        """
        Displays info based on application.

        :param str text: info text.
        """

        print('Info: {}'.format(text))

    @staticmethod
    def display_warning(text):
        """
        Displays warning based on application.

        :param str text: warning text.
        """

        print('Warning: {}'.format(text))

    @staticmethod
    def display_error(text):
        """
        Displays error based on application.

        :param str text: error text.
        """

        print('Error: {}'.format(text))


@decorators.add_metaclass(_MetaOutput)
class Output(object):
    pass


def display_info(text):
    return Output().display_info(text)


def display_warning(text):
    return Output().display_warning(text)


def display_error(text):
    return Output().display_error(text)
