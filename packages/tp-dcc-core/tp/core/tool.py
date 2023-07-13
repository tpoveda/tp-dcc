#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to define Dcc tools
"""

from __future__ import annotations

import sys
import abc
import typing
import traceback

from tp.core import log
from tp.common.python import decorators
from tp.common import plugin

if typing.TYPE_CHECKING:
    from tp.core.managers.tools import ToolsManager

logger = log.tpLogger


@decorators.add_metaclass(abc.ABCMeta)
class Tool(plugin.Plugin):
    """
    Base class used by tp-dcc-tools framework to implement DCC tools that have access to tp-dcc-tools functionality.
    """

    UI_DATA = {                             # Dictionary containing tool DCC UI related data
        'label': '',
        'icon': '',
        'tooltip': ''
    }

    def __init__(self, factory: plugin.PluginFactory, tools_manager: ToolsManager):
        super(Tool, self).__init__(factory=factory)

        self._tools = list()
        self._tools_manager = tools_manager

    @property
    @abc.abstractmethod
    def id(self):
        pass

    @property
    @abc.abstractmethod
    def creator(self):
        pass

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        pass

    def teardown(self):
        pass

    def set_stylesheet(self, style):
        pass

    def run(self):
        pass

    def _execute(self, *args, **kwargs):

        try:
            tool = self.execute(*args, **kwargs)
            if tool is not None:
                self._tools.append(tool)
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            raise
        finally:
            tb = None
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)

    def _run_teardown(self):
        """
        Internal function that tries to tear down the tool in a safe way.
        """

        try:
            self.teardown()
        except RuntimeError:
            logger.error(f'Failed to teardown tool: {self.id}', exc_info=True)
