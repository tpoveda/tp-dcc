import sys

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

if not hasattr(OpenMaya, '_TPDCC_COMMAND'):
    OpenMaya._TPDCC_COMMAND = None
    OpenMaya._COMMAND_RUNNER = None


def maya_useNewAPI():
    pass


class UndoCommand(OpenMaya.MPxCommand):
    """
    Custom undo command plugin that allow us to support the undo of custom tpDcc
    commands that uses both API and MEL code
    """

    commandName = 'tpDccUndo'
    Id = '-id'
    IdLong = '-commandId'

    def __init__(self):
        super(UndoCommand, self).__init__()

        self._command = None
        self._command_name = ''
        self._command_runner = None

    @classmethod
    def command_creator(cls):
        return UndoCommand()

    @staticmethod
    def syntax_creator():
        syntax = OpenMaya.MSyntax()
        syntax.addFlag(UndoCommand.Id, UndoCommand.IdLong, OpenMaya.MSyntax.kString)
        return syntax

    def doIt(self, args_list):
        parser = OpenMaya.MArgParser(self.syntax(), args_list)
        command_id = parser.flagArgumentString(UndoCommand.Id, 0)
        self._command_name = command_id
        self._command_runner = OpenMaya._COMMAND_RUNNER
        if OpenMaya._TPDCC_COMMAND is not None:
            self._command = OpenMaya._TPDCC_COMMAND
            OpenMaya._TPDCC_COMMAND = None
            self.redoIt()

    def redoIt(self):
        if self._command is None:
            return

        prev_state = cmds.undoInfo(query=True, stateWithoutFlush=True)
        try:
            if self._command.disable_queue:
                cmds.undoInfo(stateWithoutFlush=False)
            self._command_runner._run(self._command)
        finally:
            cmds.undoInfo(stateWithoutFlush=prev_state)

    def undoIt(self):
        if self._command is None or not self._command.is_undoable:
            return

        prev_state = cmds.undoInfo(query=True, stateWithoutFlush=True)
        cmds.undoInfo(stateWithoutFlush=False)
        try:
            self._command.undo()
        finally:
            cmds.undoInfo(stateWithoutFlush=prev_state)

    def isUndoable(self):
        return self._command.is_undoable


def initializePlugin(mobj):
    mplugin = OpenMaya.MFnPlugin(mobj, 'Tomas Poveda', '1.0', 'Any')
    try:
        mplugin.registerCommand(UndoCommand.commandName, UndoCommand.command_creator, UndoCommand.syntax_creator)
    except Exception:
        sys.stderr.write('Failed to register command: {}'.format(UndoCommand.commandName))


def uninitializePlugin(mobj):
    mplugin = OpenMaya.MFnPlugin(mobj)
    try:
        mplugin.deregisterCommand(UndoCommand.commandName)
    except Exception:
        sys.stderr.write('Failed to unregister command: {}'.format(UndoCommand.commandName))
