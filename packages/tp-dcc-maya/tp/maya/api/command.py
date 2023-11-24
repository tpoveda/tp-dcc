#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya command implementation
"""

import sys
import traceback
from typing import Any

from overrides import override
import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from tp.core import log, command, exceptions
from tp.maya.cmds import helpers
from tp.maya.api import output

logger = log.tpLogger


class MayaCommand(command.DccCommand):

    @override
    def do(self, **kwargs: dict) -> Any:
        raise NotImplementedError


class MayaCommandRunner(command.BaseCommandRunner):
    """
    Maya Command runner implementation that allows to inject DCC commands into the Maya undo stack.
    """

    def __init__(self):
        super().__init__(interface=MayaCommand)

        OpenMaya._COMMAND_RUNNER = None
        helpers.load_plugin('tpundo.py')

    @override
    def run(self, command_id: str, **kwargs: dict) -> Any:

        logger.debug(f'Executing command: "{command_id}"')

        command_to_run = self.find_command(command_id)
        if command_to_run is None:
            raise ValueError(f'No command found with given id "{command_id}"')

        if OpenMaya._COMMAND_RUNNER is None:
            OpenMaya._COMMAND_RUNNER = self

        command_to_run = command_to_run()
        if not command_to_run.is_enabled:
            return
        try:
            command_to_run.parse_arguments(kwargs)
            if command_to_run.requires_warning():
                output.MayaOutput.display_warning(command_to_run.warning_message())
                return
        except exceptions.CommandCancel:
            return
        except Exception:
            raise

        exc_tb, exc_type, exc_value = None, None, None
        command_to_run.stats = command.CommandStats(command_to_run)
        try:
            if command_to_run.is_undoable:
                cmds.undoInfo(openChunk=True, chunkName=command_to_run.id)
                self._undo_stack.append(command_to_run)
            OpenMaya._TPDCC_COMMAND = command_to_run
            cmds.tpDccUndo(id=command_to_run.id)
            return command_to_run._return_result
        except exceptions.CommandCancel:
            command_to_run.stats.finish(None)
        except Exception:
            exc_type, exc_value, exc_trace = sys.exc_info()
            if command_to_run.is_undoable and command_to_run.use_undo_chunk:
                self._undo_stack.pop()
            raise
        finally:
            tb = None
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            if command_to_run.is_undoable and command_to_run.use_undo_chunk:
                cmds.undoInfo(closeChunk=True)
            command_to_run.stats.finish(tb)
            logger.debug(f'Finished executing command: "{command_id}"')

    @override
    def undo_last(self) -> bool:
        if not self._undo_stack:
            return False

        command_to_undo = self._undo_stack[-1]
        if command_to_undo is None or not command_to_undo.is_undoable:
            return False

        exc_tb, exc_type, exc_value = None, None, None
        try:
            command_to_undo.stats = command.CommandStats(command_to_undo)
            cmds.undo()
        except exceptions.CommandCancel:
            command_to_undo.stats.finish(None)
            return False
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            raise
        finally:
            tb = None
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            elif command_to_undo.is_undoable:
                self._undo_stack.remove(command_to_undo)
            self._redo_stack.append(command_to_undo)
            command_to_undo.stats.finish(tb)

        return True

    def redo_last(self) -> Any:

        if not self._redo_stack:
            return

        result = None
        command_to_redo = self._redo_stack[-1]
        if command_to_redo is None:
            return result

        exc_tb, exc_type, exc_value = None, None, None
        try:
            command_to_redo.stats = command.CommandStats(command_to_redo)
            cmds.redo()
        except exceptions.CommandCancel:
            command_to_redo.stats.finish(None)
            return
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            raise
        finally:
            tb = None
            command_to_redo = self._redo_stack.pop()
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            elif command_to_redo.is_undoable:
                self._undo_stack.append(command_to_redo)
            command_to_redo.stats.finish(tb)

        return result

    @override
    def flush(self):
        super().flush()
        cmds.flushUndo()

    @override
    def _run(self, command_to_run: command.DccCommand) -> Any:
        if OpenMaya.MGlobal.isRedoing():
            if self._redo_stack:
                self._redo_stack.pop()
            result = super()._run(command_to_run)
            self._undo_stack.append(command_to_run)
            return result
        try:
            return super(MayaCommandRunner, self)._run(command_to_run)
        except Exception:
            logger.error(f'Unhandled exception ocurred in command "{command_to_run.id}"')
            raise
