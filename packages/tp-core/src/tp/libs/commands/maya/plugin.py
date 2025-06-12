from __future__ import annotations

import os
import sys
import typing
import traceback
from typing import Any

from maya import cmds
from loguru import logger
from maya.api import OpenMaya as OpenMaya

from tp.libs.commands.result import CommandReturnStatus

if typing.TYPE_CHECKING:
    from tp.libs.commands.maya.command import MayaCommand

if not hasattr(OpenMaya, "_TP_DCC_COMMAND"):
    OpenMaya._TP_DCC_COMMAND = None


def maya_useNewAPI():
    """The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """

    pass


def install():
    """Loads this module as a plug-in.

    Call this prior to using the module.
    """

    cmds.loadPlugin(__file__.replace(".pyc", ".py"), quiet=True)


def uninstall():
    """Undo `install()`

    This unregisters the associated plug-in.
    """

    # Plug-in may exist in undo queue and therefore cannot be unloaded until flushed.
    cmds.flushUndo()

    cmds.unloadPlugin(os.path.basename(__file__.replace(".pyc", ".py")))


def reinstall():
    """Automatically reload both Maya plug-in and Python module.

    Notes:
        Call this when changes have been made to this module.
    """

    uninstall()
    sys.modules.pop(__name__)
    module = __import__(__name__, globals(), locals(), ["*"], -1)
    module.install()
    return module


class UndoCommand(OpenMaya.MPxCommand):
    """Custom Maya command that allows to undo/redo commands using OpenMaya."""

    COMMAND_NAME = "tpUndoCommand"

    def __init__(self):
        super().__init__()

        self._command: MayaCommand | None = None
        self._command_name = ""

    @staticmethod
    def creator() -> UndoCommand:
        """Function that returns a new instance of the command."""

        return UndoCommand()

    @staticmethod
    def syntax_creator():
        """Function that returns the syntax of the command."""

        syntax = OpenMaya.MSyntax()
        syntax.addFlag("-id", "-commandId", OpenMaya.MSyntax.kString)
        return syntax

    # noinspection PyMethodOverriding
    def isUndoable(self) -> bool:
        """Returns whether the command is undoable or not."""

        return self._command is not None and self._command.is_undoable

    # noinspection PyMethodOverriding,PyUnresolvedReferences,PyProtectedMember
    def doIt(self, arguments: OpenMaya.MArgList):
        """Function that is called when the command is executed in Maya."""

        parser = OpenMaya.MArgParser(self.syntax(), arguments)
        command_id = parser.flagArgumentString("-id", 0)
        self._command_name = command_id
        if OpenMaya._TP_DCC_COMMAND is not None:
            self._command = OpenMaya._TP_DCC_COMMAND
            OpenMaya._TP_DCC_COMMAND = None
            self.redoIt()

    # noinspection PyMethodOverriding
    def redoIt(self):
        """Function that is called when the command is redone in Maya."""

        if self._command is None:
            return

        previous_state = cmds.undoInfo(query=True, stateWithoutFlush=True)
        try:
            if self._command.disable_queue:
                cmds.undoInfo(stateWithoutFlush=False)
            self._call_do_it(self._command)
        finally:
            cmds.undoInfo(stateWithoutFlush=previous_state)

    # noinspection PyMethodOverriding
    def undoIt(self):
        """Function that is called when the command is undone in Maya."""

        if self._command is None or not self._command.is_undoable:
            return

        previous_state = cmds.undoInfo(query=True, stateWithoutFlush=True)
        cmds.undoInfo(stateWithoutFlush=False)
        try:
            self._command.undo()
        except Exception as err:
            logger.exception(
                f"Error while undoing command: {self._command_name} | {err}",
                exc_info=True,
            )
        finally:
            cmds.undoInfo(stateWithoutFlush=previous_state)

    def _call_do_it(self, command: MayaCommand) -> Any:
        """Internal function that calls the `do_it` method of the given command.

        Args:
            command: Command to call the `do_it` method from.

        Returns:
            The result of the `do_it` method.
        """

        try:
            result = command.do(**command.arguments)
            command.return_result = result
            command.return_status = CommandReturnStatus.Success
        except Exception as err:
            logger.exception(
                f"Error while executing command: {self._command_name} | {err}",
                exc_info=True,
            )
            result = None
            command.return_result = result
            command.return_status = CommandReturnStatus.Error
            command._errors = traceback.format_exc()
        else:
            command.return_result = result

        return result


# noinspection PyPep8Naming
def initializePlugin(obj: OpenMaya.MObject):
    """Initialize the plug-in when Maya loads it.

    Args:
        obj: plug-in object to register the command with.
    """

    plugin = OpenMaya.MFnPlugin(obj, "Tomi Poveda", "1.0")
    try:
        plugin.registerCommand(
            UndoCommand.COMMAND_NAME, UndoCommand.creator, UndoCommand.syntax_creator
        )
    except Exception as err:
        logger.exception(f"Error while registering command: {err}", exc_info=True)
        raise


# noinspection PyPep8Naming,SpellCheckingInspection
def uninitializePlugin(obj: OpenMaya.MObject):
    """Uninitialize the plug-in when Maya unloads it.

    Args:
        obj: plug-in object to deregister the command with.
    """

    plugin = OpenMaya.MFnPlugin(obj)
    try:
        plugin.deregisterCommand(UndoCommand.COMMAND_NAME)
    except Exception as err:
        logger.exception(f"Error while deregistering command: {err}", exc_info=True)
        raise
