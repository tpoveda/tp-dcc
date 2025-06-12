from __future__ import annotations

import os
import sys
import types
import logging
from typing import Callable

from maya import cmds
from maya.api import OpenMaya as OpenMaya

logger = logging.getLogger(__name__)

__version__ = "1.0.0"


# noinspection PyPep8Naming
def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """

    pass


# Support for multiple co-existing versions of apiundo.
# NOTE: This is important for vendoring, as otherwise a vendored apiundo
# could register e.g. cmds.apiUndo() first, causing a newer version
# to inadvertently use this older command (or worse yet, throwing an
# error when trying to register it again).
command = f'_apiUndo_{__version__.replace(".", "_")}'

# This module is both a Python module and Maya plug-in.
# Data is shared amongst the two through this "module"
name = "_apiundoShared"
if name not in sys.modules:
    sys.modules[name] = types.ModuleType(name)

shared = sys.modules[name]
shared.undo = None
shared.redo = None


def commit(undo: Callable, redo: Callable = lambda: None):
    """
    Commit `undo` and `redo` to history

    :param undo: Call this function on next undo.
    :param redo: Like `undo`, for redo
    """

    if not hasattr(cmds, command):
        install()

    # Precautionary measure.
    # If this doesn't pass, odds are we've got a race condition.
    # NOTE: This assumes calls to `commit` can only be done from a single thread,
    # which should already be the case given that Maya's API is not threadsafe.
    assert shared.redo is None
    assert shared.undo is None

    # Temporarily store the functions at module-level, they are later picked up by
    # the command once called.
    shared.undo = undo
    shared.redo = redo

    # Let Maya know that something is undoable.
    getattr(cmds, command)()


def install():
    """
    Loads this module as a plug-in.

    Call this prior to using the module.
    """

    cmds.loadPlugin(__file__.replace(".pyc", ".py"), quiet=True)


def uninstall():
    """
    Undo `install()`

    This unregisters the associated plug-in.
    """

    # Plug-in may exist in undo queue and
    # therefore cannot be unloaded until flushed.
    cmds.flushUndo()

    cmds.unloadPlugin(os.path.basename(__file__.replace(".pyc", ".py")))


def reinstall():
    """
    Automatically reload both Maya plug-in and Python module

    .note:: FOR DEVELOPERS: Call this when changes have been made to this module.
    """

    uninstall()
    sys.modules.pop(__name__)
    module = __import__(__name__, globals(), locals(), ["*"], -1)
    module.install()
    return module


# noinspection PyMethodOverriding,PyPep8Naming
class _apiUndo(OpenMaya.MPxCommand):
    # noinspection PyAttributeOutsideInit
    def doIt(self, args):
        self.undo = shared.undo
        self.redo = shared.redo

        # Facilitate the above precautionary measure
        shared.undo = None
        shared.redo = None

    def undoIt(self):
        self.undo()

    def redoIt(self):
        self.redo()

    def isUndoable(self):
        return True


# noinspection PyPep8Naming
def initializePlugin(obj: OpenMaya.MObject):
    """
    Initialize the plug-in when Maya loads it.

    :param obj: plug-in object to register the command with.
    """

    plugin = OpenMaya.MFnPlugin(obj, 'Tomi Poveda', '1.0')
    try:
        plugin.registerCommand(command, _apiUndo)
    except Exception as err:
        logger.exception(f"Failed to register command: {err}", exc_info=True)
        raise


# noinspection PyPep8Naming,SpellCheckingInspection
def uninitializePlugin(obj: OpenMaya.MObject):
    """
    Uninitialize the plug-in when Maya unloads it.

    :param obj: plug-in object to deregister the command with.
    """

    plugin = OpenMaya.MFnPlugin(obj)
    try:
        plugin.deregisterCommand(command)
    except Exception as err:
        logger.exception(f"Failed to deregister command: {err}", exc_info=True)
        raise
