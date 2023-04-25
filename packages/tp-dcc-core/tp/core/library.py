#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains class that defines DCC libraries
"""


class DccLibrary(object):

    ID = None
    VERSION = '0.0.0'

    def __init__(self, manager, config=None, dev=False, *args, **kwargs):
        super(DccLibrary, self).__init__(manager=manager)

        self._config = config
        self._dev = dev

    @property
    def config(self):
        return self._config

    @property
    def dev(self):
        return self._dev

    @classmethod
    def load(cls):
        """
        Function that is called when library is discovered by the Library Manager

        NOTE: This function is called during import time, so we should try to reduce as much as possible the amount
        of code that we call here
        :return:
        """

        pass

    @classmethod
    def config_dict(cls):
        """
        Returns internal tool configuration dictionary
        :return: dict
        """

        return {
            'name': 'DccLib',
            'id': 'tpDcc-libs-library',
            'supported_dccs': dict(),
            'creator': 'Tomas Poveda',
            'tooltip': ''
        }
