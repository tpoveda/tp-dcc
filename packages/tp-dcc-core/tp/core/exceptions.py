#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains consts exception used by libraries
"""


class DccError(Exception):
    pass


class SettingsNameDoesNotExistError(DccError):
    pass


class NoObjectFoundError(DccError):
    pass


class MoreThanOneObjectFoundError(DccError):
    pass


class CommandCancel(DccError):
    def __init__(self, message, errors=None):
        super(CommandCancel, self).__init__(message)
        self._errors = errors

    @property
    def errors(self):
        return self._errors
