#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for settings manager
"""

from tp.core import log

logger = log.tpLogger


class ConfigAttribute(dict, object):
    """
    Class that allows access nested dictionaries using Python attribute access
    https://stackoverflow.com/questions/38034377/object-like-attribute-access-for-nested-dictionary
    """

    def __init__(self, *args, **kwargs):
        super(ConfigAttribute, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @staticmethod
    def from_nested_dict(data):
        """
        Constructs a nested YAMLConfigurationAttribute from nested dictionaries
        :param data: dict
        :return: YAMLConfigurationAttribute
        """

        if not isinstance(data, dict):
            return data
        else:
            return ConfigAttribute(
                {key: ConfigAttribute.from_nested_dict(data[key]) for key in data})


class YAMLConfigurationParser(object):
    def __init__(self, config_data):
        super(YAMLConfigurationParser, self).__init__()

        self._config_data = config_data
        self._parsed_data = dict()

    def parse(self):
        self._parsed_data = self._config_data
        return ConfigAttribute.from_nested_dict(self._parsed_data)


class DccConfig(object):
    def __init__(self, config_name, data, environment=None):
        super(DccConfig, self).__init__()

        self._config_name = config_name
        self._environment = environment or 'production'
        self._parsed_data = data

    @property
    def data(self):
        return self._parsed_data

    @data.setter
    def data(self, value):
        self._parsed_data = value

    def get_path(self):
        if not self._parsed_data:
            return None

        return self._parsed_data.get('config', {}).get('path', None)

    def get(self, attr_section, attr_name=None, default=None):
        """
        Returns an attribute of the configuration
        :param attr_name: str
        :param attr_section: str
        :param default: object
        :return:
        """

        if not self._parsed_data:
            logger.warning('Configuration "{}" is empty for "{}"'.format(
                self._config_name, self._environment))
            return default

        if attr_section and attr_name:
            orig_section = attr_section
            attr_section = self._parsed_data.get(attr_section, dict())
            if not attr_section:
                logger.warning('Configuration "{}" has no attribute "{}" in section "{}" for "{}"'.format(
                    self._config_name, attr_name, orig_section, self._environment))
                return default
            attr_value = attr_section.get(attr_name, None)
            if attr_value is None:
                logger.warning('Configuration "{}" has no attribute "{}" in section "{}" for "{}"'.format(
                    self._config_name, attr_name, attr_section, self._environment))
                return default
            return attr_value
        else:
            attr_to_use = attr_section
            if attr_name and not default:
                default = attr_name
            if not attr_section:
                attr_to_use = attr_name
            attr_value = self._parsed_data.get(attr_to_use, None)
            if attr_value is None and default is None:
                logger.warning('Configuration "{}" has no attribute "{}" for "{}"'.format(
                    self._config_name, attr_to_use, self._environment))
                return default
            return attr_value
