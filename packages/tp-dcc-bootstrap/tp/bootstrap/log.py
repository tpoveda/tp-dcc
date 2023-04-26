#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc log manager
"""

import os
import inspect
import logging
from distutils.util import strtobool

main = __import__('__main__')

LOGGER_NAME = 'tp-dcc'
BOOTSTRAP_LOGGER_NAME = 'tp-dcc-bootstrap'


def get_log_levels():
	"""
	Returns a list with all levels available within Python logging system.

	:return: list of log levels.
	:rtype: list(str)
	"""

	return map(logging.getLevelName, range(0, logging.CRITICAL + 1, 10))


def get_levels_dict():
	"""
	Returns a dict with all levels available within Python logging system.

	:return: dictionary log levels.
	:rtype: list(str, str)
	"""

	return dict(zip(get_log_levels(), range(0, logging.CRITICAL + 1, 10)))


def global_log_level_override(logger):
	"""
	Makes sure the global level override is set.

	:param logging.Logger logger: logger to set.
	"""

	global_logging_level = os.environ.get('TPDCC_LOG_LEVEL', 'INFO')
	env_level = get_levels_dict()[global_logging_level]
	current_level = logger.getEffectiveLevel()
	if not current_level or current_level != env_level:
		logger.setLevel(env_level)


def logging_wrapper(method, source_name, *args, **kwargs):
	"""
	Wrapper function to log any individual method call.

	:param fn method: method to wrap.
	:param str source_name: name to tag into the logging file for this log.
	:param list args: arguments for the method.
	:param dict kwargs: keyword arguments for the method.
	"""

	def method_wrap(*args, **kwargs):
		print_args = [x for x in args if (not type(x) == dict) and (not type(x) == list)]
		tpLogger.info('{} -----> {}.{} ~~ Args:{} Kwargs:{}'.format(
			source_name, method.__module__, method.__name__, print_args, kwargs))
		return method(*args, **kwargs)

	return method_wrap, args, kwargs


def add_metaclass(metaclass):
	"""
	Decorators that allows to create a class using a metaclass
	https://github.com/benjaminp/six/blob/master/six.py
	"""

	def wrapper(cls):
		orig_vars = cls.__dict__.copy()
		slots = orig_vars.get('__slots__')
		if slots is not None:
			if isinstance(slots, str):
				slots = [slots]
			for slots_var in slots:
				orig_vars.pop(slots_var)
		orig_vars.pop('__dict__', None)
		orig_vars.pop('__weakref__', None)
		if hasattr(cls, '__qualname__'):
			orig_vars['__qualname__'] = cls.__qualname__
		return metaclass(cls.__name__, cls.__bases__, orig_vars)
	return wrapper


class _MetaLogHandler(type):
	def __call__(cls, *args, **kwargs):
		as_class = kwargs.pop('as_class', False)

		if 'cmds' in main.__dict__:
			from tp.bootstrap.dccs.maya import log
			if as_class:
				return log.MayaLogHandler
			else:
				return type.__call__(log.MayaLogHandler, *args, **kwargs)
		else:
			return None


@add_metaclass(_MetaLogHandler)
class LogHandler(object):
	pass


class Singleton(type):
	"""
	Singleton decorator as metaclass. Should be used in conjunction with add_metaclass function of this module

	@add_metaclass(Singleton)
	class MyClass(BaseClass, object):
	"""

	def __new__(meta, name, bases, clsdict):
		if any(isinstance(cls, meta) for cls in bases):
			raise TypeError('Cannot inherit from singleton class')
		clsdict['_instance'] = None
		return super(Singleton, meta).__new__(meta, name, bases, clsdict)

	def __call__(cls, *args, **kwargs):
		if not isinstance(cls._instance, cls):
			cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instance


def create_loggers():
	"""
	Returns logger of current module
	"""

	# import here because this was causing problems during MotionBuilder startup while loading CPG tools.
	import logging.config

	logger_directory = os.path.normpath(os.path.join(os.path.expanduser('~'), 'tp', 'dcc', 'logs'))
	if not os.path.isdir(logger_directory):
		os.makedirs(logger_directory)

	root_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
	logging_config = os.path.normpath(os.path.join(root_path, '__logging__.ini'))

	logging.config.fileConfig(logging_config, disable_existing_loggers=True)
	loggers = (logging.getLogger(BOOTSTRAP_LOGGER_NAME), logging.getLogger(LOGGER_NAME))
	for logger in loggers:
		dcc_handler = LogHandler()
		if dcc_handler:
			logger.addHandler(dcc_handler)
		global_log_level_override(logger)

		dev = bool(strtobool((os.environ.get('TPDCC_DEV', 'False'))))
		if dev:
			logger.setLevel(logging.DEBUG)
			for handler in logger.handlers:
				handler.setLevel(logging.DEBUG)

	return loggers


tpLogger, bootstrapLogger = create_loggers()
