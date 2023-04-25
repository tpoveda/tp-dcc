#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC command implementation
"""

import sys
import time
import inspect
import traceback
from collections import deque
from abc import ABCMeta, abstractproperty, abstractmethod

from tp.core import log, exceptions, dcc
from tp.common.python import decorators, osplatform
from tp.common import plugin

logger = log.tpLogger


@decorators.add_metaclass(ABCMeta)
class DccCommand(object):

    class ArgumentParser(dict):
        def __getattr__(self, item):
            result = self.get(item)
            if result:
                return result
            try:
                return self[item]
            except KeyError:
                return super(DccCommand.ArgumentParser, self).__getattribute__(item)

    is_enabled = True

    def __init__(self, stats=None):
        self._stats = stats
        self._arguments = self.ArgumentParser()
        self._return_result = None
        self.initialize()

    @property
    def stats(self):
        return self._stats

    @stats.setter
    def stats(self, value):
        self._stats = value

    @property
    def arguments(self):
        return self._arguments

    @abstractproperty
    def id(self):
        """
        Returns unique command ID used to call the command
        :return: str, unique command ID
        """

        raise NotImplementedError('abstract command DCC property id not implemented!')

    @abstractproperty
    def creator(self):
        """
        Returns the command developer name
        :return: str
        """

        raise NotImplementedError('abstract command DCC property creator not implemented!')

    @abstractproperty
    def is_undoable(self):
        """
        Returns whether or not this command is undoable
        :return: bol
        """

        return False

    @abstractmethod
    def run(self, **kwargs):
        """
        Executes the command functionality.
        :param kwargs: dict, dictionary with key value pairs. Any kind of type is supported (even DCC specific types).
        :return: variant, this function can return values. Any kind type is supported. (even DCC specific types).
        """

        raise NotImplementedError('abstract command DCC function run not implemented!')

    def initialize(self):
        """
        Initializes functionality for the command
        """

        func_args = inspect.getargspec(self.run)
        args = func_args.args[1:]
        defaults = func_args.defaults or tuple()
        if len(args) != len(defaults):
            raise ValueError('Command run function({}) must only use keyword arguments.'.format(self.id))
        elif args and defaults:
            arguments = self.ArgumentParser(zip(args, defaults))
            self._arguments = arguments
            return arguments

        return self.ArgumentParser()

    def description(self):
        """
        Returns the descriptino of the command. Class doc is used by default.
        :return: str
        """

        return self.__doc__

    def undo(self):
        """
        If the command is undoable this function is call to reverse the operation done by run function
        """

        pass

    def has_argument(self, name):
        """
        Returns whether or not this command supports given argument
        :param name: str
        :return: bool
        """

        return name in self._arguments

    def parse_arguments(self, arguments):
        """
        Parses given command arguments
        :param arguments: dict
        :return: bool
        """

        kwargs = self._arguments
        kwargs.update(arguments)
        self.resolve_arguments(self.ArgumentParser(**kwargs))

        return True

    def resolve_arguments(self, arguments):
        """
        Function that is called before running the command. Useful to valid incoming command arguments before executing
        the command.
        :param arguments: dict, key, value pairs of commands being passed to the run command function
        :return: dict, dictionary with the same key value pairs as the arguments param
        """

        return arguments


class CommandStats(object):
    def __init__(self, command):
        self._command = command
        self._start_time = 0.0
        self._end_time = 0.0
        self._execution_time = 0.0

        self._info = dict()

        self._init()

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        self._start_time = value

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, value):
        self._end_time = value

    @property
    def execution_time(self):
        return self._execution_time

    def _init(self):
        """
        Internal function that initializes info for the plugin and its environment
        """

        self._info.update({
            'name': self._command.__class__.__name__,
            'creator': self._command.creator,
            'module': self._command.__class__.__module__,
            'filepath': inspect.getfile(self._command.__class__),
            'id': self._command.id,
            'application': dcc.get_name()
        })
        self._info.update(osplatform.machine_info())

    def start(self):
        """
        Starts the execution of the plugin
        """

        self._start_time = time.time()

    def finish(self, trace=None):
        """
        Function that is called when plugin finishes its execution
        :param trace: str or None
        """

        self._end_time = time.time()
        self._execution_time = self._end_time - self._start_time
        self._info['executionTime'] = self._execution_time
        self._info['lastUsed'] = self._end_time
        if trace:
            self._info['traceback'] = trace


class MetaCommandRunner(type):

    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            if dcc.is_maya():
                from tp.maya.cmds import command
                cls._instance = type.__call__(command.MayaCommandRunner, *args, **kwargs)
            else:
                cls._instance = type.__call__(BaseCommandRunner, *args, **kwargs)

        return cls._instance


class BaseCommandRunner(object):
    def __init__(self):
        self._undo_stack = deque()
        self._redo_stack = deque()
        self._manager = plugin.PluginFactory(DccCommand, plugin_id='id')
        self._manager.register_paths_from_env_var('TPDCC_COMMAND_LIB', package_name='tp-dcc')

    @property
    def undo_stack(self):
        return self._undo_stack

    @property
    def redo_stack(self):
        return self._redo_stack

    def commands(self):
        return self._manager.plugins()

    def manager(self):
        return self._manager

    def run(self, command_id, **kwargs):
        command_to_run = self.find_command(command_id)
        if not command_to_run:
            raise ValueError(
                'No command found with given id "{}" in package "{}"'.format(command_id, self._manager.package))

        command_to_run = command_to_run(CommandStats(command_to_run))
        if not command_to_run.is_enabled:
            return
        try:
            command_to_run.parse_arguments(kwargs)
        except exceptions.CommandCancel:
            return
        except Exception:
            raise

        trace = None
        result = None
        try:
            result = self._run(command_to_run)
        except exceptions.CommandCancel:
            self._undo_stack.remove(command_to_run)
            command_to_run.stats.finish(None)
            return result
        except Exception:
            exc_type, exc_value, exc_trace = sys.exc_info()
            trace = traceback.format_exception(exc_type, exc_value, exc_trace)
            logger.exception(trace)
            raise
        finally:
            if not trace and command_to_run.is_undoable:
                self._undo_stack.append(command_to_run)
            command_to_run.stats.finish(trace)

            return result

    def undo_last(self):
        if not self._undo_stack:
            return False

        command_to_undo = self._undo_stack[-1]
        if command_to_undo is not None and command_to_undo.is_undoable:
            command_to_undo.undo()
            self._redo_stack.append(command_to_undo)
            self._undo_stack.remove(command_to_undo)
            return True

        return False

    def redo_last(self):
        trace = None
        result = None
        if self._redo_stack:
            command_to_redo = self._redo_stack.pop()
            if command_to_redo is not None:
                try:
                    command_to_redo.stats = CommandStats(command_to_redo)
                    result = self._run(command_to_redo)
                except exceptions.CommandCancel:
                    self._undo_stack.remove(command_to_redo)
                    command_to_redo.stats.finish(None)
                    raise
                except Exception:
                    exc_type, exc_value, exc_trace = sys.exc_info()
                    trace = traceback.format_exception(exc_type, exc_value, exc_trace)
                    logger.exception(trace)
                finally:
                    if not trace and command_to_redo.is_undoable:
                        self._undo_stack.append(command_to_redo)
                    command_to_redo.stats.finish(trace)

        return result

    def find_command(self, command_id):
        """
        Returns registered command by its ID
        :param command_id: str
        :return: DccCommand
        """

        return self._manager.get_plugin_from_id(command_id)

    def command_help(self, command_id):
        """
        Returns the command help of the given command
        :param command_id: str
        :return: str
        """

        command = self.find_command(command_id)
        if not command:
            return

        doc_help = inspect.getdoc(command)
        run_help = inspect.getdoc(command.run)

        return 'Class: {}\n{}\nRun: {}'.format(command.__name__, doc_help, run_help)

    def flush(self):
        """
        Clears the undo/redo history of the command
        """

        self._undo_stack.clear()
        self._redo_stack.clear()

    def cancel(self, msg):
        """
        Cancels command execution
        :param msg: str
        """

        raise exceptions.CommandCancel(msg)

    def _run(self, command_to_run):
        result = command_to_run.run(**command_to_run.arguments)
        command_to_run._return_result = result

        return result


@decorators.add_metaclass(MetaCommandRunner)
class CommandRunner(object):
    pass
