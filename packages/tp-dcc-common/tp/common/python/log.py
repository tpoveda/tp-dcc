# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to create basic logs
"""

import os
import logging
from logging.handlers import RotatingFileHandler, SysLogHandler
from tp.common.python import osplatform

try:
    import curses
except ImportError:
    curses = None

loggers = list()


class LoggerLevel:
    def __init__(self):
        pass

    INFO = logging.INFO
    WARNING = logging.WARNING
    DEBUG = logging.DEBUG
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class Logger(object):

    _LOGGER_IDENTIFIER = '_is_tpdcc_logger'
    _LOGGER_DEFAULT_NAME = 'tpdcc_logger'
    _LOGGER_INTERNAL_HANDLER_IS_CUSTOM_LOG_LEVEL = '_is_tpdcc_logger_internal_handler_custom_log_level'
    _LOGGER_DEFAULT_FORMAT = '[%(levelname)1.1s %(asctime)s | %(name)s | %(module)s:%(lineno)d]: %(message)s'
    _LOGGER_DEFAULT_DATE_FORMAT = '%d/%m/%y %H:%M:%S'

    def __init__(self, name=None, log_file=None, level=logging.DEBUG, formatter=None, max_bytes=0, backup_count=0,
                 file_log_level=None, enable_stderr_logger=True):
        super(Logger, self).__init__()

        self._name = name or self._LOGGER_DEFAULT_NAME
        self._log_level = level or logging.DEBUG
        self._log_file = log_file
        self._formatter = formatter

        self._logger = Logger.create_logger(name=self._name, log_file=self._log_file, level=self._log_level,
                                            formatter=self._formatter, max_bytes=max_bytes,
                                            file_log_level=file_log_level, backup_count=backup_count,
                                            enable_stderr_logger=enable_stderr_logger)

    def get_name(self):
        return self._name

    def get_logger(self):
        return self._logger

    name = property(get_name)
    logger = property(get_logger)

    @staticmethod
    def create_logger(name, log_file=None, level=logging.DEBUG, formatter=None, max_bytes=0, backup_count=0,
                      file_log_level=None, enable_stderr_logger=True):
        """
        Creates a fully configured logger instance
        :param name: str, name of the logger object
        :param log_file: str, If given, path where the log should be stored
        :param level: int, minimum logging level to display
        :param formatter: Python logging Formater object to apply
        :param max_bytes: int, size of log file when rollover should occur. Default is 0, so rollover never should occur
        :param backup_count: int, number of backups to keep. Default is 0, so no backups are done
        :param file_log_level: int, logging level for the file logger
        :param enable_stderr_logger: bool, Whether the default stderr logger be disabled or not
        :return: Logger object
        """

        if formatter is None:
            formatter = logging.Formatter(fmt=Logger._LOGGER_DEFAULT_FORMAT, datefmt=Logger._LOGGER_DEFAULT_DATE_FORMAT)

        _logger = logging.getLogger(name)
        _logger.propagate = False
        _logger.setLevel(level)

        stderr_stream_handler = None
        for handler in list(_logger.handlers):
            if hasattr(handler, Logger._LOGGER_IDENTIFIER):
                if isinstance(handler, logging.FileHandler):
                    _logger.removeHandler(handler)
                    continue
                elif isinstance(handler, logging.StreamHandler):
                    stderr_stream_handler = handler

            handler.setLevel(level)
            handler.setFormatter(formatter)

        if not enable_stderr_logger:
            if stderr_stream_handler is not None:
                _logger.removeHandler(stderr_stream_handler)
        elif stderr_stream_handler is None:
            stderr_stream_handler = logging.StreamHandler()
            setattr(stderr_stream_handler, Logger._LOGGER_IDENTIFIER, True)
            stderr_stream_handler.setLevel(level)
            stderr_stream_handler.setFormatter(formatter)
            _logger.addHandler(stderr_stream_handler)

        if log_file:
            rotating_file_handler = RotatingFileHandler(filename=log_file, maxBytes=max_bytes, backupCount=backup_count)
            setattr(rotating_file_handler, Logger._LOGGER_IDENTIFIER, True)
            rotating_file_handler.setLevel(file_log_level or level)
            rotating_file_handler.setFormatter(formatter)
            _logger.addHandler(rotating_file_handler)

        return _logger

    def reset(self):
        """
        Resets the internal logger to its initial configuration
        """

        self._logger = Logger.create_logger(name=self._name, log_file=self._log_file, level=self._log_level,
                                            formatter=self._formatter)

    def log_level(self, level=logging.DEBUG, update_custom_handlers=False):
        """
        Set the minimum log level for the internal logger
        :param level: int, new miminimum log level
        :param update_custom_handlers: bool, Whether to only reconfigure internal logger handlers only or also
            reconfigure custom handlers
        """

        self._logger.setLevel(level)

        # Reconfigure existing internal handlers
        for handler in list(self._logger.handlers):
            if hasattr(handler, Logger._LOGGER_IDENTIFIER) or update_custom_handlers:
                # If handler is a custom one we do not update log level
                if hasattr(handler, Logger._LOGGER_INTERNAL_HANDLER_IS_CUSTOM_LOG_LEVEL):
                    continue

                # Updates the log level for all default handlers
                handler.setLevel(level)

        self._log_level = level

    def formatter(self, formatter, update_custom_handlers=False):
        """
        Set the formatter for all handlers of the default logger
        :param formatter: formatter, new Python logging formatter
        :param update_custom_handlers: bool, Whether to only reconfigure internal logger handlers only or also
            reconfigure custom handlers
        """

        for handler in list(self._logger.handlers):
            if hasattr(handler, Logger._LOGGER_IDENTIFIER) or update_custom_handlers:
                handler.setFormatter(formatter)

        self._formatter = formatter

    def log_file(self, file_name, formatter=None, mode='a', max_bytes=0, backup_count=0, encoding=None,
                 log_level=None, enable_stderr_logger=True):
        """
        Setup logging to a file (using a RotatingFileHandler)
        :param file_name: str, file name of the log file
        :param formatter: Python logging formatter
        :param mode: str, mode to open the file with
        :param max_bytes: int, size of the log file when rollover should occurs. If 0, rollover never occurs
        :param backup_count: int, number of backups to keep. If 0, backup never occurs
        :param encoding: str, used to open the file with that encoding
        :param log_level: int, set a custom log level for the file logger, else uses the current global log level
        :param enable_stderr_logger: bool, Whether the default stderr logger be enabled or not
        """

        # If an internal RotatingFileHandler already exists we remove it
        self._remove_internal_loggers(enable_stderr_logger=enable_stderr_logger)

        if formatter is None and self._formatter is None:
            formatter = logging.Formatter(fmt=Logger._LOGGER_DEFAULT_FORMAT, datefmt=Logger._LOGGER_DEFAULT_DATE_FORMAT)

        # If want, we add a new RotatingFileHandler
        if file_name:
            rotating_file_handler = RotatingFileHandler(file_name, mode=mode, maxBytes=max_bytes,
                                                        backupCount=backup_count, encoding=encoding)
            setattr(rotating_file_handler, Logger._LOGGER_IDENTIFIER, True)
            if log_level:
                setattr(rotating_file_handler, Logger._LOGGER_INTERNAL_HANDLER_IS_CUSTOM_LOG_LEVEL, True)

            # Configure the handler and add it to the logger
            rotating_file_handler.setLevel(log_level or self._log_level)
            rotating_file_handler.setFormatter(formatter or self._formatter)
            self._logger.addHandler(rotating_file_handler)

    def sys_log(self, facility=SysLogHandler.LOG_USER, enable_stderr_logger=False):
        """
        Setup logging to sys log and disable other internal logger handlers
        :param facility: syslog facility to log to
        :param enable_stderr_logger: bool, Whether the default stderr logger be enabled or not
        :return: SysLogHandler
        """

        self._remove_internal_loggers(enable_stderr_logger=enable_stderr_logger)

        sys_log_handler = SysLogHandler(facility=facility)
        setattr(sys_log_handler, Logger._LOGGER_IDENTIFIER, True)
        self._logger.addHandler(sys_log_handler)

        return sys_log_handler

    def start_temp_log(self):
        """
        Initializes a new temp and stores its results in environment variable
        """

        start_temp_log(self.name)

    def record_temp_log(self, value):
        """
        Adds a new value to the temp log with the given name (if exists)
        :param value: str
        """

        record_temp_log(self.name, value)

    def end_temp_log(self):
        """
        Removes temp log with given name and returns its contents
        :return: str
        """

        return end_temp_log(self.name)

    def _remove_internal_loggers(self, enable_stderr_logger=False):
        """
        Removes the internal logger handlers of the internal logger
        :param enable_stderr_logger: bool, Whether the default stderrl logger should be disabled or not
        """

        for handler in list(self._logger.handlers):
            if hasattr(handler, Logger._LOGGER_IDENTIFIER):
                if isinstance(handler, RotatingFileHandler):
                    self._logger.removeHandler(handler)
                elif isinstance(handler, SysLogHandler):
                    self._logger.removeHandler(handler)
                elif isinstance(handler, logging.StreamHandler) and not enable_stderr_logger:
                    self._logger.removeHandler(handler)


def create_logger(logger_name, logger_path):
    """
    Function to create standard logger for modules and apps
    :param logger_name: str, name of the logger
    :param logger_path: str, path were logger will be created
    :return: Logger
    """

    # If the given path does not exists we create the given folder
    if not os.path.exists(logger_path):
        os.makedirs(logger_path)

    log_file = os.path.join(logger_path, logger_name + '.log')
    logger = Logger(name=logger_name, log_file=log_file)
    global loggers
    loggers.append(logger)

    return logger


def get_logger(logger_name):
    """
    Returns a logger, if exists, from the list of already created loggers
    :param logger_name: str, name of the logger we want to retrieve
    :return: variant, Logger || None
    """

    global loggers
    for log in loggers:
        if log.name == logger_name:
            return log

    return None


def start_temp_log(log_name):
    """
    Initializes a new temp and stores its results in environment variable
    :param log_name: str, name of the log
    """

    osplatform.set_env_var('{}_KEEP_TEMP_LOG'.format(log_name.upper()), 'True')
    osplatform.set_env_var('{}_TEMP_LOG'.format(log_name.upper()), '')


def record_temp_log(log_name, value):
    """
    Adds a new value to the temp log with the given name (if exists)
    :param log_name: str, name of the log we want to add value into
    :param value: str
    """

    if osplatform.get_env_var('{}_KEEP_TEMP_LOG'.format(log_name.upper())) == 'True':
        value = value.replace('\t', '  ') + '\n'
        osplatform.append_env_var('{}_TEMP_LOG'.format(log_name.upper()), value)


def end_temp_log(log_name):
    """
    Removes temp log with given name and returns its contents
    :param log_name: str, nam of the temp log we want to remove
    :return: str
    """

    osplatform.set_env_var('{}_KEEP_TEMP_LOG'.format(log_name.upper()), 'False')
    value = osplatform.get_env_var('{}_TEMP_LOG'.format(log_name.upper()))
    osplatform.set_env_var('{}_TEMP_LOG'.format(log_name.upper()), '')
    osplatform.set_env_var('{}_LAST_TEMP_LOG'.format(log_name.upper()), value)

    return value


def open_logger(logger):
    """
    Opens file of the given logger object if possible
    :param logger: logger, logger object to open
    """

    from tp.common.python import fileio

    log_file = None
    for handler in logger.handlers:
        if hasattr(handler, 'baseFilename'):
            log_file = handler.baseFilename
            break

    if log_file:
        fileio.open_browser(log_file)
