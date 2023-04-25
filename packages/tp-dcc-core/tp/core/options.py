#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base classes to handle options
"""

from tp.core import log
from tp.common.python import helpers, settings

logger = log.tpLogger


class OptionObject(object):
    def __init__(self, option_settings=None):
        super(OptionObject, self).__init__()

        self._option_settings = option_settings

    # ================================================================================================
    # ======================== PROPERTIES
    # ================================================================================================

    @property
    def options(self):
        return self._option_settings

    # ================================================================================================
    # ======================== BASE
    # ================================================================================================

    def get_option_file(self):
        """
        Returns options file
        :return: str
        """

        self._setup_options()

        return self._option_settings.get_file()

    def has_options(self):
        """
        Returns whether the current has options or not
        :return: bool
        """

        self._setup_options()

        return self._option_settings.has_settings()

    def has_option(self, name, group=None):
        """
        Returns whether the current object has given option or not
        :param name: str, name of the option
        :param group: variant, str || None, group of the option (optional)
        :return: bool
        """

        self._setup_options()
        if group:
            name = '{}.{}'.format(group, name)
        else:
            name = str(name)

        return self._option_settings.has_setting(name)

    def add_option(self, name, value, group=None, option_type=None):
        """
        Adds a new option to the options file
        :param name: str, name of the option
        :param value: variant, value of the option
        :param group: variant, str || None, group of the option (optional)
        :param option_type: variant, str || None, option type (optional)
        """

        self._setup_options()

        if group:
            name = '{}.{}'.format(group, name)
        else:
            name = str(name)

        value_from_option_type = self._get_option_value(value=value, option_type=option_type)

        self._option_settings.set(name, value_from_option_type)

    def set_option(self, name, value, group=None):
        """
        Set an option of the option settings file. If the option does not exist, it will be created
        :param name: str, name of the option we want to set
        :param value: variant, value of the option
        :param group: variant, str || None, group of the option (optional)
        """

        if group:
            name = '{}.{}'.format(group, name)
        else:
            name = str(name)

        # TODO: We should do checks by type. At this moment there are some options types that will be broken
        # TODO: if we set them directly using this function (for example, 'combo').

        self._option_settings.set(name, value)

    def get_unformatted_option(self, name, group=None):
        """
        Returns option without format (string format)
        :param name: str, name of the option we want to retrieve
        :param group: variant, str || None, group of the option (optional)
        :return: str
        """

        self._setup_options()
        if group:
            name = '{}.{}'.format(group, name)
        else:
            name = str(name)

        value = self._option_settings.get(name)

        return value

    def get_option(self, name, group=None, default=None):
        """
        Returns option by name and group
        :param name: str, name of the option we want to retrieve
        :param group: variant, str || None, group of the option (optional)
        :param default:
        :return: variant
        """

        self._setup_options()

        value = self.get_unformatted_option(name, group)
        if value is None or value == '':
            if default is not None:
                return default
            else:
                logger.warning(
                    'Impossible to access option with proper format from {}'.format(self._option_settings.directory))
                if self.has_option(name, group):
                    if group:
                        logger.warning('Could not find option: "{}" in group: "{}"'.format(name, group))
                    else:
                        logger.warning('Could not find option: {}'.format(name))
                return value

        value = self._format_option_value(value)

        logger.debug('Accessed Option - Option: "{}" | Group: "{}" | Value: "{}"'.format(name, group, value))

        return value

    def get_option_match(self, name, return_first=True):
        """
        Function that tries to find a matching option in all the options
        :param name: str
        :param return_first: bool
        :return: variant
        """

        self._setup_options()
        options_dict = self._option_settings.settings_dict
        found = dict()
        for key in options_dict:
            if key.endswith(name):
                if return_first:
                    value = self._format_option_value(options_dict[key])
                    logger.debug('Accessed - Option: {}, value: {}'.format(name, options_dict[key]))
                    return value
                found[name] = options_dict[key]

        return found

    def get_options(self):
        """
        Returns all options contained in the settings file
        :return: str
        """

        self._setup_options()
        options = list()
        if self._option_settings:
            options = self._option_settings.settings()

        return options

    def reload_options(self):
        """
        Reload settings
        """

        if not self._option_settings:
            return

        self._option_settings.reload()

    def clear_options(self):
        """
        Clears all the options
        """

        if self._option_settings:
            self._option_settings.clear()
        self._option_settings = None

    # ================================================================================================
    # ======================== OVERRIDES
    # ================================================================================================

    def _format_option_value(self, value):
        """
        Internal function used to format object option value
        :param value: variant
        :return: variant
        """

        new_value = value
        option_type = None
        if type(value) == list:
            try:
                option_type = value[1]
            except Exception:
                pass
            value = value[0]
            if option_type == 'dictionary':
                new_value = value[0]
                dict_order = value[1]
                if type(new_value) == list:
                    new_value = new_value[0]
                new_value = helpers.order_dict_by_list_of_keys(new_value, dict_order)
                return new_value
            elif option_type == 'list' or option_type == 'file' or option_type == 'vector3f':
                return value
            elif option_type == 'combo':
                try:
                    return value[1]
                except Exception:
                    return [-1, '']
            else:
                new_value = self._format_custom_option_value(option_type, value)

        if not option_type == 'script':
            if helpers.is_string(value):
                eval_value = None
                try:
                    if value:
                        eval_value = eval(value)
                except Exception:
                    pass
                if eval_value:
                    if type(eval_value) in [list, tuple, dict]:
                        new_value = eval_value
                        value = eval_value
            if helpers.is_string(value):
                if value.find(',') > -1:
                    new_value = value.split(',')

        logger.debug('Formatted value: {}'.format(new_value))

        return new_value

    def _get_option_value(self, value, option_type):
        """
        Returns a value depending on the option type
        :param value:
        :param option_type:
        :return:
        """

        if option_type == 'combo':
            format_value = list()
            if value:
                if isinstance(value[0], (list, tuple)):
                    if len(value) == 1:
                        format_value = [value, []]
                    else:
                        format_value = value
                else:
                    format_value = [value, []]
            return [format_value, 'combo']
        else:
            if option_type:
                value = [value, option_type]

        return value

    def _format_custom_option_value(self, option_type, value):
        """
        Internal function used to format object option value with custom option types
        :param option_type: str
        :param value: object
        :return: object
        """

        return value

    def _setup_options(self):
        """
        Internal function that initializes option files
        """

        if not self._option_settings:
            self._load_options()

    def _load_options(self):
        """
        Internal function that load options settings
        """

        self._option_settings = settings.JSONSettings()
