#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains default implementation for nested YAML configurations
"""

import os
from collections import OrderedDict

# To avoid errors when initializing Dcc server
try:
    import metayaml
except ImportError:
    pass

from tp.core import log, dcc
from tp.common.python import decorators, helpers

logger = log.tpLogger


class ConfigurationAttribute(dict, object):
    """
    Class that allows access nested dictionaries using Python attribute access
    https://stackoverflow.com/questions/38034377/object-like-attribute-access-for-nested-dictionary
    """

    def __init__(self, *args, **kwargs):
        super(ConfigurationAttribute, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @staticmethod
    def from_nested_dict(data):
        """
        Construct a nested ConfigurationAttribute from nested dictionaries
        :param data: dict
        :return: ConfigurationAttribute
        """

        if not isinstance(data, dict):
            return data
        else:
            return ConfigurationAttribute(
                {key: ConfigurationAttribute.from_nested_dict(data[key]) for key in data})


class YAMLConfigurationParser(object):
    def __init__(self, config_data):
        super(YAMLConfigurationParser, self).__init__()

        self._config_data = config_data
        self._parsed_data = OrderedDict()

    def parse(self):
        self._parsed_data = self._config_data
        return ConfigurationAttribute.from_nested_dict(self._parsed_data)


class YAMLConfiguration(object):
    def __init__(self, config_name, config_dict=None, parser_class=YAMLConfigurationParser, manager=None):
        super(YAMLConfiguration, self).__init__()

        self._config_name = config_name
        self._parser_class = parser_class
        self._config_dict = config_dict or dict()
        self._manager = manager if manager else ConfigurationManagerSingleton().get()
        self._parsed_data = self.load()

    @property
    def data(self):
        return self._parsed_data

    def get_path(self):
        if not self._parsed_data:
            return None

        return self._parsed_data.get('config', {}).get('path', None)

    def __getattr__(self, item):
        if hasattr(self._parsed_data, item):
            return getattr(self._parsed_data, item)

    def get(self, attr_section, attr_name=None, default=None):
        """
        Returns an attribute of the configuration
        :param attr_name: str
        :param attr_section: str
        :param default: object
        :return:
        """

        if not self._parsed_data:
            logger.warning('Configuration "{}" is empty"'.format(self._config_name))
            return default

        if attr_section and attr_name:
            orig_section = attr_section
            attr_section = self._parsed_data.get(attr_section, dict())
            if not attr_section:
                logger.warning('Configuration "{}" has no attribute "{}" in section "{}"'.format(
                    self._config_name, attr_name, orig_section))
                return default
            attr_value = attr_section.get(attr_name, None)
            if attr_value is None:
                logger.warning('Configuration "{}" has no attribute "{}" in section "{}"'.format(
                    self._config_name, attr_name, attr_section))
                return default
            return attr_value
        else:
            attr_to_use = attr_section
            if attr_name and not default:
                default = attr_name
            if not attr_section:
                attr_to_use = attr_name
            attr_value = self._parsed_data.get(attr_to_use, None)
            if attr_value is None:
                logger.warning('Configuration "{}" has no attribute "{}"'.format(self._config_name, attr_to_use))
                return default
            return attr_value

    def load(self):
        """
        Function that reads project configuration file and initializes project variables properly
        This function can be extended in new projects
        """

        if self._config_dict is None:
            self._config_dict = OrderedDict()

        config_data = self._get_config_data(self._config_name, config_dict=self._config_dict)
        if not config_data:
            return False

        parsed_data = self._parser_class(config_data).parse()

        return parsed_data

    def _get_config_data(self, config_name, config_dict):
        """
        Returns the config data of the given project name
        :return: dict
        """

        if not config_name:
            logger.error('Project Configuration File not found! {}'.format(self, config_name))
            return

        module_config_name = config_name
        if not module_config_name.endswith('.yml'):
            module_config_name = config_name + '.yml'

        all_config_paths = self._manager.get_config_paths(
            module_config_name=module_config_name, skip_non_existent=False)
        valid_config_paths = self._manager.get_config_paths(module_config_name=module_config_name)
        if not valid_config_paths:
            raise RuntimeError(
                'Impossible to load configuration "{}" because it does not exists in any of '
                'the configuration folders: {}'.format(config_name, ''.join(all_config_paths)))

        root_config_path = valid_config_paths[-1]
        config_data = metayaml.read(valid_config_paths, config_dict) or OrderedDict()
        if config_data is None:
            raise RuntimeError(
                'Project Configuration File {} is empty! {}'.format(self, root_config_path))

        # We store path where configuration file is located in disk
        if 'config' in config_data and 'path' in config_data['config']:
            raise RuntimeError(
                'Project Configuration File for {} Project cannot contains '
                'config section with path attribute! {}'.format(self, root_config_path))
            return
        if 'config' in config_data:
            config_data['config']['path'] = root_config_path
        else:
            config_data['config'] = {'path': root_config_path}

        return config_data


class ConfigurationManager(object):
    def __init__(self, config_paths=None):

        self._config_paths = list()

        if config_paths is None:
            config_paths = list()
        else:
            config_paths = helpers.force_list(config_paths)
        for config_path in config_paths:
            self.register_config_path(config_path)

    def get_config(self, config_name, config_dict=None, parser_class=YAMLConfigurationParser):
        new_cfg = YAMLConfiguration(
            config_name=config_name,
            config_dict=config_dict,
            parser_class=parser_class,
            manager=self
        )

        return new_cfg

    def register_config_path(self, config_path):
        if config_path and os.path.isdir(config_path) and config_path not in self._config_paths:
            self._config_paths.append(config_path)

    def get_config_paths(self, module_config_name, skip_non_existent=True):
        """
        Returns a list of valid paths where configuration files can be located
        :return: list(str)
        """

        found_paths = list()
        for config_path in self._config_paths:
            root_path = os.path.join(config_path, module_config_name)
            dcc_config_path = os.path.join(config_path, dcc.get_name(), module_config_name)
            dcc_version_config_path = os.path.join(
                config_path, dcc.get_name(), dcc.get_version_name(), module_config_name)
            for p in [root_path, dcc_config_path, dcc_version_config_path]:
                if skip_non_existent:
                    if p and os.path.isfile(p) and p not in found_paths:
                        found_paths.append(p)
                else:
                    if p and p not in found_paths:
                        found_paths.append(p)

        return found_paths


@decorators.add_metaclass(decorators.Singleton)
class ConfigurationManagerSingleton(object):
    """
    Singleton class that holds configuration manager instance
    """

    def __init__(self):
        self.manager = ConfigurationManager()

    def get(self):
        """
        Returns ConfigurationManager instance
        :return: ConfigurationManager
        """

        return self.manager
