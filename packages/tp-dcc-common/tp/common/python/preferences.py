#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different classes to handle preferences
"""

import os
import json
import pickle

from tp.core import log
from tp.common.python import helpers, decorators

if helpers.is_python2():
    json_decode_error = Exception
else:
    json_decode_error = json.decoder.JSONDecodeError

logger = log.tpLogger

_broken_files = dict()


class PreferenceHandler(object):
    """
    Allows for a specific preference to be handled completely different than others
    Must reimplement set_preference_value and get_preference_value functions
    """

    @staticmethod
    @decorators.abstractmethod
    def get_preference_value():
        raise NotImplementedError

    @staticmethod
    @decorators.abstractmethod
    def set_preference_value():
        raise NotImplementedError


class PreferenceFile(dict):
    """
    Base Dictionary based preference file.
    """

    def __init__(self, path, handlers=None):

        self._path = path
        self._handlers = handlers or dict()
        if os.path.isfile(self._path):
            self.read()
        else:
            self.write()

        super(PreferenceFile, self).__init__()

    def __setitem__(self, key, value):
        self.read()
        if key in self._handlers:
            value = self._handlers.get(key).set_preference_value(value)
            if not value:
                value = '<external>'
        super(PreferenceFile, self).__setitem__(key, value)
        self.write()

    def __getitem__(self, key):
        self.read()
        if key in self._handlers:
            return self._handlers.get(key).get_preference_value()
        return super(PreferenceFile, self).__getitem__(key)

    @property
    def path(self):
        return self._path

    @property
    def handlers(self):
        return self._handlers

    @decorators.abstractmethod
    def write(self):
        """
        Writes local preferences to stored path
        Must be overwritten in custom preferences
        :return: str
        """

        raise NotImplementedError

    @decorators.abstractmethod
    def read(self):
        """
        Reads local preferences from stored path
        Must be overwritten in custom preferences
        :return: str
        """

        raise NotImplementedError

    def get(self, key, default=None):
        """
        Returns preference value. If not found, fallback to default
        :param key: str
        :param default: variant
        :return: variant
        """

        try:
            return self[key]
        except KeyError:
            return default

    def pop(self, key):
        """
        Overwrites base dict pop function to force to save of the preference file
        after removing the key
        :param key: str
        """

        super(PreferenceFile, self).pop(key)
        self.write()

    def set_handler(self, preference_key, handler):
        """
        Sets the handler to use for the given preference key
        :param preference_key: str
        :param handler: PrefHandler
        """

        self._handlers[preference_key] = handler

    def remove_handler(self, preference_key):
        """
        Removes any present handler from the given preference key
        :param preference_key: str
        """

        try:
            self._handlers.pop(preference_key)
        except KeyError:
            pass


class JsonPreference(PreferenceFile):

    def write(self):
        out = dict()
        out.update(self)
        with open(self._path, 'w+') as fh:
            json.dump(out, fh, indent=4, sort_keys=False, separators=(',', ': '))

    def read(self):
        contents = dict()
        if not os.path.isfile(self._path):
            return contents

        try:
            with open(self._path, 'r') as fh:
                contents = json.load(fh)
        except json_decode_error:
            _broken_files.setdefault(self._path, 0)
            times_hit = _broken_files[self._path]
            if times_hit < 3:
                logger.error('Invalid preference JSON file "{}"'.format(self._path))
            times_hit += 1
            _broken_files[self._path] = times_hit

        self.clear()
        self.update(contents)


class PicklePreference(PreferenceFile):

    def write(self):
        out = dict()
        out.update(self)
        with open(self._path, 'wb+') as fh:
            pickle.dump(out, fh, protocol=2)

    def read(self):
        contents = dict()
        if not os.path.isfile(self._path):
            return contents

        try:
            with open(self._path, 'r+b') as fh:
                contents = pickle.load(fh) if python.is_python2() else pickle.load(fh, encoding='bytes')
        except pickle.UnpicklingError:
            _broken_files.setdefault(self._path, 0)
            times_hit = _broken_files[self._path]
            if times_hit < 3:
                logger.error('Failed to load pickle preference "{}"'.format(self._path))
            times_hit += 1
            _broken_files[self._path] = times_hit

        self.clear()
        self.update(contents)
